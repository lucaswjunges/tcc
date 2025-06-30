#!/bin/bash
# Script para iniciar o MCP Server compartilhado

echo "🚀 Iniciando MCP LLM Server Compartilhado..."
echo "──────────────────────────────────────────────────"

# Verificar se está na pasta correta
if [ ! -f "shared_mcp_server.py" ]; then
    echo "❌ Erro: Execute este script na pasta mcp-llm-server"
    exit 1
fi

# Ativar ambiente virtual
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "❌ Erro: Ambiente virtual não encontrado"
    echo "Execute: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verificar dependências
echo "📦 Verificando dependências..."
python3 -c "import flask, flask_cors, openai, google.generativeai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependências faltando. Instalando..."
    pip install flask flask-cors openai google-generativeai python-dotenv
fi

# Verificar API keys
echo "🔑 Verificando API keys..."
if [ -z "$OPENAI_API_KEY" ] && [ -z "$(grep OPENAI_API_KEY .env 2>/dev/null)" ]; then
    echo "⚠️  OPENAI_API_KEY não encontrada"
fi

if [ -z "$OPENROUTER_API_KEY" ] && [ -z "$(grep OPENROUTER_API_KEY .env 2>/dev/null)" ]; then
    echo "⚠️  OPENROUTER_API_KEY não encontrada"
fi

if [ -z "$GEMINI_API_KEY" ] && [ -z "$(grep GEMINI_API_KEY .env 2>/dev/null)" ]; then
    echo "⚠️  GEMINI_API_KEY não encontrada"
fi

# Descobrir IP local
LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7; exit}' 2>/dev/null || echo "localhost")

echo ""
echo "📍 Informações do Servidor:"
echo "   🌐 IP Local: $LOCAL_IP"
echo "   🚪 Porta: 8080"
echo "   🔑 Token: evolux-shared-token-2024-secure"
echo "   📋 URL: http://$LOCAL_IP:8080"
echo ""
echo "📤 Compartilhe com seu amigo:"
echo "   IP: $LOCAL_IP"
echo "   Token: evolux-shared-token-2024-secure"
echo ""
echo "🚀 Iniciando servidor..."
echo "   (Pressione Ctrl+C para parar)"
echo "──────────────────────────────────────────────────"

# Iniciar servidor
python3 shared_mcp_server.py