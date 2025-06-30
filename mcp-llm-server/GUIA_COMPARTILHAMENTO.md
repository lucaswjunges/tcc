#!/usr/bin/env python3
"""
Cliente MCP compatível com Claude Code
Permite que seu amigo use suas APIs através do Claude Code
"""

import asyncio
import json
import sys
import os
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

class ClaudeMCPClient:
    """Cliente MCP para usar com Claude Code."""
    
    def __init__(self):
        self.server = Server("shared-llm-client")
        self.setup_tools()
        
        # Configurações - SEU AMIGO DEVE EDITAR ISSO
        self.server_url = "http://SEU_IP:8080"  # IP do seu servidor
        self.access_token = "shared-token-2024"  # Token que você forneceu
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def setup_tools(self):
        """Configura as ferramentas MCP."""
        
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="shared_llm_chat",
                    description="Chat with shared LLM providers (OpenAI, Gemini, OpenRouter)",
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
                ),
                Tool(
                    name="shared_list_models",
                    description="List available models for shared LLM providers",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "shared_llm_chat":
                return await self.handle_chat(arguments)
            elif name == "shared_list_models":
                return await self.handle_list_models()
            else:
                return [TextContent(type="text", text=f"Ferramenta desconhecida: {name}")]
    
    async def handle_chat(self, arguments: dict):
        """Processa chat usando o servidor compartilhado."""
        provider = arguments["provider"]
        message = arguments["message"]
        model = arguments.get("model")
        
        data = {
            "provider": provider,
            "message": message
        }
        if model:
            data["model"] = model
        
        try:
            response = requests.post(
                f"{self.server_url}/chat",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return [TextContent(
                        type="text",
                        text=f"**{provider.upper()}** ({result.get('model', 'default')}):\n\n{result['response']}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ Erro com {provider}: {result.get('error', 'Erro desconhecido')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Erro de conexão: {response.status_code}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Erro de conexão: {str(e)}"
            )]
    
    async def handle_list_models(self):
        """Lista modelos disponíveis."""
        try:
            response = requests.get(
                f"{self.server_url}/models",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                result = "**Modelos Disponíveis:**\n\n"
                for provider, model_list in models.items():
                    result += f"**{provider.upper()}:**\n"
                    for model in model_list:
                        result += f"- {model}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Erro ao listar modelos: {response.status_code}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Erro de conexão: {str(e)}"
            )]
    
    async def run(self):
        """Executa o servidor MCP."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Função principal."""
    client = ClaudeMCPClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())