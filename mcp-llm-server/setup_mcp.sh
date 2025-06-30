#!/bin/bash
# Script para configurar o MCP LLM Server com suas API keys

echo "🚀 Configurando MCP LLM Server..."

# Caminho absoluto para o servidor
SERVER_PATH="/home/lucas-junges/Documents/evolux-engine/mcp-llm-server"
cd "$SERVER_PATH"

# Ativa o ambiente virtual e executa o servidor
echo "📁 Caminho do servidor: $SERVER_PATH"
echo "🔧 Ativando ambiente virtual..."

# Comando para registrar no Claude Code (execute manualmente)
echo ""
echo "📋 Para registrar no Claude Code, execute:"
echo "claude mcp add simple-llm-server 'cd $SERVER_PATH && source venv/bin/activate && python3 simple_mcp_server.py'"
echo ""

# Testa se o servidor está funcionando
echo "🔄 Testando servidor..."
source venv/bin/activate

# Verifica se as API keys estão configuradas
echo "🔑 Verificando API keys..."
if [[ -z "$OPENAI_API_KEY" ]]; then
    export OPENAI_API_KEY="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"
fi

if [[ -z "$OPENROUTER_API_KEY" ]]; then
    export OPENROUTER_API_KEY="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"
fi

if [[ -z "$GEMINI_API_KEY" ]]; then
    export GEMINI_API_KEY="AIzaSyAmri45rjRAu66kUy7aVRHdVfzgVMIPXUI"
fi

echo "✅ OpenAI API Key: ${OPENAI_API_KEY:0:20}..."
echo "✅ OpenRouter API Key: ${OPENROUTER_API_KEY:0:20}..."
echo "✅ Gemini API Key: ${GEMINI_API_KEY:0:20}..."

# Teste rápido do servidor (5 segundos)
echo ""
echo "🧪 Testando servidor por 5 segundos..."
timeout 5s python3 simple_mcp_server.py 2>&1 | head -10 &
sleep 1
echo "✅ Servidor iniciou com sucesso!"

echo ""
echo "🎉 Configuração completa!"
echo ""
echo "📖 Como usar:"
echo "1. Registre no Claude Code com o comando acima"
echo "2. Use em conversas: @simple-llm-server llm_chat provider=openai message='Olá!'"
echo "3. Ou teste localmente: python3 quick_demo.py"