# 🚀 Como Executar o Método Avançado - GUIA COMPLETO

## 🎯 **VOCÊ (Lucas) - Hospedeiro das APIs**

### **📍 Passo 1: Ir para pasta do MCP Server**
```bash
cd /home/lucas-junges/Documents/evolux-engine/mcp-llm-server
```

### **🚀 Passo 2: Iniciar o Servidor Compartilhado**
```bash
# Método 1: Script automático
./start_shared_server.sh

# Método 2: Manual
source venv/bin/activate
python3 shared_mcp_server.py
```

### **📋 Passo 3: Você verá algo assim:**
```
🚀 Iniciando Shared MCP LLM Server...
🔑 Token de acesso: evolux-shared-token-2024-secure
📡 Servidor disponível para conexões externas
──────────────────────────────────────────────────
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://192.168.0.58:8080
```

### **📤 Passo 4: Compartilhar informações**
Envie para seu amigo:
- **IP:** `192.168.0.58`
- **Porta:** `8080`
- **Token:** `evolux-shared-token-2024-secure`
- **Arquivos:** `claude_mcp_client.py` e `client_mcp.py`

---

## 👥 **SEU AMIGO - Cliente**

### **📥 Passo 1: Baixar arquivos**
```bash
# Opção 1: Se você subir no GitHub
git clone https://github.com/seu-usuario/mcp-llm-server.git
cd mcp-llm-server

# Opção 2: Baixar arquivos específicos
# - claude_mcp_client.py (para Claude Code)
# - client_mcp.py (para teste)
```

### **📦 Passo 2: Instalar dependências**
```bash
pip install mcp requests openai google-generativeai python-dotenv
```

### **🧪 Passo 3: Testar conexão**
```bash
python3 client_mcp.py
```

### **⚙️ Passo 4: Registrar no Claude Code**
```bash
claude mcp add lucas-apis 'python3 /caminho/completo/para/claude_mcp_client.py'
```

### **🎮 Passo 5: Usar no Claude Code**
```bash
@lucas-apis shared_llm_chat provider=openai message="Explique inteligência artificial"
@lucas-apis shared_llm_chat provider=gemini message="Como criar uma startup?"
@lucas-apis shared_list_models
```

---

## 🔧 **Comandos Práticos**

### **Para VOCÊ (Lucas):**

#### Iniciar servidor:
```bash
cd /home/lucas-junges/Documents/evolux-engine/mcp-llm-server
source venv/bin/activate
python3 shared_mcp_server.py
```

#### Verificar se está funcionando:
```bash
curl -H "Authorization: Bearer evolux-shared-token-2024-secure" http://localhost:8080/health
```

#### Parar servidor:
```bash
# Pressione Ctrl+C no terminal onde está rodando
```

### **Para seu AMIGO:**

#### Testar conexão:
```bash
python3 client_mcp.py
```

#### Verificar IP do Lucas:
```bash
ping 192.168.0.58
```

#### Usar no Claude Code:
```bash
@lucas-apis shared_llm_chat provider=openai message="Sua pergunta aqui"
```

---

## 📋 **Arquivos Necessários**

### **No seu PC (Lucas):**
- ✅ `shared_mcp_server.py` - Servidor principal
- ✅ `start_shared_server.sh` - Script de inicialização  
- ✅ `.env` - Com suas API keys
- ✅ `venv/` - Ambiente virtual

### **No PC do seu amigo:**
- ✅ `claude_mcp_client.py` - Cliente para Claude Code
- ✅ `client_mcp.py` - Cliente para teste
- ✅ Dependências instaladas

---

## 🎯 **Próximos Passos**

### **Agora:**
1. **Você:** Execute `./start_shared_server.sh`
2. **Amigo:** Baixe os arquivos e teste com `python3 client_mcp.py`
3. **Amigo:** Registre no Claude Code
4. **Ambos:** Testem o sistema

### **Depois:**
1. Fazer push no GitHub (sem .env)
2. Seu amigo clona o repositório
3. Colaborar nos projetos usando as APIs compartilhadas

---

## ✅ **Status Atual**

- ✅ **Servidor compartilhado** criado e funcional
- ✅ **Cliente para Claude Code** implementado
- ✅ **Cliente de teste** funcionando
- ✅ **API keys protegidas** (não vão para GitHub)
- ✅ **Token de segurança** configurado
- ✅ **IP local** descoberto (192.168.0.58)
- ✅ **Instruções completas** criadas

**🚀 Pronto para usar! Execute o servidor e compartilhe com seu amigo!**