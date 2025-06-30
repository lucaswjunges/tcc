#!/usr/bin/env python3
"""
Teste direto de configuração sem importar o servidor.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Carrega .env manualmente
from dotenv import load_dotenv
load_dotenv('.env')

def test_direct_config():
    """Testa criação direta de configuração."""
    print("🔄 Testando configuração direta...")
    
    try:
        from pydantic import BaseModel, Field, field_validator
        from pydantic_settings import BaseSettings, SettingsConfigDict
        
        # Caminho para o arquivo .env
        ENV_FILE = str(Path(__file__).parent / '.env')
        print(f"📁 Arquivo .env: {ENV_FILE}")
        print(f"📁 Existe: {Path(ENV_FILE).exists()}")
        
        class TestOpenAIConfig(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=ENV_FILE,
                env_file_encoding='utf-8',
                case_sensitive=False,
                extra='ignore'
            )
            
            api_key: str = Field(env="OPENAI_API_KEY")
            base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
        
        config = TestOpenAIConfig()
        print(f"✅ OpenAI API Key carregada: {config.api_key[:20]}...")
        print(f"✅ Base URL: {config.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_vars():
    """Testa se as variáveis estão no ambiente."""
    print("\n🔄 Testando variáveis de ambiente...")
    
    vars_to_check = [
        'OPENAI_API_KEY',
        'OPENROUTER_API_KEY', 
        'GEMINI_API_KEY',
        'SECRET_KEY'
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: não encontrada")
    
    return all(os.getenv(var) for var in vars_to_check)

def test_simple_server():
    """Testa criação de um servidor simples."""
    print("\n🔄 Testando servidor simples...")
    
    try:
        # Só importa o que é necessário
        import mcp_llm_server.utils.logging as logging_utils
        print("✅ Utils importado")
        
        import mcp_llm_server.clients.base as base_client
        print("✅ Base client importado")
        
        print("✅ Importações básicas funcionaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 MCP LLM Server - Teste de Configuração Direta\n")
    
    success = True
    success &= test_env_vars()
    success &= test_direct_config()
    success &= test_simple_server()
    
    if success:
        print("\n🎉 Configuração básica está funcionando!")
        print("📝 O problema pode estar na importação circular ou na instância global.")
        print("💡 Sugestão: Modificar para não instanciar settings automaticamente.")
    else:
        print("\n💥 Problemas na configuração básica.")
        sys.exit(1)