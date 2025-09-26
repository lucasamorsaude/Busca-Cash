import os
import re
import requests
import io
import pandas as pd
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename

from login_auth import get_auth_new

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

HEADERS = {
    'Content-Type': 'application/json',
}

CASHBACK_URL = 'https://amei.amorsaude.com.br/api/v1/cartao-todos/cashback'

def get_cashback(headers,cpf):
    
    params = {'matriculaoucpf': cpf}

    print(f"Consultando cashback para o CPF: {cpf}")

    try:
        response = requests.get(CASHBACK_URL, headers=headers, params=params)
        response.raise_for_status()
        print(f"Resposta da API (Status {response.status_code}): {response.text}")

        if response.text:
            return response.json()
        else:
            return {"info": "A API retornou uma resposta vazia.", "cpf_consultado": cpf}

    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao buscar cashback: {http_err}")
        print(f"Resposta do servidor: {http_err.response.text}")
        return {"erro": f"Erro HTTP {http_err.response.status_code}", "detalhes": http_err.response.text}
    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição ao buscar cashback: {e}")
        return {"erro": "Erro de conexão com a API."}
    except ValueError:
        print("Erro ao decodificar JSON da resposta da API.")
        return {"erro": "A resposta da API não é um JSON válido.", "resposta_recebida": response.text}

@app.route('/', methods=['GET', 'POST'])
def index():
    auth_token = get_auth_new()
    if not auth_token:
        return {"erro": "Autenticação inicial falhou. Verifique as credenciais e reinicie o servidor."}

    headers = HEADERS.copy()
    headers['Authorization'] = f"Bearer {auth_token}"

    cashback_data = None
    error_message = None
    cpf_digitado = ""
    tabela_resultado = None

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                try:
                    df = pd.read_excel(file)
                    if 'CPF' not in df.columns:
                        error_message = "A planilha deve conter a coluna 'CPF'."
                    else:
                        df['CPF'] = df['CPF'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)
                        resultados = []
                        for cpf in df['CPF']:
                            res = get_cashback(headers,cpf)
                            saldo = res.get('balanceAvailable') if 'balanceAvailable' in res else None
                            resultados.append({'CPF': cpf, 'Cashback': saldo})
                        tabela_resultado = pd.DataFrame(resultados)
                        # Converte para lista de dicts para o template
                        tabela_resultado = tabela_resultado.to_dict(orient='records')
                except Exception as e:
                    error_message = f"Erro ao processar a planilha: {e}"
            else:
                error_message = "Arquivo inválido. Por favor, envie um arquivo Excel (.xls ou .xlsx)."
        else:
            cpf_sujo = request.form.get('cpf', '')
            cpf_digitado = cpf_sujo
            if cpf_sujo:
                cpf_limpo = re.sub(r'\D', '', cpf_sujo)
                resultado = get_cashback(headers,cpf_limpo)
                if 'erro' in resultado:
                    error_message = f"Falha na consulta: {resultado.get('erro')} - {resultado.get('detalhes', '')}"
                else:
                    cashback_data = resultado
            else:
                error_message = "Por favor, digite um CPF."

    return render_template('index.html',
                           cashback_data=cashback_data,
                           error_message=error_message,
                           cpf_digitado=cpf_digitado,
                           tabela_resultado=tabela_resultado)



@app.route('/download-result', methods=['POST'])
def download_result():
    csv_data = request.form.get('csv_data')
    if not csv_data:
        return "Nenhum dado para download.", 400
    output = io.BytesIO()
    output.write(csv_data.encode('utf-8'))
    output.seek(0)
    return send_file(output, download_name="resultado_cashback.csv", as_attachment=True, mimetype='text/csv')

@app.route('/download-template')
def download_template():
    df = pd.DataFrame(columns=['CPF'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name="template_cpf.xlsx", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)