#!/usr/bin/env python3
"""
MCP LLM Server Compartilhado - Para usar com amigos
Este servidor aceita conexões via HTTP/WebSocket para compartilhar APIs
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv('.env')

# Clientes LLM
import openai
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # Permite conexões de outros domínios

class SharedLLMService:
    """Serviço LLM compartilhado via HTTP."""
    
    def __init__(self):
        # Configuração das APIs
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.openrouter_client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('OPENROUTER_API_KEY'),
        )
        
        # Token de acesso simples (trocar por algo mais seguro em produção)
        self.access_token = os.getenv('SHARED_ACCESS_TOKEN', 'shared-token-2024')
    
    def verify_token(self, token):
        """Verifica se o token de acesso é válido."""
        return token == self.access_token
    
    async def chat(self, provider, message, model=None):
        """Processa chat com diferentes provedores."""
        try:
            if provider == "openai":
                model = model or "gpt-3.5-turbo"
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500
                )
                result = response.choices[0].message.content
                
            elif provider == "gemini":
                response = self.gemini_model.generate_content(message)
                result = response.text
                model = model or "gemini-1.5-flash"
                
            elif provider == "openrouter":
                model = model or "anthropic/claude-3-haiku"
                response = self.openrouter_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500
                )
                result = response.choices[0].message.content
                
            return {
                "success": True,
                "provider": provider,
                "model": model,
                "response": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

# Inicializar serviço
llm_service = SharedLLMService()

@app.route('/health', methods=['GET'])
def health_check():
    """Verificação de saúde do servidor."""
    return jsonify({
        "status": "healthy",
        "service": "Shared LLM MCP Server",
        "version": "1.0.0"
    })

@app.route('/chat', methods=['POST'])
async def chat_endpoint():
    """Endpoint para chat com LLMs."""
    data = request.json
    
    # Verificar token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not llm_service.verify_token(token):
        return jsonify({"error": "Token de acesso inválido"}), 401
    
    # Parâmetros obrigatórios
    provider = data.get('provider')
    message = data.get('message')
    
    if not provider or not message:
        return jsonify({"error": "Provider e message são obrigatórios"}), 400
    
    # Processar chat
    result = await llm_service.chat(
        provider=provider,
        message=message,
        model=data.get('model')
    )
    
    return jsonify(result)

@app.route('/models', methods=['GET'])
def list_models():
    """Lista modelos disponíveis por provedor."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not llm_service.verify_token(token):
        return jsonify({"error": "Token de acesso inválido"}), 401
    
    models = {
        "openai": [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ],
        "gemini": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ],
        "openrouter": [
            "anthropic/claude-3-haiku",
            "microsoft/wizardlm-2-8x22b",
            "anthropic/claude-3-sonnet"
        ]
    }
    
    return jsonify(models)

if __name__ == '__main__':
    print("🚀 Iniciando Shared MCP LLM Server...")
    print(f"🔑 Token de acesso: {llm_service.access_token}")
    print("📡 Servidor disponível para conexões externas")
    print("─" * 50)
    
    # Executar servidor
    app.run(
        host='0.0.0.0',  # Aceita conexões de qualquer IP
        port=8080,       # Porta diferente do Flask padrão
        debug=False,     # Desativar debug em produção
        threaded=True
    )