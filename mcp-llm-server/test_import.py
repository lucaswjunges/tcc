#!/usr/bin/env python3
"""
Teste básico de importação do MCP LLM Server.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    try:
        print("🔄 Testando importações...")
        
        # Testa configurações
        from mcp_llm_server.config import settings
        print("✅ Config importado com sucesso")
        
        # Testa utilitários
        from mcp_llm_server.utils import get_logger, LoggerMixin
        print("✅ Utils importado com sucesso")
        
        # Testa clientes (sem inicializar)
        from mcp_llm_server.clients import BaseLLMClient, LLMClientFactory
        print("✅ Clients importado com sucesso")
        
        # Testa autenticação
        from mcp_llm_server.auth import OAuthManager, TokenManager
        print("✅ Auth importado com sucesso")
        
        # Testa ferramentas
        from mcp_llm_server.tools import ChatTool, CompletionTool, ModelInfoTool
        print("✅ Tools importado com sucesso")
        
        # Testa servidor principal
        from mcp_llm_server.server import MCPLLMServer
        print("✅ Server importado com sucesso")
        
        print("\n🎉 Todas as importações funcionaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na importação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_config():
    """Testa configuração básica."""
    try:
        print("\n🔄 Testando configuração básica...")
        
        from mcp_llm_server.config import settings
        
        print(f"✅ Servidor: {settings.server.name} v{settings.server.version}")
        print(f"✅ Log level: {settings.logging.level}")
        print(f"✅ Debug mode: {settings.server.debug}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na configuração: {e}")
        return False

def test_logger():
    """Testa sistema de logging."""
    try:
        print("\n🔄 Testando sistema de logging...")
        
        from mcp_llm_server.utils import get_logger, init_logging_from_env
        
        # Inicializa logging
        init_logging_from_env()
        
        # Cria logger
        logger = get_logger("test")
        logger.info("✅ Logger funcionando corretamente")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no logging: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MCP LLM Server - Teste de Importação\n")
    
    # Define variáveis mínimas necessárias
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-12345"
    
    success = True
    success &= test_imports()
    success &= test_basic_config()
    success &= test_logger()
    
    if success:
        print("\n🎯 Todos os testes passaram! O servidor está pronto para uso.")
        print("\n📝 Próximos passos:")
        print("   1. Configure as API keys no arquivo .env")
        print("   2. Execute: python -m mcp_llm_server")
        print("   3. Ou integre com Claude Code: claude mcp add llm-server 'python -m mcp_llm_server'")
    else:
        print("\n💥 Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)