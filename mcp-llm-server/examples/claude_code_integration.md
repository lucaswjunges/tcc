# Integração com Claude Code

Este guia mostra como integrar o MCP LLM Server com Claude Code para ter acesso a múltiplos provedores de LLM diretamente do seu terminal.

## Pré-requisitos

1. **Claude Code** instalado e configurado
2. **API Keys** dos provedores que deseja usar
3. **Python 3.9+** instalado

## Configuração Rápida

### 1. Instalar o Servidor

```bash
# Clone o repositório
git clone <repo-url>
cd mcp-llm-server

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys
```

### 2. Configurar API Keys

Edite o arquivo `.env` com suas chaves:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Claude (Anthropic)
CLAUDE_API_KEY=sk-ant-your-claude-key-here

# OpenRouter
OPENROUTER_API_KEY=sk-or-your-openrouter-key-here

# Gemini (Google)
GEMINI_API_KEY=your-gemini-key-here

# OAuth (opcional, para segurança)
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-secret-key-for-jwt
```

### 3. Adicionar ao Claude Code

```bash
# Adiciona o servidor MCP ao Claude Code
claude mcp add llm-server "python -m mcp_llm_server"

# Ou com configuração de environment
claude mcp add -e OPENAI_API_KEY=sk-... llm-server "python -m mcp_llm_server"

# Verificar se foi adicionado
claude mcp list
```

## Usando o Servidor

### Ferramentas Disponíveis

O servidor oferece 3 ferramentas principais:

#### 1. **chat** - Conversas de Chat
```json
{
  "name": "chat",
  "arguments": {
    "messages": [
      {"role": "user", "content": "Explique machine learning"}
    ],
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "max_tokens": 500,
    "temperature": 0.7
  }
}
```

#### 2. **completion** - Text Completion
```json
{
  "name": "completion", 
  "arguments": {
    "prompt": "Complete esta frase: A inteligência artificial",
    "provider": "claude",
    "max_tokens": 100
  }
}
```

#### 3. **model_info** - Informações dos Modelos
```json
{
  "name": "model_info",
  "arguments": {
    "action": "list_all",
    "include_details": true
  }
}
```

### Exemplos Práticos

#### Chat Simples com Claude
```bash
# No Claude Code, você pode usar:
@llm-server chat with Claude about the benefits of functional programming
```

#### Comparar Respostas de Múltiplos Provedores
```bash
# Obter resposta do OpenAI
@llm-server chat "Explain quantum computing" with provider openai

# Comparar com Claude
@llm-server chat "Explain quantum computing" with provider claude

# E com Gemini
@llm-server chat "Explain quantum computing" with provider gemini
```

#### Listar Modelos Disponíveis
```bash
@llm-server list all available models with details
```

#### Code Completion
```bash
@llm-server complete this Python code: "def fibonacci(n):"
```

### Prompts Pré-definidos

O servidor inclui prompts prontos para uso comum:

#### Simple Chat
```bash
@llm-server simple_chat "What is the weather like?" provider=openai
```

#### Code Completion
```bash
@llm-server code_completion code="def sort_list(arr):" language=python provider=claude
```

#### Text Generation
```bash
@llm-server text_generation topic="artificial intelligence" style=academic length=medium
```

#### Summarization
```bash
@llm-server summarization text="Long text here..." length=brief
```

## Configurações Avançadas

### Streaming de Respostas

Para respostas em tempo real:

```json
{
  "name": "chat",
  "arguments": {
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true,
    "provider": "openai"
  }
}
```

### Configuração de Modelos Específicos

```json
{
  "name": "chat",
  "arguments": {
    "messages": [{"role": "user", "content": "Code review this function"}],
    "provider": "openai",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.1,
    "max_tokens": 1000
  }
}
```

### OAuth Security

Para ambientes de produção, configure OAuth:

```bash
# Configurar OAuth no .env
OAUTH_CLIENT_ID=your-app-id
OAUTH_CLIENT_SECRET=your-app-secret
SECRET_KEY=your-jwt-secret

# O servidor irá requerer autenticação OAuth
claude mcp add --oauth llm-server-secure "python -m mcp_llm_server"
```

## Troubleshooting

### Problemas Comuns

1. **"Provider not available"**
   ```bash
   # Verifique se a API key está configurada
   echo $OPENAI_API_KEY
   
   # Verifique os logs do servidor
   python -m mcp_llm_server --debug
   ```

2. **"Authentication failed"**
   ```bash
   # Verifique se a API key é válida
   # Para OpenAI: deve começar com "sk-"
   # Para Claude: deve começar com "sk-ant-"
   ```

3. **"Model not found"**
   ```bash
   # Liste modelos disponíveis
   @llm-server model_info action=list_provider provider=openai
   ```

### Debug Mode

```bash
# Executar em modo debug
python -m mcp_llm_server --debug --log-level DEBUG

# Ver logs detalhados
tail -f logs/mcp-server.log
```

### Configuração de Development

```bash
# Para desenvolvimento, use o arquivo de configuração local
cp .env.example .env.dev

# Execute com configuração de desenvolvimento
DEVELOPMENT_MODE=true python -m mcp_llm_server
```

## Recursos Avançados

### Cache de Respostas

O servidor inclui cache automático para otimizar performance:

```bash
# Configurar cache no .env
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

### Rate Limiting

Para controlar uso de API:

```bash
# Configurar rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Monitoring

O servidor oferece métricas detalhadas:

```bash
# Ver estatísticas
@llm-server get server status and statistics
```

## Próximos Passos

1. **Explore os prompts**: Use os prompts pré-definidos para tarefas comuns
2. **Configure OAuth**: Para segurança em produção
3. **Customize modelos**: Experimente diferentes modelos para diferentes tarefas
4. **Monitor uso**: Acompanhe custos e performance

Para mais informações, consulte a documentação completa no arquivo `README.md`.