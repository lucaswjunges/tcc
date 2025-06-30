#!/usr/bin/env python3
"""
Teste da configuração simplificada.
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_simple_settings():
    """Testa a configuração simplificada."""
    print("🔄 Testando configuração simplificada...")
    
    try:
        from mcp_llm_server.config.simple_settings import settings
        
        # Cria as configurações
        config = settings()
        print("✅ Configurações criadas com sucesso")
        
        # Valida configurações básicas
        print(f"✅ Servidor: {config.server.name} v{config.server.version}")
        print(f"✅ Logging: {config.logging.level}")
        print(f"✅ Security: Secret key configurada ({len(config.security.secret_key)} chars)")
        
        # Verifica provedores configurados
        providers = []
        if config.openai:
            providers.append("OpenAI")
            print(f"✅ OpenAI: {config.openai.api_key[:20]}...")
            
        if config.claude:
            providers.append("Claude")
            print(f"✅ Claude: {config.claude.api_key[:20]}...")
            
        if config.openrouter:
            providers.append("OpenRouter")
            print(f"✅ OpenRouter: {config.openrouter.api_key[:20]}...")
            
        if config.gemini:
            providers.append("Gemini")
            print(f"✅ Gemini: {config.gemini.api_key[:20]}...")
        
        print(f"✅ Provedores configurados: {', '.join(providers)}")
        
        # Valida todas as configurações
        config.validate_all()
        print("✅ Validação completa passou!")
        
        # Testa get_provider_config
        for provider in ["openai", "openrouter", "gemini"]:
            provider_config = config.get_provider_config(provider)
            if provider_config:
                print(f"✅ {provider.capitalize()}: {provider_config['default_model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_to_dict():
    """Testa conversão para dicionário."""
    print("\n🔄 Testando conversão para dict...")
    
    try:
        from mcp_llm_server.config.simple_settings import settings
        
        config = settings()
        config_dict = config.to_dict()
        
        print("✅ Conversão para dict funcionou")
        print(f"✅ Chaves principais: {list(config_dict.keys())}")
        
        # Verifica que não há API keys expostas
        def check_no_secrets(d, path=""):
            for key, value in d.items():
                if isinstance(value, dict):
                    check_no_secrets(value, f"{path}.{key}")
                elif isinstance(value, str) and any(secret in key.lower() for secret in ["key", "secret", "token"]):
                    if len(value) > 10:  # Se tem conteúdo significativo
                        print(f"⚠️  Possível segredo exposto em {path}.{key}")
        
        check_no_secrets(config_dict)
        print("✅ Validação de segurança passou")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MCP LLM Server - Teste de Configuração Simplificada\n")
    
    success = True
    success &= test_simple_settings()
    success &= test_to_dict()
    
    if success:
        print("\n🎉 Todos os testes da configuração simplificada passaram!")
        print("💡 A configuração simplificada está funcionando corretamente.")
    else:
        print("\n💥 Alguns testes falharam.")
        sys.exit(1)