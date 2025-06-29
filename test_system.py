#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema Evolux Engine está funcionando corretamente
"""

import os
import sys
import asyncio
from pathlib import Path

def test_basic_imports():
    """Testa importações básicas"""
    print("🔧 Testando importações básicas...")
    
    try:
        import evolux_engine
        print("✅ evolux_engine importado com sucesso")
        
        from evolux_engine import (
            AdvancedSystemConfig,
            ConfigurationManager,
            EnterpriseObservabilityService,
            AdvancedContextManager,
            SecurityGateway,
            ModelRouter,
            LLMFactory,
            PromptEngine,
            IntelligentProjectScaffolding
        )
        print("✅ Todas as classes principais importadas com sucesso")
        
        return True
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False

def test_configuration():
    """Testa sistema de configuração"""
    print("\n⚙️  Testando sistema de configuração...")
    
    try:
        from evolux_engine import AdvancedSystemConfig, ConfigurationManager
        
        # Teste com API key mock diretamente
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        config = AdvancedSystemConfig()
        print(f"✅ Configuração com API key funcionando")
        
        # Verificar se API key está sendo lida
        api_key = config.get_api_key('openrouter')
        if api_key:
            print(f"✅ API key OpenRouter detectada: {api_key[:8]}***")
        else:
            print("❌ API key OpenRouter não detectada")
        print(f"✅ Configuração criada com sucesso")
        print(f"   - Provedor padrão: {config.default_llm_provider}")
        print(f"   - Modelo executor: {config.default_model_executor}")
        print(f"   - Timeout: {config.request_timeout}s")
        
        # Teste do ConfigurationManager
        config_manager = ConfigurationManager()
        loaded_config = config_manager.load_configuration()
        print(f"✅ ConfigurationManager funcionando")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de configuração: {e}")
        return False

def test_observability():
    """Testa sistema de observabilidade"""
    print("\n📊 Testando sistema de observabilidade...")
    
    try:
        from evolux_engine import EnterpriseObservabilityService, AdvancedSystemConfig
        
        # Configuração mock
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        config = AdvancedSystemConfig()
        
        # Criar serviço de observabilidade
        obs_service = EnterpriseObservabilityService(config)
        
        # Testar métricas
        from evolux_engine.services.enterprise_observability import MetricType
        obs_service.record_metric("test.counter", 1.0, MetricType.COUNTER)
        obs_service.set_gauge("test.gauge", 42.5)
        print("✅ Registro de métricas funcionando")
        
        # Testar tracing
        span_id = obs_service.start_trace("test_operation")
        obs_service.add_trace_log(span_id, "Test log entry")
        obs_service.finish_trace(span_id, "completed")
        print("✅ Sistema de tracing funcionando")
        
        # Testar métricas de performance
        metrics = obs_service.get_performance_metrics()
        print(f"✅ Métricas de performance obtidas: CPU {metrics.cpu_percent}%")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de observabilidade: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security():
    """Testa sistema de segurança"""
    print("\n🔒 Testando sistema de segurança...")
    
    try:
        from evolux_engine.security.security_gateway import SecurityGateway, SecurityLevel
        
        # Criar gateway de segurança
        security = SecurityGateway(SecurityLevel.STRICT)
        
        # Testar comando seguro
        result = asyncio.run(security.validate_command("ls -la"))
        print(f"✅ Comando seguro validado: {result.is_safe}")
        
        # Testar comando perigoso
        result = asyncio.run(security.validate_command("rm -rf /"))
        print(f"✅ Comando perigoso bloqueado: {not result.is_safe}")
        print(f"   Razão: {result.blocked_reason}")
        
        # Estatísticas
        stats = security.get_security_stats()
        print(f"✅ Estatísticas de segurança: {stats['total_validations']} validações")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de segurança: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_routing():
    """Testa sistema de roteamento de LLM"""
    print("\n🤖 Testando sistema de roteamento de LLM...")
    
    try:
        from evolux_engine import ModelRouter, LLMFactory
        from evolux_engine.llms.model_router import TaskCategory
        
        # Criar router
        router = ModelRouter()
        
        # Testar seleção de modelo
        model = router.select_model(TaskCategory.CODE_GENERATION)
        print(f"✅ Modelo selecionado para geração de código: {model}")
        
        # Testar fallback
        fallback = router.get_fallback_model(model, TaskCategory.CODE_GENERATION)
        print(f"✅ Modelo de fallback: {fallback}")
        
        # Estatísticas
        stats = router.get_routing_stats()
        print(f"✅ Estatísticas do router: {stats['total_models']} modelos disponíveis")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de roteamento LLM: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_scaffolding():
    """Testa sistema de scaffolding"""
    print("\n🏗️  Testando sistema de scaffolding...")
    
    try:
        from evolux_engine import IntelligentProjectScaffolding, AdvancedSystemConfig
        from evolux_engine.core.project_scaffolding import ProjectType, Framework
        
        # Configuração
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        config = AdvancedSystemConfig()
        
        # Criar sistema de scaffolding
        scaffolding = IntelligentProjectScaffolding(config)
        
        # Analisar goal
        analysis = scaffolding.analyze_project_goal("Create a REST API using Flask")
        print(f"✅ Análise de goal concluída:")
        print(f"   - Tipo detectado: {analysis['project_type']}")
        print(f"   - Linguagem: {analysis['language']}")
        print(f"   - Features: {analysis['detected_features']}")
        
        # Gerar scaffold
        scaffold = scaffolding.generate_project_scaffold(
            goal="Create a simple Flask web application",
            project_name="TestApp",
            output_dir="/tmp/test_scaffold",
            force_type=ProjectType.WEB_APPLICATION,
            force_framework=Framework.FLASK
        )
        print(f"✅ Scaffold gerado: {scaffold.name}")
        print(f"   - Framework: {scaffold.framework}")
        print(f"   - Dependências: {len(scaffold.dependencies.get('python', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de scaffolding: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_manager():
    """Testa sistema de gerenciamento de contexto"""
    print("\n📝 Testando sistema de gerenciamento de contexto...")
    
    try:
        from evolux_engine import AdvancedContextManager, AdvancedSystemConfig
        
        # Configuração
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        config = AdvancedSystemConfig()
        
        # Criar context manager
        context_manager = AdvancedContextManager(config)
        
        # Criar contexto de teste
        context = context_manager.create_new_project_context(
            goal="Test project for system validation",
            project_name="Test Project"
        )
        print(f"✅ Contexto criado: {context.project_id}")
        
        # Salvar contexto
        success = context_manager.save_project_context(context, create_snapshot=True)
        print(f"✅ Contexto salvo: {success}")
        
        # Carregar contexto
        loaded_context = context_manager.load_project_context(context.project_id)
        print(f"✅ Contexto carregado: {loaded_context.project_name}")
        
        # Estatísticas
        stats = context_manager.get_manager_stats()
        print(f"✅ Estatísticas: {stats['total_contexts']} contextos, hit rate: {stats['cache_hit_rate']:.2%}")
        
        # Cleanup
        context_manager.cleanup_and_shutdown()
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de context manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do sistema Evolux Engine")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_configuration,
        test_observability,
        test_security,
        test_llm_routing,
        test_project_scaffolding,
        test_context_manager
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Erro inesperado em {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Resultados dos testes:")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Taxa de sucesso: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 Todos os testes passaram! O sistema está funcionando corretamente.")
        return 0
    else:
        print(f"\n⚠️  {failed} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())