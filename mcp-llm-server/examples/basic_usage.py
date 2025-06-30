#!/usr/bin/env python3
"""
Exemplo básico de uso do MCP LLM Server.

Este exemplo demonstra como configurar e usar o servidor MCP
para interagir com diferentes provedores de LLM.
"""

import asyncio
import json
from pathlib import Path

# Adiciona o diretório src ao path para importar o módulo
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mcp_llm_server.server import MCPLLMServer
from mcp_llm_server.config import settings


async def test_chat_tool():
    """Testa a ferramenta de chat."""
    print("🚀 Testando ferramenta de chat...")
    
    # Simula argumentos da ferramenta
    chat_arguments = {
        "messages": [
            {
                "role": "user",
                "content": "Olá! Como você está?"
            }
        ],
        "provider": "openai",  # ou claude, openrouter, gemini
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    # Cria instância do servidor (normalmente seria feito pelo MCP)
    server = MCPLLMServer()
    
    # Obtém a ferramenta de chat
    chat_tool = server._tools["chat"]
    
    try:
        # Executa a ferramenta
        result = await chat_tool.execute(chat_arguments)
        print("✅ Resultado do chat:")
        print(json.dumps(json.loads(result), indent=2))
    except Exception as e:
        print(f"❌ Erro no chat: {e}")


async def test_completion_tool():
    """Testa a ferramenta de completion."""
    print("\n🚀 Testando ferramenta de completion...")
    
    # Simula argumentos da ferramenta
    completion_arguments = {
        "prompt": "Complete esta frase: A inteligência artificial é",
        "provider": "claude",
        "max_tokens": 50,
        "temperature": 0.5
    }
    
    server = MCPLLMServer()
    completion_tool = server._tools["completion"]
    
    try:
        result = await completion_tool.execute(completion_arguments)
        print("✅ Resultado do completion:")
        print(json.dumps(json.loads(result), indent=2))
    except Exception as e:
        print(f"❌ Erro no completion: {e}")


async def test_model_info_tool():
    """Testa a ferramenta de informações de modelos."""
    print("\n🚀 Testando ferramenta de informações de modelos...")
    
    # Lista todos os provedores
    providers_arguments = {
        "action": "get_providers"
    }
    
    server = MCPLLMServer()
    model_info_tool = server._tools["model_info"]
    
    try:
        result = await model_info_tool.execute(providers_arguments)
        print("✅ Provedores disponíveis:")
        print(json.dumps(json.loads(result), indent=2))
    except Exception as e:
        print(f"❌ Erro ao listar provedores: {e}")


async def test_prompts():
    """Testa os prompts pré-definidos."""
    print("\n🚀 Testando prompts pré-definidos...")
    
    server = MCPLLMServer()
    chat_tool = server._tools["chat"]
    
    # Testa prompt de chat simples
    try:
        prompt = await chat_tool.get_prompt("simple_chat", {
            "message": "Explique o que é machine learning em termos simples",
            "provider": "openai"
        })
        
        print("✅ Prompt gerado:")
        print(json.dumps(prompt, indent=2))
        
        # Executa o prompt
        if prompt:
            result = await chat_tool.execute(prompt)
            print("\n✅ Resultado do prompt:")
            print(json.dumps(json.loads(result), indent=2))
            
    except Exception as e:
        print(f"❌ Erro com prompts: {e}")


async def main():
    """Função principal para executar todos os testes."""
    print("🎯 MCP LLM Server - Exemplos de Uso\n")
    print(f"Servidor: {settings.server.name} v{settings.server.version}")
    print(f"Provedores configurados: {', '.join(['openai', 'claude', 'openrouter', 'gemini'])}\n")
    
    # Nota: Em um ambiente real, você precisaria ter as API keys configuradas
    print("⚠️  NOTA: Para executar estes exemplos, configure as API keys no arquivo .env")
    print("   Exemplo: OPENAI_API_KEY=sk-..., CLAUDE_API_KEY=sk-ant-..., etc.\n")
    
    try:
        # Executa todos os testes
        await test_chat_tool()
        await test_completion_tool() 
        await test_model_info_tool()
        await test_prompts()
        
        print("\n🎉 Todos os testes concluídos!")
        
    except Exception as e:
        print(f"\n💥 Erro geral: {e}")
        print("\nVerifique se as API keys estão configuradas corretamente no arquivo .env")


if __name__ == "__main__":
    # Executa os exemplos
    asyncio.run(main())