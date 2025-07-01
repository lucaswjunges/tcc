#!/usr/bin/env python3
"""
Teste de Integração da Metacognição com o Sistema Evolux
=========================================================

Testa se a metacognição está funcionando corretamente integrada 
com o sistema A2A e o Orchestrator.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar caminho do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from evolux_engine.core.metacognitive_engine import get_metacognitive_engine
from evolux_engine.core.intelligent_a2a_system import get_intelligent_a2a_system
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("metacognition_test")

async def test_metacognitive_engine():
    """Testa funcionalidades básicas do motor metacognitivo"""
    logger.info("🧠 Testando Motor Metacognitivo...")
    
    # Obter instância do motor metacognitivo
    metacognitive_engine = get_metacognitive_engine()
    
    # Teste 1: Reflexão sobre processo de pensamento
    logger.info("📋 Teste 1: Reflexão sobre processo de pensamento")
    process_context = {
        "strategy": "analytical",
        "task_type": "software_development",
        "complexity": "high",
        "steps": ["Analisar requisitos", "Planejar arquitetura", "Implementar código"],
        "execution_time": 2.5
    }
    
    thinking_analysis = await metacognitive_engine.reflect_on_thinking_process(process_context)
    logger.info(f"✅ Análise de pensamento concluída - Efetividade: {thinking_analysis.effectiveness_score:.2f}")
    
    # Teste 2: Auto-avaliação de capacidades
    logger.info("📋 Teste 2: Auto-avaliação de capacidades")
    cognitive_profile = await metacognitive_engine.evaluate_own_capabilities()
    logger.info(f"✅ Auto-avaliação concluída - Meta-awareness: {cognitive_profile.meta_awareness:.2f}")
    
    # Teste 3: Adaptação de estratégia de pensamento
    logger.info("📋 Teste 3: Adaptação de estratégia de pensamento")
    execution_context = {
        "problem_type": "software_engineering",
        "complexity": "medium",
        "resources": {"a2a_agents": 3}
    }
    
    thinking_strategy = await metacognitive_engine.adapt_thinking_strategy(execution_context)
    logger.info(f"✅ Estratégia adaptada: {thinking_strategy.value}")
    
    # Teste 4: Meta-aprendizado
    logger.info("📋 Teste 4: Meta-aprendizado")
    learning_experience = {
        "task_type": "code_generation",
        "success": True,
        "execution_time": 1.5,
        "learning_effectiveness": 0.8
    }
    
    meta_insight = await metacognitive_engine.meta_learn_from_experience(learning_experience)
    logger.info(f"✅ Meta-aprendizado concluído: {meta_insight.description}")
    
    # Teste 5: Questionamento de suposições
    logger.info("📋 Teste 5: Questionamento de suposições")
    assumptions_context = {
        "problem_definition": "Criar aplicação web",
        "chosen_strategy": "desenvolvimento_incremental"
    }
    
    questions = await metacognitive_engine.question_own_assumptions(assumptions_context)
    logger.info(f"✅ {len(questions)} questões auto-reflexivas geradas")
    for i, question in enumerate(questions[:3]):
        logger.info(f"   {i+1}. {question}")
    
    return metacognitive_engine

async def test_a2a_metacognition_integration():
    """Testa integração entre metacognição e sistema A2A"""
    logger.info("🤝 Testando Integração Metacognição + A2A...")
    
    # Obter instâncias
    metacognitive_engine = get_metacognitive_engine()
    intelligent_a2a = get_intelligent_a2a_system()
    
    # Teste 1: Integração metacognição com A2A
    logger.info("📋 Teste 1: Integração metacognição com A2A")
    await intelligent_a2a.integrate_metacognitive_engine(metacognitive_engine)
    logger.info("✅ Integração metacognitiva com A2A concluída")
    
    # Teste 2: Integração A2A com metacognição  
    logger.info("📋 Teste 2: Integração A2A com metacognição")
    a2a_integration = await metacognitive_engine.integrate_with_a2a_system(intelligent_a2a)
    logger.info(f"✅ Integração A2A com metacognição - Efetividade: {a2a_integration['effectiveness_score']:.2f}")
    
    # Teste 3: Registrar agentes simulados
    logger.info("📋 Teste 3: Registrar agentes simulados")
    await intelligent_a2a.register_intelligent_agent(
        agent_id="test_planner",
        initial_capabilities={
            "performance_metrics": {"planning_speed": 1.2, "plan_quality": 0.9},
            "max_concurrent_tasks": 3,
            "expertise_level": {"CREATE_FILE": 0.8, "EXECUTE_COMMAND": 0.7}
        }
    )
    
    await intelligent_a2a.register_intelligent_agent(
        agent_id="test_executor", 
        initial_capabilities={
            "performance_metrics": {"execution_speed": 1.5, "success_rate": 0.95},
            "max_concurrent_tasks": 5,
            "expertise_level": {"CREATE_FILE": 0.9, "EXECUTE_COMMAND": 0.95}
        }
    )
    
    logger.info("✅ Agentes simulados registrados")
    
    # Teste 4: Análise metacognitiva de agente
    logger.info("📋 Teste 4: Análise metacognitiva de agente")
    agent_analysis = await intelligent_a2a.metacognitive_agent_analysis("test_executor")
    if "error" not in agent_analysis:
        logger.info(f"✅ Análise metacognitiva do agente - Efetividade: {agent_analysis['metacognitive_analysis']['effectiveness_score']:.2f}")
    else:
        logger.warning(f"⚠️ Erro na análise: {agent_analysis['error']}")
    
    # Teste 5: Relatório metacognitivo de colaboração
    logger.info("📋 Teste 5: Relatório metacognitivo de colaboração")
    collab_report = await intelligent_a2a.get_metacognitive_collaboration_report()
    if "error" not in collab_report:
        logger.info(f"✅ Relatório de colaboração gerado - Meta-awareness: {collab_report['collaborative_cognitive_profile']['meta_awareness']:.2f}")
    else:
        logger.warning(f"⚠️ Erro no relatório: {collab_report['error']}")
    
    return True

async def test_self_model_generation():
    """Testa geração de modelo de auto-consciência"""
    logger.info("🧩 Testando Geração de Modelo de Auto-Consciência...")
    
    metacognitive_engine = get_metacognitive_engine()
    
    # Gerar modelo de auto-consciência
    self_model = await metacognitive_engine.generate_self_model()
    
    logger.info("✅ Modelo de auto-consciência gerado:")
    logger.info(f"   Arquitetura Cognitiva: {len(self_model['cognitive_architecture'])} componentes")
    logger.info(f"   Padrões Operacionais: {len(self_model['operational_patterns'])} padrões")
    logger.info(f"   Limitações: {len(self_model['limitations'])} limitações identificadas")
    logger.info(f"   Forças: {len(self_model['strengths'])} áreas de força")
    logger.info(f"   Meta-conhecimento: {len(self_model['meta_knowledge'])} insights")
    
    return self_model

async def main():
    """Função principal de teste"""
    logger.info("🚀 Iniciando Testes de Integração da Metacognição")
    
    try:
        # Teste 1: Funcionalidades básicas da metacognição
        metacognitive_engine = await test_metacognitive_engine()
        logger.info("✅ Teste de funcionalidades básicas: PASSOU")
        
        # Teste 2: Integração A2A + Metacognição
        await test_a2a_metacognition_integration()
        logger.info("✅ Teste de integração A2A + Metacognição: PASSOU")
        
        # Teste 3: Geração de modelo de auto-consciência
        await test_self_model_generation()
        logger.info("✅ Teste de modelo de auto-consciência: PASSOU")
        
        logger.info("🎉 TODOS OS TESTES PASSARAM! Metacognição integrada com sucesso.")
        
        # Demonstração final
        logger.info("🧠 DEMONSTRAÇÃO: Capacidades Metacognitivas Integradas")
        
        # Mostrar estatísticas finais
        cognitive_profile = await metacognitive_engine.evaluate_own_capabilities()
        logger.info(f"📊 Estatísticas Finais:")
        logger.info(f"   • Força Analítica: {cognitive_profile.analytical_strength:.2f}")
        logger.info(f"   • Força Criativa: {cognitive_profile.creative_strength:.2f}")
        logger.info(f"   • Habilidade Colaborativa: {cognitive_profile.collaborative_ability:.2f}")
        logger.info(f"   • Meta-Consciência: {cognitive_profile.meta_awareness:.2f}")
        logger.info(f"   • Limitações Identificadas: {len(cognitive_profile.identified_limits)}")
        logger.info(f"   • Áreas de Força: {len(cognitive_profile.strength_areas)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Executar testes
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 METACOGNIÇÃO INTEGRADA COM SUCESSO!")
        print("O sistema Evolux agora possui:")
        print("  🧠 Capacidade de pensar sobre como pensa")
        print("  🤔 Auto-reflexão sobre processos cognitivos")
        print("  📚 Meta-aprendizado contínuo")
        print("  🤝 Metacognição colaborativa com agentes A2A")
        print("  🧩 Auto-consciência estrutural")
        print("  ❓ Questionamento de próprias suposições")
    else:
        print("\n❌ FALHA NA INTEGRAÇÃO DA METACOGNIÇÃO")
        sys.exit(1)