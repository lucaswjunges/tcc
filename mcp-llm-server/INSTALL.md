# Instalação do MCP LLM Server

Este guia detalha como instalar e configurar o MCP LLM Server para usar com Claude Code.

## ⚡ Instalação Rápida

```bash
# 1. Clone/baixe o projeto
cd mcp-llm-server

# 2. Verifique o setup
python3 setup_check.py

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edite .env com suas chaves

# 5. Teste a instalação
python3 test_import.py

# 6. Adicione ao Claude Code
claude mcp add llm-server "python3 -m mcp_llm_server"
```

## 📋 Pré-requisitos

### Sistema
- **Python 3.9+** (recomendado 3.11+)
- **pip** para instalação de pacotes
- **Claude Code** instalado e configurado

### API Keys (pelo menos uma)
- **OpenAI**: https://platform.openai.com/api-keys
- **Claude (Anthropic)**: https://console.anthropic.com/
- **OpenRouter**: https://openrouter.ai/keys
- **Gemini (Google)**: https://makersuite.google.com/app/apikey

## 🔧 Instalação Detalhada

### 1. Verificação do Sistema

```bash
# Verifique Python
python3 --version  # Deve ser 3.9+

# Verifique Claude Code
claude --version

# Execute verificação completa
python3 setup_check.py
```

### 2. Instalação de Dependências

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Ou instalar apenas o necessário
pip install mcp==0.9.0 pydantic pydantic-settings httpx aiohttp
pip install openai anthropic google-generativeai  # Clientes LLM
pip install structlog rich cryptography python-dotenv  # Utilitários
```

### 3. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas API keys
nano .env  # ou seu editor preferido
```

#### Exemplo de `.env`:
```bash
# Pelo menos uma API key é necessária
OPENAI_API_KEY=sk-your-openai-key-here
CLAUDE_API_KEY=sk-ant-your-claude-key-here
OPENROUTER_API_KEY=sk-or-your-openrouter-key-here
GEMINI_API_KEY=your-gemini-key-here

# Configurações opcionais
SECRET_KEY=your-secret-key-for-jwt-tokens
LOG_LEVEL=INFO
DEFAULT_LLM_PROVIDER=openai
```

### 4. Teste da Instalação

```bash
# Teste básico de importação
python3 test_import.py

# Teste manual do servidor (Ctrl+C para sair)
python3 -m mcp_llm_server --debug

# Verificação final
python3 setup_check.py
```

### 5. Integração com Claude Code

```bash
# Adicionar servidor MCP
claude mcp add llm-server "python3 -m mcp_llm_server"

# Verificar se foi adicionado
claude mcp list

# Testar conexão
claude mcp get llm-server
```

## 🛠️ Resolução de Problemas

### Erro: "No module named 'mcp'"
```bash
# Instale a versão correta do MCP
pip install mcp==0.9.0
```

### Erro: "Authentication failed"
```bash
# Verifique se as API keys estão corretas
echo $OPENAI_API_KEY  # Deve começar com "sk-"
echo $CLAUDE_API_KEY  # Deve começar com "sk-ant-"
```

### Erro: "Provider not configured"
```bash
# Verifique se pelo menos uma API key está no .env
cat .env | grep API_KEY

# Recarregue as variáveis
source .env  # se usando bash
```

### Erro: "Permission denied"
```bash
# Torne o script executável
chmod +x mcp-llm-server/src/mcp_llm_server/__main__.py

# Ou use caminho absoluto
claude mcp add llm-server "/usr/bin/python3 -m mcp_llm_server"
```

### Problemas de Dependências
```bash
# Limpe cache do pip
pip cache purge

# Reinstale dependências
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# Use ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔍 Verificação da Instalação

### Comandos de Teste

```bash
# 1. Teste de importação
python3 -c "from mcp_llm_server import MCPLLMServer; print('✅ OK')"

# 2. Teste de configuração
python3 -c "from mcp_llm_server.config import settings; print(f'Server: {settings.server.name}')"

# 3. Teste de cliente LLM
python3 -c "from mcp_llm_server.clients import LLMClientFactory; print('✅ Clients OK')"

# 4. Teste MCP
claude mcp list | grep llm-server
```

### Logs de Debug

```bash
# Ver logs em tempo real
tail -f logs/mcp-server.log

# Debug completo
LOG_LEVEL=DEBUG python3 -m mcp_llm_server

# Teste com Claude Code
claude mcp get llm-server --debug
```

## 🚀 Uso Básico

Após a instalação, você pode usar:

```bash
# No Claude Code
@llm-server chat "Hello world" provider=openai
@llm-server completion "Complete this: AI is" provider=claude
@llm-server model_info action=list_all

# Direto no terminal
python3 examples/basic_usage.py
```

## 📚 Próximos Passos

1. **Explore os exemplos**: Veja `examples/` para casos de uso
2. **Configure OAuth**: Para segurança em produção
3. **Customize prompts**: Crie seus próprios prompts
4. **Monitore uso**: Acompanhe custos e performance

Para mais detalhes, consulte:
- `README.md` - Documentação completa
- `examples/` - Exemplos de uso
- `docs/` - Documentação técnica