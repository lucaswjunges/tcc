#!/usr/bin/env python3
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
                        model = model or "anthropic/claude-3-haiku"
                        response = self.openrouter_client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": message}],
                            max_tokens=500
                        )
                        result = response.choices[0].message.content
                    
                    return [TextContent(
                        type="text",
                        text=f"**{provider.upper()}** ({model or 'default'}):\n\n{result}"
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
