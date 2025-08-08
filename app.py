import os
import re # Importa o módulo de expressões regulares
import requests
from flask import Flask, request, render_template

from login_auth import get_auth_new

# ... (o resto da configuração inicial não muda) ...
app = Flask(__name__)
# ... (autenticação e definições de URL não mudam) ...
# --- 1. CONFIGURAÇÃO DA APLICAÇÃO E AUTENTICAÇÃO ---

# Inicializa o Flask. Ele automaticamente reconhece a pasta 'templates'.
app = Flask(__name__)

# Realiza a autenticação uma vez quando o app inicia
print("Iniciando autenticação com a API AmorSaúde...")
try:
    auth_token = get_auth_new()
    print("Autenticação bem-sucedida.")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao obter o token de autenticação. O app não poderá funcionar. Erro: {e}")
    auth_token = None

# Headers para as requisições na API
HEADERS = {
    'Content-Type': 'application/json',
}

# URL da nova API de Cashback
CASHBACK_URL = 'https://amei.amorsaude.com.br/api/v1/cartao-todos/cashback'


# --- 2. FUNÇÃO PARA CONSULTAR O CASHBACK ---
# (A função get_cashback não precisa de alterações)
def get_cashback(cpf):

    auth_token = get_auth_new()

    if not auth_token:
        return {"erro": "Autenticação inicial falhou. Verifique as credenciais e reinicie o servidor."}

    request_headers = HEADERS.copy()
    request_headers['Authorization'] = f"Bearer {auth_token}"
    params = {'matriculaoucpf': cpf}
    
    print(f"Consultando cashback para o CPF: {cpf}")
    
    try:
        response = requests.get(CASHBACK_URL, headers=request_headers, params=params)
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


# --- 3. ROTA DA APLICAÇÃO WEB (INTERFACE) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    cashback_data = None
    error_message = None
    cpf_digitado = ""

    if request.method == 'POST':
        cpf_sujo = request.form.get('cpf', '') # Pega o valor do formulário
        cpf_digitado = cpf_sujo
        
        if cpf_sujo:
            # LÓGICA DE LIMPEZA: Remove tudo que não for dígito
            cpf_limpo = re.sub(r'\D', '', cpf_sujo)
            
            resultado = get_cashback(cpf_limpo) # Usa o CPF limpo na consulta
            if 'erro' in resultado:
                error_message = f"Falha na consulta: {resultado.get('erro')} - {resultado.get('detalhes', '')}"
            else:
                cashback_data = resultado
        else:
            error_message = "Por favor, digite um CPF."

    return render_template('index.html', 
                           cashback_data=cashback_data, 
                           error_message=error_message, 
                           cpf_digitado=cpf_digitado)

# --- 4. EXECUÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
