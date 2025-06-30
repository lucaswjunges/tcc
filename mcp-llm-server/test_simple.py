#!/usr/bin/env python3
"""
Teste simples de configuração com suas API keys.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Carrega .env manualmente
from dotenv import load_dotenv
load_dotenv('.env')

def test_env_loading():
    """Testa se as API keys estão sendo carregadas."""
    print("🔄 Testando carregamento de variáveis de ambiente...")
    
    api_keys = {
        'OPENAI_API_KEY': 'OpenAI',
        'OPENROUTER_API_KEY': 'OpenRouter', 
        'GEMINI_API_KEY': 'Gemini',
        'SECRET_KEY': 'Secret Key'
    }
    
    for env_var, name in api_keys.items():
        value = os.getenv(env_var)
        if value:
            print(f"✅ {name}: {value[:20]}...")
        else:
            print(f"❌ {name}: não encontrada")
    
    return all(os.getenv(key) for key in api_keys.keys())

def test_config_creation():
    """Testa criação de configurações diretamente."""
    print("\n🔄 Testando criação de configurações...")
    
    try:
        from mcp_llm_server.config.settings import OpenAIConfig, GeminiConfig, SecurityConfig
        
        # Testa SecurityConfig 
        security = SecurityConfig()
        print(f"✅ SecurityConfig: secret_key={security.secret_key[:10]}...")
        
        # Testa OpenAIConfig
        openai = OpenAIConfig()
        print(f"✅ OpenAIConfig: api_key={openai.api_key[:20]}...")
        
        # Testa GeminiConfig
        gemini = GeminiConfig()
        print(f"✅ GeminiConfig: api_key={gemini.api_key[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_manual_settings():
    """Testa Settings criando manualmente."""
    print("\n🔄 Testando Settings manual...")
    
    try:
        from mcp_llm_server.config.settings import Settings
        
        settings = Settings()
        print(f"✅ Settings criado com sucesso")
        print(f"✅ OpenAI configurado: {bool(settings.openai.api_key)}")
        print(f"✅ Gemini configurado: {bool(settings.gemini.api_key)}")
        
        # Valida configurações
        settings.validate_all()
        print("✅ Validação passou!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 MCP LLM Server - Teste Simples de Configuração\n")
    
    success = True
    success &= test_env_loading()
    success &= test_config_creation() 
    success &= test_manual_settings()
    
    if success:
        print("\n🎉 Todos os testes passaram! Configuração está funcionando.")
    else:
        print("\n💥 Alguns testes falharam.")
        sys.exit(1)