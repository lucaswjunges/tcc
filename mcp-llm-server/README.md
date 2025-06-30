# MCP LLM Server

Um servidor MCP (Model Context Protocol) em Python que oferece acesso unificado a múltiplos provedores de LLM incluindo Claude AI, OpenAI, OpenRouter e Gemini.

## 🚀 Características

- **Múltiplos Provedores**: Suporte para Claude AI, OpenAI, OpenRouter e Gemini
- **Autenticação OAuth 2.0**: Sistema de autenticação seguro
- **Arquitetura Modular**: Fácil de estender e manter
- **Configuração Flexível**: Suporte a múltiplos formatos de configuração
- **Logging Estruturado**: Sistema de logs detalhado para debugging
- **Tratamento de Erros**: Recuperação automática e retry logic

## 📦 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd mcp-llm-server

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves de API
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API Keys
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
GEMINI_API_KEY=...

# OAuth Configuration
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8080/callback

# Server Configuration
MCP_SERVER_NAME=llm-server
MCP_SERVER_VERSION=1.0.0
LOG_LEVEL=INFO
```

## 🏗️ Arquitetura

```
src/mcp_llm_server/
├── __init__.py           # Inicialização do pacote
├── server.py             # Servidor MCP principal
├── auth/                 # Sistema de autenticação
│   ├── __init__.py
│   ├── oauth.py         # OAuth 2.0 implementation
│   └── token_manager.py # Gerenciamento de tokens
├── clients/             # Clientes para LLMs
│   ├── __init__.py
│   ├── base.py         # Cliente base abstrato
│   ├── claude.py       # Cliente Claude AI
│   ├── openai.py       # Cliente OpenAI
│   ├── openrouter.py   # Cliente OpenRouter
│   └── gemini.py       # Cliente Gemini
├── config/             # Gerenciamento de configuração
│   ├── __init__.py
│   └── settings.py     # Configurações do sistema
├── tools/              # Ferramentas MCP
│   ├── __init__.py
│   ├── chat.py         # Ferramenta de chat
│   ├── completion.py   # Ferramenta de completion
│   └── model_info.py   # Informações dos modelos
└── utils/              # Utilitários
    ├── __init__.py
    ├── logging.py      # Sistema de logging
    └── exceptions.py   # Exceções customizadas
```

## 🔌 Uso com Claude Code

```bash
# Adicionar o servidor MCP
claude mcp add llm-server "python -m mcp_llm_server"

# Ou com configuração específica
claude mcp add -e OPENAI_API_KEY=sk-... llm-server "python -m mcp_llm_server"
```

## 🛠️ Desenvolvimento

```bash
# Executar testes
pytest tests/

# Executar com debugging
python -m mcp_llm_server --debug

# Executar linting
flake8 src/
black src/
```

## 📚 Exemplos

Veja a pasta `examples/` para exemplos de uso detalhados.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.