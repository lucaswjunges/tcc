#!/usr/bin/env python3
"""
Cliente MCP para conectar ao servidor compartilhado
Seu amigo usa este script para conectar às suas APIs
"""

import requests
import json
import sys

class SharedMCPClient:
    """Cliente para conectar ao MCP server compartilhado."""
    
    def __init__(self, server_url, access_token):
        self.server_url = server_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def health_check(self):
        """Verifica se o servidor está funcionando."""
        try:
            response = requests.get(f"{self.server_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, provider, message, model=None):
        """Envia mensagem para o LLM."""
        data = {
            "provider": provider,
            "message": message
        }
        if model:
            data["model"] = model
        
        try:
            response = requests.post(
                f"{self.server_url}/chat",
                headers=self.headers,
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_models(self):
        """Lista modelos disponíveis."""
        try:
            response = requests.get(
                f"{self.server_url}/models",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    """Função principal para teste."""
    # Configurações - seu amigo deve ajustar isso
    SERVER_URL = "http://192.168.0.58:8080"  # IP do Lucas
    ACCESS_TOKEN = "evolux-shared-token-2024-secure"  # Token fornecido pelo Lucas
    
    client = SharedMCPClient(SERVER_URL, ACCESS_TOKEN)
    
    print("🔄 Testando conexão com servidor compartilhado...")
    
    # Teste de saúde
    health = client.health_check()
    print(f"📊 Status do servidor: {health}")
    
    if "error" in health:
        print("❌ Erro de conexão. Verifique se o servidor está rodando.")
        return
    
    # Listar modelos
    models = client.list_models()
    print(f"📋 Modelos disponíveis: {json.dumps(models, indent=2)}")
    
    # Teste de chat
    test_cases = [
        {"provider": "openai", "message": "Diga olá em português"},
        {"provider": "gemini", "message": "Como você está?"},
        {"provider": "openrouter", "message": "Conte uma piada"}
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testando {test['provider']}...")
        result = client.chat(test['provider'], test['message'])
        
        if result.get('success'):
            print(f"✅ {test['provider']}: {result['response']}")
        else:
            print(f"❌ {test['provider']}: {result.get('error', 'Erro desconhecido')}")

if __name__ == "__main__":
    main()