#!/usr/bin/env python3
"""
Verificação de setup do MCP LLM Server.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Verifica versão do Python."""
    print("🔄 Verificando versão do Python...")
    
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ é necessário. Versão atual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print("\n🔄 Verificando dependências principais...")
    
    required_packages = [
        ("pydantic", "2.0"),
        ("pydantic_settings", "2.0"),
        ("httpx", "0.24"),
        ("aiohttp", "3.8"),
        ("structlog", "23.0"),
        ("rich", "13.0"),
        ("cryptography", "40.0"),
    ]
    
    missing = []
    
    for package, min_version in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (não instalado)")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Para instalar dependências faltantes:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_optional_dependencies():
    """Verifica dependências opcionais para LLMs."""
    print("\n🔄 Verificando clientes LLM...")
    
    llm_packages = [
        ("openai", "OpenAI GPT-4"),
        ("anthropic", "Claude"),
        ("google.generativeai", "Gemini"),
    ]
    
    available = []
    
    for package, name in llm_packages:
        try:
            __import__(package)
            print(f"✅ {name} ({package})")
            available.append(name)
        except ImportError:
            print(f"⚠️  {name} ({package}) - não instalado")
    
    if not available:
        print("\n📦 Para instalar clientes LLM:")
        print("pip install openai anthropic google-generativeai")
        return False
    
    print(f"\n🎯 Clientes LLM disponíveis: {', '.join(available)}")
    return True

def check_configuration():
    """Verifica arquivos de configuração."""
    print("\n🔄 Verificando configuração...")
    
    project_dir = Path(__file__).parent
    
    # Verifica .env.example
    env_example = project_dir / ".env.example"
    if env_example.exists():
        print("✅ .env.example encontrado")
    else:
        print("❌ .env.example não encontrado")
        return False
    
    # Verifica se .env existe
    env_file = project_dir / ".env"
    if env_file.exists():
        print("✅ .env encontrado")
    else:
        print("⚠️  .env não encontrado - copie de .env.example")
    
    # Verifica estrutura do projeto
    src_dir = project_dir / "src" / "mcp_llm_server"
    if src_dir.exists():
        print("✅ Estrutura do projeto OK")
    else:
        print("❌ Estrutura do projeto incorreta")
        return False
    
    return True

def check_environment_variables():
    """Verifica variáveis de ambiente básicas."""
    print("\n🔄 Verificando variáveis de ambiente...")
    
    # Carrega .env se existir
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✅ Carregando .env...")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            print("⚠️  python-dotenv não instalado - instale com: pip install python-dotenv")
    
    # Verifica se pelo menos uma API key está configurada
    api_keys = [
        ("OPENAI_API_KEY", "OpenAI"),
        ("CLAUDE_API_KEY", "Claude"),
        ("OPENROUTER_API_KEY", "OpenRouter"), 
        ("GEMINI_API_KEY", "Gemini"),
    ]
    
    configured = []
    for env_var, name in api_keys:
        if os.getenv(env_var):
            print(f"✅ {name} API key configurada")
            configured.append(name)
        else:
            print(f"⚠️  {name} API key não configurada ({env_var})")
    
    if not configured:
        print("\n⚠️  Nenhuma API key configurada. Configure pelo menos uma no arquivo .env")
        return False
    
    print(f"\n🎯 Provedores configurados: {', '.join(configured)}")
    return True

def main():
    """Função principal."""
    print("🚀 MCP LLM Server - Verificação de Setup\n")
    
    checks = [
        ("Versão Python", check_python_version),
        ("Dependências Core", check_dependencies),
        ("Clientes LLM", check_optional_dependencies),
        ("Configuração", check_configuration),
        ("Variáveis de Ambiente", check_environment_variables),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro em {name}: {e}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "="*50)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✅ OK" if result else "❌ FALHOU"
        print(f"{name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Status: {passed}/{len(results)} verificações passaram")
    
    if passed == len(results):
        print("\n🎉 Setup completo! O servidor está pronto para uso.")
        print("\n📝 Próximos passos:")
        print("   1. pip install -r requirements.txt")
        print("   2. python -m mcp_llm_server")
        print("   3. claude mcp add llm-server 'python -m mcp_llm_server'")
    elif passed >= len(results) - 1:
        print("\n⚠️  Setup quase completo. Verifique os itens marcados como FALHOU.")
    else:
        print("\n💥 Setup incompleto. Corrija os problemas antes de continuar.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())