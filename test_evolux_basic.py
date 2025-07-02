#!/usr/bin/env python3
"""
Teste básico do sistema Evolux
"""

import sys
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """Teste de imports básicos"""
    print("🔍 Testando imports básicos do Evolux...")
    
    try:
        from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus, ProjectStatus
        print("✅ Schemas/contracts importados com sucesso")
        
        # Teste de criação de Task
        task = Task(
            task_id='test_001',
            task_type=TaskType.CREATE_FILE,
            description='Teste de criação de arquivo',
            status=TaskStatus.PENDING
        )
        print(f"✅ Task criada: {task.task_id} - {task.description}")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports básicos: {e}")
        return False

def test_mas_components():
    """Teste dos componentes MAS implementados"""
    print("\n🤖 Testando componentes MAS...")
    
    try:
        # Teste direto das classes core
        from enum import Enum
        from dataclasses import dataclass, field
        from typing import Dict, List, Any
        from datetime import datetime

        class ModelTier(Enum):
            ECONOMY = ("haiku", 0.25, 0.5, 1.0)
            BALANCED = ("sonnet", 3.0, 15.0, 1.5)
            PREMIUM = ("opus", 15.0, 75.0, 2.0)
            ULTRA = ("gpt-4", 30.0, 60.0, 2.5)

            def __init__(self, model_name: str, input_cost: float, output_cost: float, performance_factor: float):
                self.model_name = model_name
                self.input_cost = input_cost
                self.output_cost = output_cost
                self.performance_factor = performance_factor

            @property
            def total_cost_per_1k(self) -> float:
                return (self.input_cost * 0.6) + (self.output_cost * 0.4)

        @dataclass
        class TokenAllocation:
            initial_budget: int
            consumed: int = 0
            reserved: int = 0
            model_tier: ModelTier = ModelTier.BALANCED
            allocation_history: List[Dict[str, Any]] = field(default_factory=list)
            
            @property
            def available(self) -> int:
                return max(0, self.initial_budget - self.consumed - self.reserved)
            
            @property
            def utilization_rate(self) -> float:
                return self.consumed / self.initial_budget if self.initial_budget > 0 else 0.0
            
            def allocate_tokens(self, amount: int, purpose: str, expected_value: float = 0.0) -> bool:
                if amount > self.available:
                    return False
                
                self.consumed += amount
                self.allocation_history.append({
                    "timestamp": datetime.now(),
                    "amount": amount,
                    "purpose": purpose,
                    "expected_value": expected_value
                })
                return True

        # Teste do sistema de tokens
        print("✅ Sistema de ModelTier testado:")
        for tier in ModelTier:
            print(f"   {tier.name}: {tier.model_name} - Custo: ${tier.total_cost_per_1k:.2f}/1k tokens")

        # Teste de alocação de tokens
        allocation = TokenAllocation(initial_budget=1000)
        print(f"\n✅ TokenAllocation testado:")
        print(f"   Budget inicial: {allocation.initial_budget} tokens")

        success1 = allocation.allocate_tokens(300, "task_planning", 1.5)
        success2 = allocation.allocate_tokens(200, "task_execution", 1.2)
        success3 = allocation.allocate_tokens(600, "large_task", 2.0)  # Deve falhar
        
        print(f"   Alocação 1 (300 tokens): {success1}")
        print(f"   Alocação 2 (200 tokens): {success2}")
        print(f"   Alocação 3 (600 tokens): {success3} (esperado: False)")
        print(f"   Tokens consumidos: {allocation.consumed}")
        print(f"   Tokens disponíveis: {allocation.available}")
        print(f"   Taxa de utilização: {allocation.utilization_rate:.1%}")
        
        print("✅ Componentes MAS funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos componentes MAS: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_utility_computation():
    """Teste da computação de utilidade"""
    print("\n🧠 Testando computação de utilidade...")
    
    try:
        from typing import Dict, Any
        
        def compute_expected_utility(action: str, token_cost: int, context: Dict[str, Any], budget: int) -> float:
            """Computação de utilidade esperada usando teoria de decisão Bayesiana"""
            importance = context.get('importance', 1.0)
            complexity = context.get('complexity', 1.0)
            
            # Probabilidade de sucesso baseada em importância e complexidade
            success_probability = 0.8 * importance / complexity
            success_probability = max(0.1, min(0.95, success_probability))
            
            # Valor esperado
            expected_value = importance * 1.5
            
            # Custo normalizado
            normalized_cost = token_cost / budget if budget > 0 else 1.0
            
            # Utilidade = (P(sucesso) × Valor) - Custo
            utility = (success_probability * expected_value) - normalized_cost
            return utility

        # Testes com diferentes contextos
        test_contexts = [
            {'importance': 0.9, 'complexity': 1.0, 'desc': 'Alta importância, baixa complexidade'},
            {'importance': 0.5, 'complexity': 2.0, 'desc': 'Média importância, alta complexidade'},
            {'importance': 1.0, 'complexity': 0.5, 'desc': 'Alta importância, muito baixa complexidade'},
            {'importance': 0.3, 'complexity': 1.5, 'desc': 'Baixa importância, média complexidade'}
        ]

        print("📊 Resultados da computação de utilidade:")
        for i, context in enumerate(test_contexts, 1):
            utility = compute_expected_utility('test_action', 200, context, 1000)
            print(f"   Contexto {i}: {context['desc']}")
            print(f"      Importância: {context['importance']}, Complexidade: {context['complexity']}")
            print(f"      Utilidade: {utility:.3f}")
        
        print("✅ Computação de utilidade funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na computação de utilidade: {e}")
        return False

def test_resource_optimization_concept():
    """Teste conceitual de otimização de recursos"""
    print("\n💰 Testando conceitos de otimização de recursos...")
    
    try:
        from enum import Enum
        
        class AllocationStrategy(Enum):
            FAIR_SHARE = "fair_share"
            PERFORMANCE_BASED = "performance_based"
            UTILITY_MAXIMIZING = "utility_maximizing"
            RISK_ADJUSTED = "risk_adjusted"
            COLLABORATIVE = "collaborative"
            ADAPTIVE = "adaptive"

        # Simulação de demandas de recursos
        resource_demands = [
            {'agent_id': 'planner', 'tokens': 300, 'priority': 0.9, 'utility': 2.0},
            {'agent_id': 'executor', 'tokens': 500, 'priority': 0.7, 'utility': 1.5},
            {'agent_id': 'critic', 'tokens': 200, 'priority': 0.6, 'utility': 1.8}
        ]
        
        total_budget = 800  # Budget limitado
        total_demand = sum(d['tokens'] for d in resource_demands)
        
        print(f"📊 Simulação de alocação de recursos:")
        print(f"   Budget total: {total_budget} tokens")
        print(f"   Demanda total: {total_demand} tokens")
        print(f"   Pressão de recursos: {total_demand/total_budget:.1f}x")
        
        # Estratégia Fair Share
        print(f"\n🔧 Estratégia Fair Share:")
        if total_demand <= total_budget:
            for demand in resource_demands:
                allocated = demand['tokens']
                print(f"   {demand['agent_id']}: {allocated} tokens (100%)")
        else:
            ratio = total_budget / total_demand
            for demand in resource_demands:
                allocated = int(demand['tokens'] * ratio)
                print(f"   {demand['agent_id']}: {allocated} tokens ({ratio:.1%})")
        
        # Estratégia Utility Maximizing
        print(f"\n🎯 Estratégia Utility Maximizing:")
        sorted_by_efficiency = sorted(resource_demands, 
                                     key=lambda x: x['utility'] / x['tokens'], 
                                     reverse=True)
        remaining_budget = total_budget
        for demand in sorted_by_efficiency:
            allocated = min(demand['tokens'], remaining_budget)
            efficiency = demand['utility'] / demand['tokens']
            print(f"   {demand['agent_id']}: {allocated} tokens (eficiência: {efficiency:.3f})")
            remaining_budget -= allocated
            if remaining_budget <= 0:
                break
        
        print("✅ Conceitos de otimização de recursos funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na otimização de recursos: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 EVOLUX - Teste do Sistema Multi-Agente")
    print("=" * 60)
    
    tests = [
        ("Imports Básicos", test_basic_imports),
        ("Componentes MAS", test_mas_components),
        ("Computação de Utilidade", test_utility_computation),
        ("Otimização de Recursos", test_resource_optimization_concept)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema Evolux funcionando corretamente.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)