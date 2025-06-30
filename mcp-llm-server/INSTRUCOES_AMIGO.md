# 🤝 Instruções para usar as APIs do Lucas

## 🎯 O que você vai ter acesso:
- **OpenAI** (GPT-4, GPT-3.5-turbo, etc.)
- **Google Gemini** (Gemini 1.5 Pro/Flash)
- **OpenRouter** (Claude, LLaMA, etc.)

## 📋 Setup Rápido

### 1. **Baixar arquivos necessários**
```bash
# Baixe estes arquivos do GitHub:
# - claude_mcp_client.py
# - client_mcp.py
# - requirements.txt (instalar: pip install -r requirements.txt)
```

### 2. **Instalar dependências**
```bash
pip install mcp requests openai google-generativeai python-dotenv
```

### 3. **Testar conexão**
```bash
python3 client_mcp.py
```

**Saída esperada:**
```
🔄 Testando conexão com servidor compartilhado...
📊 Status do servidor: {'status': 'healthy', 'service': 'Shared LLM MCP Server'}
✅ openai: Olá! Como posso ajudar você hoje?
✅ gemini: Como um modelo de linguagem...
✅ openrouter: Aqui vai uma piada...
```

### 4. **Registrar no Claude Code**
```bash
claude mcp add lucas-llm 'python3 /caminho/completo/para/claude_mcp_client.py'
```

### 5. **Usar no Claude Code**
```bash
# Chat com diferentes providers
@lucas-llm shared_llm_chat provider=openai message="Explique machine learning"
@lucas-llm shared_llm_chat provider=gemini message="Como criar uma API REST?"
@lucas-llm shared_llm_chat provider=openrouter message="Análise de código Python"

# Listar modelos disponíveis
@lucas-llm shared_list_models

# Especificar modelo específico
@lucas-llm shared_llm_chat provider=openai model=gpt-4 message="Análise complexa"
```

## 🔧 Configurações já definidas:
- **IP do Lucas:** `192.168.0.58`
- **Porta:** `8080`
- **Token:** `evolux-shared-token-2024-secure`

## 📞 Resolução de Problemas

### ❌ "Erro de conexão"
1. Verificar se o Lucas está com o servidor rodando
2. Verificar se estão na mesma rede WiFi
3. Testar conexão: `ping 192.168.0.58`

### ❌ "Token inválido"
1. Verificar se o token está correto no arquivo
2. Falar com o Lucas para confirmar o token

### ❌ "Timeout"
1. Aguardar um pouco (APIs podem demorar)
2. Verificar conexão de internet
3. Tentar com provider diferente

## 🎉 Vantagens para você:
- ✅ **Acesso a múltiplas APIs** sem custo
- ✅ **Integração com Claude Code** normal
- ✅ **Sem configuração complexa** 
- ✅ **Suporte do Lucas** para problemas
- ✅ **Acesso a modelos premium** (GPT-4, Claude, etc.)

## 🤝 Acordo de Uso:
- Usar com responsabilidade
- Não abusar das APIs
- Avisar se houver problemas
- Contribuir com o projeto quando possível

---

**🚀 Qualquer dúvida, chama o Lucas!**