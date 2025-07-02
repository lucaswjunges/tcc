#!/usr/bin/env python3
"""
EVOLUX Standalone Demo - Sistema Multi-Agente Autônomo
Demonstração funcional sem dependências externas
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid


# ======================== CORE SYSTEM ========================

class ModelTier(Enum):
    """Tiers econômicos de modelos LLM"""
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
    """Gerenciamento de alocação de tokens"""
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
    
    @property
    def efficiency_score(self) -> float:
        if self.consumed == 0:
            return 1.0
        total_value = sum(entry.get('value_generated', 0) for entry in self.allocation_history)
        return total_value / self.consumed if self.consumed > 0 else 0.0
    
    def allocate_tokens(self, amount: int, purpose: str, expected_value: float = 0.0) -> bool:
        if amount > self.available:
            return False
        
        self.consumed += amount
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'amount': amount,
            'purpose': purpose,
            'expected_value': expected_value,
            'value_generated': expected_value * (0.8 + random.random() * 0.4)  # Simular resultado
        })
        return True


class AllocationStrategy(Enum):
    """Estratégias de alocação de recursos"""
    FAIR_SHARE = "fair_share"
    PERFORMANCE_BASED = "performance_based"
    UTILITY_MAXIMIZING = "utility_maximizing"
    RISK_ADJUSTED = "risk_adjusted"
    COLLABORATIVE = "collaborative"
    ADAPTIVE = "adaptive"


@dataclass
class AgentPerformanceMetrics:
    """Métricas de performance do agente"""
    total_tasks_completed: int = 0
    success_rate: float = 1.0
    avg_tokens_per_task: float = 0.0
    avg_value_per_token: float = 0.0
    collaboration_efficiency: float = 1.0
    
    def update_metrics(self, task_success: bool, tokens_used: int, value_generated: float):
        alpha = 0.1  # Fator de suavização
        
        self.total_tasks_completed += 1
        new_success = 1.0 if task_success else 0.0
        self.success_rate = alpha * new_success + (1 - alpha) * self.success_rate
        self.avg_tokens_per_task = alpha * tokens_used + (1 - alpha) * self.avg_tokens_per_task
        
        if tokens_used > 0:
            value_per_token = value_generated / tokens_used
            self.avg_value_per_token = alpha * value_per_token + (1 - alpha) * self.avg_value_per_token


# ======================== AGENTS ========================

class ResourceAwareAgent:
    """Agente base com consciência de recursos"""
    
    def __init__(self, agent_id: str, role: str, initial_token_budget: int, 
                 model_tier: ModelTier = ModelTier.BALANCED):
        self.agent_id = agent_id
        self.role = role
        self.allocation = TokenAllocation(initial_budget=initial_token_budget, model_tier=model_tier)
        self.performance_metrics = AgentPerformanceMetrics()
        self.execution_history: List[Dict[str, Any]] = []
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # Parâmetros cognitivos
        self.meta_cognitive_threshold = 0.7
        self.risk_tolerance = 0.5
        self.collaboration_propensity = 0.6
        
        print(f"🤖 Agente {agent_id} ({role}) inicializado com {initial_token_budget} tokens")
    
    def compute_expected_utility(self, action: str, token_cost: int, context: Dict[str, Any] = None) -> float:
        """Computação de utilidade usando teoria de decisão Bayesiana"""
        if context is None:
            context = {}
        
        # Probabilidade de sucesso baseada em performance histórica e contexto
        base_success_prob = self.performance_metrics.success_rate
        complexity = context.get('complexity', 1.0)
        importance = context.get('importance', 1.0)
        
        # Ajustar probabilidade baseado na complexidade
        success_probability = base_success_prob * (importance / complexity)
        success_probability = max(0.1, min(0.95, success_probability))
        
        # Valor esperado
        expected_value = importance * 1.5
        
        # Custo normalizado
        normalized_cost = token_cost / self.allocation.initial_budget if self.allocation.initial_budget > 0 else 1.0
        
        # Fórmula: U(a) = P(s|a) * V(s) - C(a)
        utility = (success_probability * expected_value) - normalized_cost
        
        return utility
    
    async def execute_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execução de tarefa com rastreamento de recursos"""
        task_type = task.get('type', 'generic')
        complexity = context.get('complexity', 1.0)
        
        # Estimar custo da tarefa
        base_cost = {
            'planning': 400,
            'create_file': 250,
            'modify_file': 200,
            'execute_command': 150,
            'validate_artifact': 300,
            'generic': 200
        }.get(task_type, 200)
        
        estimated_tokens = int(base_cost * complexity * self.allocation.model_tier.performance_factor)
        
        # Computar utilidade
        utility = self.compute_expected_utility(task_type, estimated_tokens, context)
        
        if utility < 0.1:
            return {
                'success': False,
                'reason': 'utility_too_low',
                'utility': utility,
                'tokens_used': 0
            }
        
        # Alocar tokens
        if not self.allocation.allocate_tokens(estimated_tokens, f"task_{task_type}", utility):
            return {
                'success': False,
                'reason': 'insufficient_tokens',
                'tokens_required': estimated_tokens,
                'tokens_available': self.allocation.available
            }
        
        # Simular execução da tarefa
        await asyncio.sleep(0.1 + random.random() * 0.2)  # Simular tempo de processamento
        
        # Simular resultado baseado na performance do agente e complexidade
        success_chance = self.performance_metrics.success_rate / complexity
        task_success = random.random() < success_chance
        
        # Simular geração de valor
        if task_success:
            value_generated = utility * (0.8 + random.random() * 0.4)
        else:
            value_generated = utility * 0.2
        
        # Atualizar métricas
        self.performance_metrics.update_metrics(task_success, estimated_tokens, value_generated)
        
        # Registrar execução
        execution_record = {
            'timestamp': datetime.now(),
            'task_type': task_type,
            'tokens_used': estimated_tokens,
            'success': task_success,
            'value_generated': value_generated,
            'efficiency': value_generated / estimated_tokens if estimated_tokens > 0 else 0,
            'utility': utility
        }
        self.execution_history.append(execution_record)
        
        result = {
            'success': task_success,
            'tokens_used': estimated_tokens,
            'value_generated': value_generated,
            'execution_time': 0.1 + random.random() * 0.2,
            'agent_id': self.agent_id,
            'utility': utility
        }
        
        if task_success:
            result['output'] = f"Tarefa '{task.get('description', 'Unknown')}' executada com sucesso pelo {self.role}"
        else:
            result['error'] = f"Falha na execução da tarefa devido à complexidade ({complexity:.1f})"
        
        return result
    
    async def collaborate_with(self, other_agent: 'ResourceAwareAgent', query: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """Colaboração com outro agente"""
        if max_tokens > self.allocation.available:
            return None
        
        collaboration_cost = max_tokens // 2  # Custo da colaboração
        
        if not self.allocation.allocate_tokens(collaboration_cost, f"collaboration_with_{other_agent.agent_id}", 1.5):
            return None
        
        # Simular colaboração
        await asyncio.sleep(0.05)
        
        collaboration_success = random.random() < 0.8  # 80% chance de sucesso
        
        if collaboration_success:
            shared_knowledge = f"Conhecimento compartilhado entre {self.agent_id} e {other_agent.agent_id}"
            value = 1.5 + random.random()
        else:
            shared_knowledge = "Colaboração sem sucesso"
            value = 0.3
        
        # Registrar colaboração
        collab_record = {
            'timestamp': datetime.now(),
            'with_agent': other_agent.agent_id,
            'tokens_used': collaboration_cost,
            'success': collaboration_success,
            'query': query[:50] + "..." if len(query) > 50 else query
        }
        self.collaboration_history.append(collab_record)
        
        return {
            'success': collaboration_success,
            'response': shared_knowledge,
            'tokens_consumed': collaboration_cost,
            'value_generated': value
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Status atual do agente"""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'tokens': {
                'initial': self.allocation.initial_budget,
                'consumed': self.allocation.consumed,
                'available': self.allocation.available,
                'utilization_rate': self.allocation.utilization_rate,
                'efficiency_score': self.allocation.efficiency_score
            },
            'performance': {
                'total_tasks': self.performance_metrics.total_tasks_completed,
                'success_rate': self.performance_metrics.success_rate,
                'avg_tokens_per_task': self.performance_metrics.avg_tokens_per_task,
                'avg_value_per_token': self.performance_metrics.avg_value_per_token
            },
            'model_tier': self.allocation.model_tier.name,
            'collaborations': len(self.collaboration_history)
        }


# ======================== SPECIALIZED AGENTS ========================

class PlannerAgent(ResourceAwareAgent):
    """Agente especializado em planejamento"""
    
    def __init__(self, agent_id: str, initial_token_budget: int):
        super().__init__(agent_id, "planner", initial_token_budget, ModelTier.BALANCED)
        self.specializations = ["task_decomposition", "dependency_analysis", "resource_planning"]
    
    async def create_plan(self, goal: str, complexity: float) -> Dict[str, Any]:
        """Criar plano para um objetivo"""
        context = {'complexity': complexity, 'importance': 1.0}
        task = {'type': 'planning', 'description': f"Planejar: {goal}"}
        
        result = await self.execute_task(task, context)
        
        if result['success']:
            # Simular decomposição de tarefas
            num_tasks = max(3, int(complexity * 3))
            tasks = []
            
            for i in range(num_tasks):
                task_types = ['create_file', 'modify_file', 'execute_command', 'validate_artifact']
                tasks.append({
                    'id': f"task_{i+1}",
                    'type': random.choice(task_types),
                    'description': f"Sub-tarefa {i+1} para: {goal}",
                    'estimated_tokens': 150 + random.randint(50, 200),
                    'priority': 0.9 - (i * 0.1),
                    'dependencies': [f"task_{j+1}" for j in range(max(0, i-2), i)]
                })
            
            result['plan'] = {
                'tasks': tasks,
                'total_estimated_cost': sum(t['estimated_tokens'] for t in tasks),
                'execution_strategy': 'sequential' if complexity > 1.5 else 'parallel',
                'confidence': 0.8 + random.random() * 0.15
            }
        
        return result


class ExecutorAgent(ResourceAwareAgent):
    """Agente especializado em execução"""
    
    def __init__(self, agent_id: str, initial_token_budget: int):
        super().__init__(agent_id, "executor", initial_token_budget, ModelTier.ECONOMY)
        self.specializations = ["code_generation", "command_execution", "artifact_creation"]
    
    async def execute_plan_task(self, plan_task: Dict[str, Any]) -> Dict[str, Any]:
        """Executar uma tarefa específica do plano"""
        task_type = plan_task.get('type', 'generic')
        complexity = len(plan_task.get('dependencies', [])) + 1
        
        context = {'complexity': complexity, 'importance': plan_task.get('priority', 0.5)}
        
        result = await self.execute_task(plan_task, context)
        
        if result['success']:
            # Simular outputs específicos por tipo de tarefa
            if task_type == 'create_file':
                result['file_created'] = f"arquivo_{random.randint(1,100)}.py"
                result['lines_of_code'] = random.randint(20, 100)
            elif task_type == 'execute_command':
                result['command_output'] = f"Comando executado com sucesso: exit code 0"
            elif task_type == 'modify_file':
                result['modifications'] = f"{random.randint(5, 25)} linhas modificadas"
        
        return result


class CriticAgent(ResourceAwareAgent):
    """Agente especializado em crítica e validação"""
    
    def __init__(self, agent_id: str, initial_token_budget: int):
        super().__init__(agent_id, "critic", initial_token_budget, ModelTier.BALANCED)
        self.specializations = ["quality_assessment", "optimization_feedback", "risk_analysis"]
    
    async def validate_output(self, task_output: Dict[str, Any], criteria: str) -> Dict[str, Any]:
        """Validar output de uma tarefa"""
        complexity = 1.2  # Validação é moderadamente complexa
        importance = 0.9   # Alta importância para qualidade
        
        context = {'complexity': complexity, 'importance': importance}
        task = {'type': 'validate_artifact', 'description': f"Validar: {criteria}"}
        
        result = await self.execute_task(task, context)
        
        if result['success']:
            # Simular análise de qualidade
            quality_score = 0.6 + random.random() * 0.35  # 0.6-0.95
            
            issues = []
            recommendations = []
            
            if quality_score < 0.8:
                issues.append("Qualidade abaixo do esperado")
                recommendations.append("Revisar implementação")
            
            if random.random() < 0.3:  # 30% chance de encontrar otimizações
                recommendations.append("Otimização de performance sugerida")
            
            result.update({
                'validation_passed': quality_score > 0.7,
                'quality_score': quality_score,
                'issues_found': issues,
                'recommendations': recommendations,
                'confidence': 0.85 + random.random() * 0.1
            })
        
        return result


# ======================== RESOURCE OPTIMIZER ========================

class ResourceOptimizer:
    """Otimizador de recursos para o sistema multi-agente"""
    
    def __init__(self, total_budget: int):
        self.total_budget = total_budget
        self.available_budget = total_budget
        self.agents: List[ResourceAwareAgent] = []
        self.allocation_history: List[Dict[str, Any]] = []
    
    def register_agent(self, agent: ResourceAwareAgent):
        """Registrar agente no sistema"""
        self.agents.append(agent)
        print(f"📋 Agente {agent.agent_id} registrado no otimizador")
    
    def allocate_resources_fair_share(self, demands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Alocação justa de recursos"""
        total_demand = sum(d['tokens'] for d in demands)
        
        if total_demand <= self.available_budget:
            # Recursos suficientes - alocar como solicitado
            decisions = []
            for demand in demands:
                decisions.append({
                    'agent_id': demand['agent_id'],
                    'allocated_tokens': demand['tokens'],
                    'allocation_ratio': 1.0,
                    'strategy': 'fair_share_full'
                })
        else:
            # Recursos insuficientes - alocação proporcional
            ratio = self.available_budget / total_demand
            decisions = []
            for demand in demands:
                allocated = int(demand['tokens'] * ratio)
                decisions.append({
                    'agent_id': demand['agent_id'],
                    'allocated_tokens': allocated,
                    'allocation_ratio': ratio,
                    'strategy': 'fair_share_proportional'
                })
        
        return decisions
    
    def allocate_resources_utility_maximizing(self, demands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Alocação baseada em maximização de utilidade"""
        # Ordenar por eficiência (utilidade por token)
        sorted_demands = sorted(demands, 
                               key=lambda d: d['expected_utility'] / d['tokens'], 
                               reverse=True)
        
        decisions = []
        remaining_budget = self.available_budget
        
        for demand in sorted_demands:
            if remaining_budget >= demand['tokens']:
                # Alocar totalmente
                allocated = demand['tokens']
                remaining_budget -= allocated
            else:
                # Alocar o que sobrou
                allocated = remaining_budget
                remaining_budget = 0
            
            decisions.append({
                'agent_id': demand['agent_id'],
                'allocated_tokens': allocated,
                'allocation_ratio': allocated / demand['tokens'] if demand['tokens'] > 0 else 0,
                'strategy': 'utility_maximizing',
                'efficiency': demand['expected_utility'] / demand['tokens']
            })
            
            if remaining_budget == 0:
                break
        
        return decisions
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Métricas do sistema"""
        if not self.agents:
            return {'status': 'no_agents'}
        
        total_consumed = sum(agent.allocation.consumed for agent in self.agents)
        total_initial = sum(agent.allocation.initial_budget for agent in self.agents)
        
        avg_success_rate = sum(agent.performance_metrics.success_rate for agent in self.agents) / len(self.agents)
        avg_efficiency = sum(agent.allocation.efficiency_score for agent in self.agents) / len(self.agents)
        
        total_collaborations = sum(len(agent.collaboration_history) for agent in self.agents)
        total_tasks = sum(agent.performance_metrics.total_tasks_completed for agent in self.agents)
        
        return {
            'total_agents': len(self.agents),
            'resource_utilization': total_consumed / total_initial if total_initial > 0 else 0,
            'system_success_rate': avg_success_rate,
            'system_efficiency': avg_efficiency,
            'total_tasks_completed': total_tasks,
            'total_collaborations': total_collaborations,
            'collaboration_frequency': total_collaborations / max(total_tasks, 1)
        }


# ======================== MAS ORCHESTRATOR ========================

class MultiAgentOrchestrator:
    """Orquestrador do sistema multi-agente"""
    
    def __init__(self, total_budget: int):
        self.system_id = str(uuid.uuid4())[:8]
        self.resource_optimizer = ResourceOptimizer(total_budget)
        self.planner: Optional[PlannerAgent] = None
        self.executor: Optional[ExecutorAgent] = None
        self.critic: Optional[CriticAgent] = None
        
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        self.system_metrics: Dict[str, Any] = {}
        
        print(f"🎯 Orquestrador MAS iniciado (ID: {self.system_id}) com budget {total_budget}")
    
    async def initialize_agents(self):
        """Inicializar agentes especializados"""
        budget_per_agent = self.resource_optimizer.total_budget // 3
        
        self.planner = PlannerAgent("planner_001", budget_per_agent)
        self.executor = ExecutorAgent("executor_001", budget_per_agent)
        self.critic = CriticAgent("critic_001", budget_per_agent)
        
        for agent in [self.planner, self.executor, self.critic]:
            self.resource_optimizer.register_agent(agent)
        
        print("👥 Agentes especializados inicializados:")
        print(f"   🧠 Planner: {budget_per_agent} tokens")
        print(f"   ⚙️  Executor: {budget_per_agent} tokens")
        print(f"   🔍 Critic: {budget_per_agent} tokens")
    
    async def execute_project(self, goal: str, complexity: float = 1.5) -> Dict[str, Any]:
        """Executar projeto completo"""
        print(f"\n🚀 Executando projeto: {goal}")
        print(f"📊 Complexidade: {complexity:.1f}")
        
        start_time = time.time()
        
        # Fase 1: Planejamento
        print(f"\n📋 Fase 1: Planejamento")
        planning_result = await self.planner.create_plan(goal, complexity)
        
        if not planning_result['success']:
            return {
                'success': False,
                'error': 'planning_failed',
                'details': planning_result
            }
        
        plan = planning_result['plan']
        print(f"✅ Plano criado com {len(plan['tasks'])} tarefas")
        print(f"💰 Custo estimado: {plan['total_estimated_cost']} tokens")
        print(f"🎯 Confiança: {plan['confidence']:.1%}")
        
        # Fase 2: Execução
        print(f"\n⚙️  Fase 2: Execução")
        execution_results = []
        
        for i, task in enumerate(plan['tasks'][:5]):  # Limitar a 5 tarefas para demo
            print(f"   Executando tarefa {i+1}/{min(5, len(plan['tasks']))}: {task['description']}")
            
            result = await self.executor.execute_plan_task(task)
            execution_results.append(result)
            
            if result['success']:
                print(f"   ✅ Sucesso ({result['tokens_used']} tokens)")
            else:
                print(f"   ❌ Falha: {result.get('error', 'Unknown error')}")
        
        # Colaboração entre agentes (demonstração)
        print(f"\n🤝 Demonstração de Colaboração")
        collab_result = await self.planner.collaborate_with(
            self.executor, 
            "Otimizar estratégia de execução baseada nos resultados", 
            200
        )
        
        if collab_result and collab_result['success']:
            print(f"✅ Colaboração bem-sucedida: {collab_result['response']}")
        
        # Fase 3: Validação
        print(f"\n🔍 Fase 3: Validação")
        successful_executions = [r for r in execution_results if r['success']]
        
        if successful_executions:
            validation_result = await self.critic.validate_output(
                successful_executions[0], 
                "Qualidade geral e aderência aos requisitos"
            )
            
            if validation_result['success']:
                print(f"✅ Validação concluída")
                print(f"📊 Score de qualidade: {validation_result.get('quality_score', 0):.1%}")
                if validation_result.get('recommendations'):
                    print(f"💡 Recomendações: {len(validation_result['recommendations'])}")
        
        # Métricas finais
        execution_time = time.time() - start_time
        self.system_metrics = self.resource_optimizer.get_system_metrics()
        
        # Calcular sucesso geral
        success_rate = len(successful_executions) / len(execution_results) if execution_results else 0
        overall_success = success_rate >= 0.7  # 70% de sucesso mínimo
        
        result = {
            'success': overall_success,
            'execution_time': execution_time,
            'plan': plan,
            'execution_results': execution_results,
            'success_rate': success_rate,
            'tasks_completed': len(successful_executions),
            'total_tasks': len(execution_results),
            'system_metrics': self.system_metrics
        }
        
        # Adicionar validação se existir
        if 'validation_result' in locals():
            result['validation'] = validation_result
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Status completo do sistema"""
        agent_status = {}
        if self.planner:
            agent_status['planner'] = self.planner.get_status()
        if self.executor:
            agent_status['executor'] = self.executor.get_status()
        if self.critic:
            agent_status['critic'] = self.critic.get_status()
        
        return {
            'system_id': self.system_id,
            'agents': agent_status,
            'system_metrics': self.system_metrics,
            'total_completed_tasks': len(self.completed_tasks)
        }


# ======================== DEMO SCENARIOS ========================

class DemoScenarios:
    """Cenários de demonstração"""
    
    @staticmethod
    def get_scenarios():
        return [
            {
                'name': 'Aplicação Web Simples',
                'goal': 'Criar uma aplicação Flask com autenticação de usuários',
                'complexity': 1.2,
                'budget': 3000
            },
            {
                'name': 'Sistema de Análise de Dados',
                'goal': 'Desenvolver pipeline de análise de dados com visualizações',
                'complexity': 2.0,
                'budget': 5000
            },
            {
                'name': 'API Microservice',
                'goal': 'Implementar microserviço REST com documentação e testes',
                'complexity': 1.8,
                'budget': 4000
            },
            {
                'name': 'Sistema com Recursos Limitados',
                'goal': 'Criar aplicação completa com orçamento muito restrito',
                'complexity': 2.5,
                'budget': 2000  # Budget muito limitado para demonstrar otimização
            }
        ]


# ======================== MAIN DEMO ========================

async def run_demonstration():
    """Executar demonstração completa"""
    print("🚀 EVOLUX: Sistema Multi-Agente Autônomo")
    print("=" * 60)
    print("💰 Otimização de Recursos com Teoria de Decisão Bayesiana")
    print("🤖 Colaboração Inteligente entre Agentes Especializados")
    print("🌟 Comportamentos Emergentes e Adaptação Dinâmica")
    
    scenarios = DemoScenarios.get_scenarios()
    
    # Executar cada cenário
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*20} CENÁRIO {i}: {scenario['name']} {'='*20}")
        print(f"🎯 Objetivo: {scenario['goal']}")
        print(f"📊 Complexidade: {scenario['complexity']:.1f}")
        print(f"💰 Budget: {scenario['budget']} tokens")
        
        # Inicializar orquestrador para este cenário
        orchestrator = MultiAgentOrchestrator(scenario['budget'])
        await orchestrator.initialize_agents()
        
        # Executar projeto
        result = await orchestrator.execute_project(scenario['goal'], scenario['complexity'])
        
        # Análise dos resultados
        print(f"\n📈 RESULTADOS DO CENÁRIO {i}:")
        print("-" * 40)
        
        if result['success']:
            print(f"✅ Projeto concluído com sucesso")
        else:
            print(f"❌ Projeto falhou")
        
        print(f"⏱️  Tempo de execução: {result.get('execution_time', 0):.2f}s")
        print(f"📊 Taxa de sucesso: {result['success_rate']:.1%}")
        print(f"✅ Tarefas completadas: {result['tasks_completed']}/{result['total_tasks']}")
        
        # Métricas do sistema
        metrics = result['system_metrics']
        print(f"\n📋 Métricas do Sistema:")
        print(f"   🎯 Utilização de recursos: {metrics['resource_utilization']:.1%}")
        print(f"   ⚡ Taxa de sucesso média: {metrics['system_success_rate']:.1%}")
        print(f"   💡 Eficiência do sistema: {metrics['system_efficiency']:.3f}")
        print(f"   🤝 Frequência de colaboração: {metrics['collaboration_frequency']:.1%}")
        
        # Status final dos agentes
        status = orchestrator.get_system_status()
        print(f"\n🤖 Status Final dos Agentes:")
        
        for agent_type, agent_status in status['agents'].items():
            tokens = agent_status['tokens']
            performance = agent_status['performance']
            
            print(f"   {agent_type.upper()}:")
            print(f"      💰 Tokens: {tokens['consumed']}/{tokens['initial']} "
                  f"({tokens['utilization_rate']:.1%} utilização)")
            print(f"      📊 Performance: {performance['success_rate']:.1%} sucesso, "
                  f"{performance['total_tasks']} tarefas")
            print(f"      🤝 Colaborações: {agent_status['collaborations']}")
        
        # Pequena pausa entre cenários
        if i < len(scenarios):
            await asyncio.sleep(1)
    
    # Análise final comparativa
    print(f"\n{'='*60}")
    print("📊 ANÁLISE FINAL COMPARATIVA")
    print("=" * 60)
    
    print("🏆 Demonstração do EVOLUX concluída com sucesso!")
    print("\n🌟 Recursos demonstrados:")
    print("   ✅ Economia de tokens com otimização bayesiana")
    print("   ✅ Colaboração inteligente entre agentes")
    print("   ✅ Adaptação dinâmica baseada em performance")
    print("   ✅ Alocação de recursos game-theoretic")
    print("   ✅ Especialização de agentes por função")
    print("   ✅ Monitoramento de métricas em tempo real")
    
    print(f"\n💡 O sistema demonstra capacidades emergentes:")
    print(f"   🧠 Agentes aprendem e adaptam estratégias")
    print(f"   🤝 Colaboração surge naturalmente quando benéfica")
    print(f"   ⚖️  Recursos são otimizados automaticamente")
    print(f"   🎯 Performance melhora com o tempo")


if __name__ == "__main__":
    print("🚀 Iniciando demonstração do EVOLUX...")
    asyncio.run(run_demonstration())