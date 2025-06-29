#!/usr/bin/env python3
"""
Teste simples e rápido das funcionalidades principais
"""

import os
import asyncio
import tempfile

def test_simple_workflow():
    """Teste de workflow simplificado"""
    print("🔄 Testando workflow simplificado...")
    
    try:
        # Configurar ambiente
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        
        # Importar componentes essenciais
        from evolux_engine import (
            AdvancedSystemConfig,
            EnterpriseObservabilityService,
            SecurityGateway,
            ModelRouter,
            IntelligentProjectScaffolding
        )
        from evolux_engine.llms.model_router import TaskCategory
        from evolux_engine.security.security_gateway import SecurityLevel
        from evolux_engine.core.project_scaffolding import ProjectType, Framework
        
        # 1. Configuração
        config = AdvancedSystemConfig()
        print(f"✅ Config: {config.default_llm_provider}")
        
        # 2. Observabilidade (sem background monitoring)
        from evolux_engine.services.enterprise_observability import MetricType
        obs = EnterpriseObservabilityService(config)
        obs.record_metric("test.metric", 42.0, MetricType.GAUGE)
        metrics = obs.get_performance_metrics()
        print(f"✅ Observabilidade: CPU {metrics.cpu_percent}%")
        
        # 3. Segurança
        security = SecurityGateway(SecurityLevel.STRICT)
        result = asyncio.run(security.validate_command("ls -la"))
        print(f"✅ Segurança: comando seguro = {result.is_safe}")
        
        # 4. Model Router
        router = ModelRouter()
        model = router.select_model(TaskCategory.CODE_GENERATION)
        print(f"✅ Router: modelo = {model}")
        
        # 5. Project Scaffolding
        scaffolding = IntelligentProjectScaffolding(config)
        analysis = scaffolding.analyze_project_goal("Create a Flask web app")
        print(f"✅ Scaffolding: tipo = {analysis['project_type']}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            scaffold = scaffolding.generate_project_scaffold(
                goal="Simple test app",
                project_name="TestApp",
                output_dir=temp_dir,
                force_type=ProjectType.WEB_APPLICATION,
                force_framework=Framework.FLASK
            )
            
            success = scaffolding.materialize_scaffold(scaffold, temp_dir)
            print(f"✅ Scaffold materializado: {success}")
        
        print("🎉 Workflow simplificado passou!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_functionality():
    """Teste das funcionalidades centrais"""
    print("\n🧪 Testando funcionalidades centrais...")
    
    try:
        os.environ['EVOLUX_OPENROUTER_API_KEY'] = 'test_key_1234567890'
        
        # Test LLM Factory
        from evolux_engine import LLMFactory, ModelRouter, AdvancedSystemConfig
        
        config = AdvancedSystemConfig()
        router = ModelRouter()
        factory = LLMFactory(router)
        factory.configure_from_advanced_config(config)
        
        stats = factory.get_factory_stats()
        print(f"✅ LLM Factory: {stats['configured_providers']} provedores")
        
        # Test Prompt Engine
        from evolux_engine import PromptEngine
        from evolux_engine.prompts.prompt_engine import PromptContext, TaskCategory
        
        engine = PromptEngine()
        context = PromptContext(
            project_goal="Test API",
            project_type="api",
            task_description="Create endpoint"
        )
        
        prompt = engine.build_prompt("code_generation", context)
        print(f"✅ Prompt Engine: prompt gerado ({len(prompt) if prompt else 0} chars)")
        
        # Test template selection
        template_name = engine.get_template_for_category(TaskCategory.VALIDATION)
        print(f"✅ Template para validação: {template_name}")
        
        print("🎉 Funcionalidades centrais passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nas funcionalidades centrais: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🚀 Teste rápido do Evolux Engine")
    print("=" * 40)
    
    tests = [
        test_simple_workflow,
        test_core_functionality
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
            print(f"❌ Erro em {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Resultados:")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    
    if failed == 0:
        print("\n🎉 Sistema funcionando perfeitamente!")
        return 0
    else:
        print(f"\n⚠️ {failed} teste(s) falharam.")
        return 1

if __name__ == "__main__":
    exit(main())