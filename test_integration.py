#!/usr/bin/env python3
"""
Teste de integração do sistema completo Evolux Engine
"""

import os
import asyncio
import tempfile
import shutil
from pathlib import Path

def test_full_integration():
    """Teste de integração completo"""
    print("🔗 Testando integração completa do sistema...")
    
    try:
        # Configurar ambiente
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        
        # Importar todos os componentes
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
        from evolux_engine.llms.model_router import TaskCategory
        from evolux_engine.security.security_gateway import SecurityLevel
        from evolux_engine.core.project_scaffolding import ProjectType, Framework
        
        print("✅ Todos os componentes importados")
        
        # 1. Configurar sistema
        config = AdvancedSystemConfig()
        config_manager = ConfigurationManager()
        
        # 2. Inicializar observabilidade
        observability = EnterpriseObservabilityService(config)
        observability.start_monitoring()
        
        # 3. Inicializar segurança
        security = SecurityGateway(SecurityLevel.STRICT)
        
        # 4. Inicializar componentes LLM
        model_router = ModelRouter()
        llm_factory = LLMFactory(model_router)
        llm_factory.configure_from_advanced_config(config)
        
        # 5. Inicializar prompt engine
        prompt_engine = PromptEngine()
        
        # 6. Inicializar scaffolding
        scaffolding = IntelligentProjectScaffolding(config)
        
        # 7. Inicializar context manager
        context_manager = AdvancedContextManager(config)
        
        print("✅ Todos os componentes inicializados")
        
        # Teste de workflow completo
        with tempfile.TemporaryDirectory() as temp_dir:
            # Criar projeto
            project_goal = "Create a REST API for a blog management system"
            
            # 1. Criar contexto do projeto
            context = context_manager.create_new_project_context(
                goal=project_goal,
                project_name="Blog API"
            )
            print(f"✅ Contexto criado: {context.project_id}")
            
            # 2. Analisar goal e gerar scaffold
            analysis = scaffolding.analyze_project_goal(project_goal)
            scaffold = scaffolding.generate_project_scaffold(
                goal=project_goal,
                project_name="BlogAPI",
                output_dir=temp_dir,
                force_type=ProjectType.API_SERVICE,
                force_framework=Framework.FASTAPI
            )
            print(f"✅ Scaffold gerado: {scaffold.name}")
            
            # 3. Materializar scaffold
            success = scaffolding.materialize_scaffold(scaffold, temp_dir)
            print(f"✅ Scaffold materializado: {success}")
            
            # 4. Validar comandos de setup
            setup_commands = [
                "pip install fastapi",
                "python main.py",
                "pytest tests/"
            ]
            
            for cmd in setup_commands:
                result = asyncio.run(security.validate_command(cmd))
                if result.is_safe:
                    print(f"✅ Comando seguro: {cmd}")
                else:
                    print(f"❌ Comando bloqueado: {cmd} - {result.blocked_reason}")
            
            # 5. Selecionar modelo para diferentes tarefas
            code_model = model_router.select_model(TaskCategory.CODE_GENERATION)
            plan_model = model_router.select_model(TaskCategory.PLANNING)
            print(f"✅ Modelos selecionados - Code: {code_model}, Plan: {plan_model}")
            
            # 6. Gerar prompts
            from evolux_engine.prompts.prompt_engine import PromptContext
            
            context_obj = PromptContext(
                project_goal=project_goal,
                project_type="api_service",
                task_description="Create main API file"
            )
            
            prompt = prompt_engine.build_prompt("code_generation", context_obj)
            if prompt:
                print(f"✅ Prompt gerado ({len(prompt)} chars)")
            else:
                print("❌ Falha ao gerar prompt")
            
            # 7. Salvar contexto com snapshot
            context_manager.save_project_context(context, create_snapshot=True)
            print("✅ Contexto salvo com snapshot")
            
            # 8. Verificar métricas
            with observability.time_operation("test_operation"):
                # Simular operação
                pass
            
            observability.record_task_completion(True, 1500.0)
            observability.record_llm_request(True, "openrouter", "deepseek", 2000.0)
            
            metrics = observability.get_performance_metrics()
            print(f"✅ Métricas coletadas - Tasks: {metrics.completed_tasks}")
            
            # 9. Verificar health
            health = observability.get_health_summary()
            print(f"✅ Sistema saudável: {health['overall_healthy']}")
            
            # 10. Estatísticas finais
            stats = {
                'router': model_router.get_routing_stats(),
                'security': security.get_security_stats(),
                'context': context_manager.get_manager_stats(),
                'observability': observability.create_dashboard_data()
            }
            
            print("✅ Estatísticas coletadas de todos os componentes")
            
        # Cleanup
        observability.stop_monitoring()
        context_manager.cleanup_and_shutdown()
        
        print("🎉 Teste de integração completo passou!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_integration():
    """Teste de funcionalidades assíncronas"""
    print("\n⚡ Testando integração assíncrona...")
    
    async def async_test():
        try:
            from evolux_engine import (
                EnterpriseObservabilityService,
                AdvancedSystemConfig,
                SecurityGateway
            )
            from evolux_engine.security.security_gateway import SecurityLevel
            
            os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
            config = AdvancedSystemConfig()
            
            # Teste async de observabilidade
            observability = EnterpriseObservabilityService(config)
            
            async with observability.async_trace("async_operation") as span_id:
                observability.add_trace_log(span_id, "Starting async operation")
                await asyncio.sleep(0.1)  # Simular operação async
                observability.add_trace_log(span_id, "Async operation completed")
            
            print("✅ Tracing assíncrono funcionando")
            
            # Teste async de segurança
            security = SecurityGateway(SecurityLevel.STRICT)
            
            commands = ["ls -la", "python script.py", "git status"]
            results = await asyncio.gather(*[
                security.validate_command(cmd) for cmd in commands
            ])
            
            safe_count = sum(1 for result in results if result.is_safe)
            print(f"✅ Validação assíncrona: {safe_count}/{len(commands)} comandos seguros")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste assíncrono: {e}")
            return False
    
    return asyncio.run(async_test())

def main():
    """Função principal"""
    print("🚀 Iniciando testes de integração do Evolux Engine")
    print("=" * 60)
    
    tests = [
        test_full_integration,
        test_async_integration
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
    print(f"📊 Resultados dos testes de integração:")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Taxa de sucesso: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 Todos os testes de integração passaram!")
        print("🔧 O sistema Evolux Engine está totalmente funcional e integrado.")
        return 0
    else:
        print(f"\n⚠️  {failed} teste(s) de integração falharam.")
        return 1

if __name__ == "__main__":
    exit(main())