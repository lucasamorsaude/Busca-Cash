import requests
import json
import os

# 1. Definições da Requisição
LOGIN_URL = 'https://amei.amorsaude.com.br/api/v1/security/login'
REFRESH_URL = 'https://amei.amorsaude.com.br/api/v1/security/refresh-token?clinicId=932'

# Tenta carregar as credenciais do arquivo config.json
try:
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
        LOGIN_PAYLOAD = {
            'email': config.get('email'),
            'password': config.get('password'), 
            'keepConnected': True
        }
except FileNotFoundError:
    print("ERRO CRÍTICO: O arquivo 'config.json' não foi encontrado.")
    print("Por favor, crie o arquivo com seu 'email' e 'password'.")
    exit() # Interrompe a execução se o arquivo de configuração não existir
except json.JSONDecodeError:
    print("ERRO CRÍTICO: O arquivo 'config.json' contém um erro de formatação (não é um JSON válido).")
    exit()


def get_auth_new():
    # 2. Início do Teste
    print("="*60)
    print("INICIANDO AUTENTICAÇÃO EM 2 PASSOS")
    print("="*60)

    # --- PASSO 1: Login Inicial ---
    try:
        # Verifica se as credenciais foram carregadas corretamente
        if not LOGIN_PAYLOAD.get('email') or not LOGIN_PAYLOAD.get('password'):
            print("\n❌ FALHA NO PASSO 1: Email ou senha não encontrados no arquivo config.json.")
            exit()

        login_response = requests.post(LOGIN_URL, json=LOGIN_PAYLOAD)
        login_response.raise_for_status()
        preliminary_token = login_response.json().get('access_token')

        if not preliminary_token:
            print("\n❌ FALHA NO PASSO 1: Token preliminar não foi encontrado.")
            exit()

        print("\n✅ SUCESSO NO PASSO 1!")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ FALHA NO PASSO 1: Erro na requisição de login. Detalhes: {e}")
        exit()

    # --- PASSO 2: Refresh com o método POST ---
    preliminary_headers = {'Authorization': f"Bearer {preliminary_token}"}

    try:
        refresh_response = requests.post(REFRESH_URL, headers=preliminary_headers)
        refresh_response.raise_for_status()

        refresh_data = refresh_response.json()
        final_token = refresh_data.get('access_token')

        if not final_token:
            print("\n❌ FALHA NO PASSO 2: Token final não encontrado na resposta.")
            exit()

        print("\n✅ SUCESSO NO PASSO 2! Autenticação completa.")
        return final_token
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FALHA NO PASSO 2: Erro na requisição de refresh.")
        print(f"Detalhes: {e}")
        if 'refresh_response' in locals():
            print(f"Resposta do Servidor: {refresh_response.text}")

