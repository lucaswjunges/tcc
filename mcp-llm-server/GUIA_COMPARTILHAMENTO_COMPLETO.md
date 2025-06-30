# 🔗 Guia Completo: Compartilhar APIs via MCP Server

## 🎯 Objetivo
Permitir que seu amigo use suas API keys através de um servidor MCP compartilhado, sem expor as chaves no GitHub.

## 🏗️ Arquitetura

```
[Você] → MCP Server → Suas APIs (OpenAI, Gemini, OpenRouter)
   ↑
[Seu Amigo] → Cliente MCP → Conecta ao seu servidor
```

## 📋 Passo a Passo

### 🔧 **VOCÊ (Hospedeiro das APIs):**

#### 1. **Preparar o Servidor Compartilhado**
```bash
cd /home/lucas-junges/Documents/evolux-engine/mcp-llm-server
```

#### 2. **Configurar Token de Acesso**
```bash
# Adicionar token ao .env
echo "SHARED_ACCESS_TOKEN=seu-token-super-secreto-123" >> .env
```

#### 3. **Descobrir seu IP Local**
```bash
# Ver seu IP na rede local
ip route get 1.1.1.1 | awk '{print $7; exit}'

# OU
hostname -I | awk '{print $1}'

# Exemplo de resultado: 192.168.1.100
```

#### 4. **Executar o Servidor Compartilhado**
```bash
source venv/bin/activate
python3 shared_mcp_server.py
```

Você verá algo como:
```
🚀 Iniciando Shared MCP LLM Server...
🔑 Token de acesso: seu-token-super-secreto-123
📡 Servidor disponível para conexões externas
──────────────────────────────────────────────────
 * Running on all addresses (0.0.0.0)
 * Running on http://192.168.1.100:8080
```

#### 5. **Compartilhar Informações com seu Amigo**
Envie para ele:
- **IP:** `192.168.1.100` (ou o que aparecer)
- **Porta:** `8080`
- **Token:** `seu-token-super-secreto-123`

---

### 👥 **SEU AMIGO (Cliente):**

#### 1. **Baixar os Arquivos**
```bash
# Se você subiu no GitHub (sem .env)
git clone https://github.com/seu-usuario/mcp-llm-server.git
cd mcp-llm-server

# OU baixar apenas os arquivos necessários:
# - claude_mcp_client.py
# - client_mcp.py
```

#### 2. **Instalar Dependências**
```bash
pip install requests mcp
```

#### 3. **Configurar Cliente**
Editar `claude_mcp_client.py`:
```python
# Linha 17-18, substituir:
self.server_url = "http://192.168.1.100:8080"  # IP que você forneceu
self.access_token = "seu-token-super-secreto-123"  # Token que você forneceu
```

#### 4. **Testar Conexão**
```bash
python3 client_mcp.py
```

#### 5. **Registrar no Claude Code**
```bash
claude mcp add shared-llm 'python3 /caminho/para/claude_mcp_client.py'
```

#### 6. **Usar no Claude Code**
```bash
@shared-llm shared_llm_chat provider=openai message="Olá, como você está?"
@shared-llm shared_llm_chat provider=gemini message="Explique inteligência artificial"
@shared-llm shared_list_models
```

---

## 🛡️ **Opção 2: Usando ngrok (Internet)**

Se vocês não estão na mesma rede, use ngrok para expor o servidor:

### **VOCÊ:**
```bash
# Instalar ngrok
sudo snap install ngrok

# Expor servidor
ngrok http 8080
```

Isso dará uma URL pública como: `https://abc123.ngrok.io`

### **SEU AMIGO:**
```python
# Usar a URL do ngrok
self.server_url = "https://abc123.ngrok.io"
```

---

## 🔐 **Opção 3: Servidor na Nuvem**

### **Deploy no Heroku (VOCÊ):**

1. **Criar app Heroku:**
```bash
heroku create mcp-llm-shared
```

2. **Configurar variáveis:**
```bash
heroku config:set OPENAI_API_KEY=sua-chave
heroku config:set OPENROUTER_API_KEY=sua-chave  
heroku config:set GEMINI_API_KEY=sua-chave
heroku config:set SHARED_ACCESS_TOKEN=token-super-secreto
```

3. **Deploy:**
```bash
git push heroku main
```

4. **Compartilhar URL:**
```
https://mcp-llm-shared.herokuapp.com
```

---

## 🧪 **Testando o Sistema**

### **Teste Local (SEU AMIGO):**
```bash
python3 client_mcp.py
```

Saída esperada:
```
🔄 Testando conexão com servidor compartilhado...
📊 Status do servidor: {'status': 'healthy', 'service': 'Shared LLM MCP Server'}
📋 Modelos disponíveis: {...}

🧪 Testando openai...
✅ openai: Olá! Como posso ajudar você hoje?

🧪 Testando gemini...
✅ gemini: Como um modelo de linguagem...

🧪 Testando openrouter...
✅ openrouter: Aqui vai uma piada...
```

### **Teste no Claude Code:**
```bash
@shared-llm shared_llm_chat provider=openai message="Conte sobre machine learning"
```

---

## 🔒 **Segurança**

### **Medidas Implementadas:**
- ✅ **Token de Acesso:** Apenas quem tem o token pode usar
- ✅ **Rate Limiting:** Evita abuso (pode ser adicionado)
- ✅ **CORS:** Controla origens permitidas
- ✅ **Timeout:** Evita requests longos

### **Melhorias Opcionais:**
```python
# Adicionar ao servidor para mais segurança:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

---

## 📊 **Vantagens desta Solução**

### ✅ **Para Você:**
- API keys nunca saem do seu ambiente
- Controle total sobre o uso
- Pode revogar acesso a qualquer momento
- Monitora uso das APIs

### ✅ **Para seu Amigo:**
- Não precisa ter próprias API keys
- Usa através do Claude Code normalmente
- Interface familiar
- Sem configuração complexa

### ✅ **Para o Projeto:**
- GitHub limpo (sem API keys)
- Código compartilhável
- Colaboração segura
- Facilmente escalável

---

## 📞 **Troubleshooting**

### **Problema: Conexão recusada**
```bash
# Verificar se servidor está rodando
curl http://seu-ip:8080/health

# Verificar firewall
sudo ufw allow 8080
```

### **Problema: Token inválido**
```bash
# Verificar se token está correto nos dois lados
echo $SHARED_ACCESS_TOKEN
```

### **Problema: Timeout**
```bash
# Verificar se redes estão conectadas
ping seu-ip
```

---

## 🎉 **Resultado Final**

Com esta configuração:
- ✅ **API keys protegidas** (nunca vão para GitHub)
- ✅ **Compartilhamento seguro** com token de acesso
- ✅ **Uso normal no Claude Code** para seu amigo
- ✅ **Controle total** das suas APIs
- ✅ **Colaboração facilitada** no projeto

**🚀 Agora vocês podem colaborar sem expor API keys!**