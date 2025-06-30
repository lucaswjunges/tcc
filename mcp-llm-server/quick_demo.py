#!/usr/bin/env python3
"""
Demo rápido do MCP LLM Server funcionando com suas API keys.
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env
load_dotenv('.env')

# Configuração manual simples
class SimpleConfig:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.secret_key = os.getenv('SECRET_KEY')

async def test_openai():
    """Testa integração com OpenAI."""
    print("🔄 Testando OpenAI...")
    
    try:
        import openai
        
        config = SimpleConfig()
        if not config.openai_api_key:
            print("❌ API key da OpenAI não encontrada")
            return False
        
        client = openai.OpenAI(api_key=config.openai_api_key)
        
        # Teste simples
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Diga 'Olá' em português"}],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI respondeu: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Erro OpenAI: {e}")
        return False

async def test_gemini():
    """Testa integração com Gemini."""
    print("\n🔄 Testando Gemini...")
    
    try:
        import google.generativeai as genai
        
        config = SimpleConfig()
        if not config.gemini_api_key:
            print("❌ API key do Gemini não encontrada")
            return False
        
        genai.configure(api_key=config.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content("Diga 'Olá' em português")
        print(f"✅ Gemini respondeu: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Erro Gemini: {e}")
        return False

async def test_openrouter():
    """Testa integração com OpenRouter."""
    print("\n🔄 Testando OpenRouter...")
    
    try:
        import openai
        
        config = SimpleConfig()
        if not config.openrouter_api_key:
            print("❌ API key do OpenRouter não encontrada")
            return False
        
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_api_key,
        )
        
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[{"role": "user", "content": "Diga 'Olá' em português"}],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenRouter respondeu: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Erro OpenRouter: {e}")
        return False

def create_simple_mcp_server():
    """Cria um servidor MCP simples para integração com Claude Code."""
    print("\n🔄 Criando exemplo de servidor MCP...")
    
    server_script = '''#!/usr/bin/env python3
"""
Servidor MCP simples funcional com suas API keys.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv('.env')

# Importações MCP simplificadas (assumindo que as dependências estão instaladas)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP não instalado. Use: pip install mcp")
    sys.exit(1)

# Clientes LLM
import openai
import google.generativeai as genai

class SimpleLLMServer:
    def __init__(self):
        self.server = Server("simple-llm-server")
        self.setup_tools()
        
        # Configuração das APIs
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.openrouter_client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('OPENROUTER_API_KEY'),
        )
    
    def setup_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="llm_chat",
                    description="Chat with different LLM providers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "enum": ["openai", "gemini", "openrouter"],
                                "description": "LLM provider to use"
                            },
                            "message": {
                                "type": "string",
                                "description": "Message to send"
                            },
                            "model": {
                                "type": "string",
                                "description": "Model to use (optional)"
                            }
                        },
                        "required": ["provider", "message"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "llm_chat":
                provider = arguments["provider"]
                message = arguments["message"]
                model = arguments.get("model")
                
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
                        
                    elif provider == "openrouter":
                        model = model or "meta-llama/llama-3.2-3b-instruct:free"
                        response = self.openrouter_client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": message}],
                            max_tokens=500
                        )
                        result = response.choices[0].message.content
                    
                    return [TextContent(
                        type="text",
                        text=f"**{provider.upper()}** ({model or 'default'}):\\n\\n{result}"
                    )]
                    
                except Exception as e:
                    return [TextContent(
                        type="text", 
                        text=f"Erro com {provider}: {str(e)}"
                    )]
            
            return [TextContent(type="text", text="Ferramenta não encontrada")]
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    server = SimpleLLMServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open('simple_mcp_server.py', 'w') as f:
        f.write(server_script)
    
    print("✅ Servidor MCP simples criado: simple_mcp_server.py")
    print("\n📝 Para usar com Claude Code:")
    print("   claude mcp add simple-llm 'python3 simple_mcp_server.py'")
    print("\n🚀 Exemplo de uso:")
    print("   @simple-llm llm_chat provider=openai message='Olá, como está?'")
    print("   @simple-llm llm_chat provider=gemini message='Explique machine learning'")
    print("   @simple-llm llm_chat provider=openrouter message='Conte uma piada'")

async def main():
    """Função principal."""
    print("🚀 MCP LLM Server - Demo Rápido com suas API Keys\\n")
    
    config = SimpleConfig()
    print(f"🔑 OpenAI: {'✅ Configurada' if config.openai_api_key else '❌ Não configurada'}")
    print(f"🔑 OpenRouter: {'✅ Configurada' if config.openrouter_api_key else '❌ Não configurada'}")
    print(f"🔑 Gemini: {'✅ Configurada' if config.gemini_api_key else '❌ Não configurada'}")
    print()
    
    # Testa conexões
    success = 0
    if config.openai_api_key:
        if await test_openai():
            success += 1
    
    if config.gemini_api_key:
        if await test_gemini():
            success += 1
    
    if config.openrouter_api_key:
        if await test_openrouter():
            success += 1
    
    print(f"\\n📊 Resultado: {success}/3 provedores funcionando")
    
    if success > 0:
        create_simple_mcp_server()
        print("\\n🎉 Demo funcionando! Suas API keys estão corretas.")
        print("\\n💡 Dica: Use o simple_mcp_server.py como ponto de partida")
        print("     enquanto corrigimos o servidor completo.")
    else:
        print("\\n💥 Nenhum provedor funcionou. Verifique suas API keys.")

if __name__ == "__main__":
    asyncio.run(main())