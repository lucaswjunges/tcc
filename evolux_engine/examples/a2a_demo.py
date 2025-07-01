#!/usr/bin/env python3
"""
Demonstração do Sistema Parallel Handoff A2A
===========================================

Este exemplo demonstra as capacidades do sistema Agent-to-Agent (A2A)
implementado no Evolux, mostrando transferência coordenada entre agentes.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Imports do sistema A2A
from evolux_engine.core.agent_handoff import (
    AgentHandoffCoordinator, HandoffRequest, HandoffType, 
    get_handoff_coordinator, handoff_session
)
from evolux_engine.core.evolux_a2a_integration import EvoluxA2AIntegration, A2ACapableMixin
from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus, ProjectContext
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("a2a_demo")


class DemoExecutorAgent(A2ACapableMixin):
    """Agente executor de demonstração com capacidades A2A"""
    
    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
        self.execution_queue = []
        self.completed_tasks = []
        
        # Registrar no coordenador
        coordinator = get_handoff_coordinator()
        coordinator.register_agent(
            agent_id, 
            self, 
            ["handle_task_delegation", "handle_context_transfer"]
        )
        
        logger.info(f"DemoExecutorAgent {agent_id} inicializado")
    
    async def _process_received_handoff(self, request):
        """Processa handoff recebido"""
        if request.handoff_type == HandoffType.TASK_DELEGATION:
            await self._handle_task_delegation_demo(request)
        elif request.handoff_type == HandoffType.CONTEXT_TRANSFER:
            await self._handle_context_transfer_demo(request)
    
    async def _handle_task_delegation_demo(self, request):
        """Processa delegação de tarefa"""
        task_data = request.data_payload.get('task', {})
        
        logger.info(f"Executor {self.agent_id}: Recebendo tarefa {task_data.get('task_id')}")
        
        # Simular execução da tarefa
        await asyncio.sleep(0.5)  # Simular processamento
        
        # Adicionar à fila de execução
        self.execution_queue.append({
            'task_id': task_data.get('task_id'),
            'description': task_data.get('description'),
            'received_from': request.sender_agent_id,
            'received_at': datetime.utcnow()
        })
        
        logger.info(f"Executor {self.agent_id}: Tarefa {task_data.get('task_id')} adicionada à fila")
    
    async def _handle_context_transfer_demo(self, request):
        """Processa transferência de contexto"""
        context_data = request.data_payload.get('project_context', {})
        
        logger.info(f"Executor {self.agent_id}: Recebendo contexto do projeto {context_data.get('project_id')}")
        
        # Simular processamento do contexto
        await asyncio.sleep(0.3)
        
        self.project_context = context_data
        logger.info(f"Executor {self.agent_id}: Contexto integrado com sucesso")
    
    async def execute_next_task(self):
        """Executa próxima tarefa da fila"""
        if self.execution_queue:
            task = self.execution_queue.pop(0)
            
            logger.info(f"Executor {self.agent_id}: Executando tarefa {task['task_id']}")
            
            # Simular execução
            await asyncio.sleep(1.0)
            
            # Marcar como completada
            task['completed_at'] = datetime.utcnow()
            task['status'] = 'completed'
            self.completed_tasks.append(task)
            
            logger.info(f"Executor {self.agent_id}: Tarefa {task['task_id']} concluída")
            return task
        
        return None


class DemoValidatorAgent(A2ACapableMixin):
    """Agente validador de demonstração com capacidades A2A"""
    
    def __init__(self, agent_id: str):
        super().__init__()
        self.agent_id = agent_id
        self.validation_results = []
        
        # Registrar no coordenador
        coordinator = get_handoff_coordinator()
        coordinator.register_agent(
            agent_id, 
            self, 
            ["handle_knowledge_share", "handle_state_sync"]
        )
        
        logger.info(f"DemoValidatorAgent {agent_id} inicializado")
    
    async def _process_received_handoff(self, request):
        """Processa handoff recebido"""
        if request.handoff_type == HandoffType.KNOWLEDGE_SHARE:
            await self._handle_knowledge_share_demo(request)
        elif request.handoff_type == HandoffType.STATE_SYNC:
            await self._handle_state_sync_demo(request)
    
    async def _handle_knowledge_share_demo(self, request):
        """Processa compartilhamento de conhecimento"""
        knowledge_data = request.data_payload.get('knowledge', {})
        knowledge_type = request.data_payload.get('knowledge_type', 'general')
        
        logger.info(f"Validator {self.agent_id}: Recebendo conhecimento '{knowledge_type}'")
        
        # Simular processamento do conhecimento
        await asyncio.sleep(0.4)
        
        # Armazenar conhecimento
        if not hasattr(self, 'shared_knowledge'):
            self.shared_knowledge = {}
        
        self.shared_knowledge[knowledge_type] = {
            'data': knowledge_data,
            'source': request.sender_agent_id,
            'received_at': datetime.utcnow()
        }
        
        logger.info(f"Validator {self.agent_id}: Conhecimento '{knowledge_type}' integrado")
    
    async def _handle_state_sync_demo(self, request):
        """Processa sincronização de estado"""
        state_data = request.data_payload.get('state', {})
        
        logger.info(f"Validator {self.agent_id}: Sincronizando estado")
        
        # Simular sincronização
        await asyncio.sleep(0.2)
        
        self.synced_state = {
            'data': state_data,
            'synced_with': request.sender_agent_id,
            'synced_at': datetime.utcnow()
        }
        
        logger.info(f"Validator {self.agent_id}: Estado sincronizado com {request.sender_agent_id}")


async def demo_task_delegation():
    """Demonstra delegação de tarefa entre agentes"""
    print("\n" + "="*60)
    print("🔄 DEMO: Delegação de Tarefa A2A")
    print("="*60)
    
    # Criar agentes
    planner = DemoExecutorAgent("demo_planner")
    executor = DemoExecutorAgent("demo_executor")
    
    # Obter integração A2A
    a2a_integration = EvoluxA2AIntegration()
    
    # Criar tarefa para delegação
    demo_task = Task(
        task_id="demo_task_001",
        description="Criar arquivo de configuração de demonstração",
        type=TaskType.CREATE_FILE,
        status=TaskStatus.PENDING,
        details=None,
        dependencies=[],
        acceptance_criteria="Arquivo de configuração criado com sucesso"
    )
    
    # Executar delegação
    print(f"📤 Delegando tarefa {demo_task.task_id} do planner para executor...")
    
    response = await a2a_integration.delegate_task(
        sender_agent_id="demo_planner",
        receiver_agent_id="demo_executor",
        task=demo_task,
        execution_context={"priority": "high", "timeout": 300},
        priority=7
    )
    
    print(f"✅ Delegação concluída: Status = {response.status.value}")
    
    # Executor processa a tarefa
    print("⚙️ Executor processando tarefa...")
    completed_task = await executor.execute_next_task()
    
    if completed_task:
        print(f"🎉 Tarefa {completed_task['task_id']} executada com sucesso!")
    
    return response


async def demo_context_transfer():
    """Demonstra transferência de contexto entre agentes"""
    print("\n" + "="*60)
    print("📋 DEMO: Transferência de Contexto A2A")
    print("="*60)
    
    # Criar agentes
    orchestrator = DemoExecutorAgent("demo_orchestrator")
    planner = DemoExecutorAgent("demo_planner_2")
    
    # Obter integração A2A
    a2a_integration = EvoluxA2AIntegration()
    
    # Criar contexto de projeto mock
    from pathlib import Path
    mock_project_context = ProjectContext(
        project_id="demo_project_123",
        project_name="Demo A2A Project",
        project_goal="Demonstrar transferência de contexto A2A",
        workspace_path=Path("/tmp/demo_workspace")
    )
    
    # Executar transferência de contexto
    print(f"📤 Transferindo contexto do projeto {mock_project_context.project_id}...")
    
    response = await a2a_integration.transfer_project_context(
        sender_agent_id="demo_orchestrator",
        receiver_agent_id="demo_planner_2",
        project_context=mock_project_context,
        include_task_queue=True,
        include_execution_history=False
    )
    
    print(f"✅ Transferência concluída: Status = {response.status.value}")
    
    # Verificar se contexto foi recebido
    if hasattr(planner, 'project_context') and planner.project_context:
        print(f"🎯 Contexto recebido: Projeto {planner.project_context.get('project_id')}")
    
    return response


async def demo_knowledge_sharing():
    """Demonstra compartilhamento de conhecimento entre múltiplos agentes"""
    print("\n" + "="*60)
    print("🧠 DEMO: Compartilhamento de Conhecimento A2A")
    print("="*60)
    
    # Criar agentes
    expert_agent = DemoValidatorAgent("demo_expert")
    learner1 = DemoValidatorAgent("demo_learner_1")
    learner2 = DemoValidatorAgent("demo_learner_2")
    
    # Obter integração A2A
    a2a_integration = EvoluxA2AIntegration()
    
    # Preparar conhecimento para compartilhar
    expert_knowledge = {
        'best_practices': [
            'Sempre validar entrada de dados',
            'Implementar logging estruturado',
            'Usar tratamento de exceções adequado'
        ],
        'common_patterns': {
            'validation': 'pydantic_schemas',
            'logging': 'structured_json',
            'error_handling': 'custom_exceptions'
        },
        'performance_tips': [
            'Usar async/await para I/O bound operations',
            'Implementar caching quando apropriado',
            'Monitorar métricas de performance'
        ]
    }
    
    # Executar compartilhamento
    print("📤 Compartilhando conhecimento do expert para 2 agentes...")
    
    responses = await a2a_integration.share_knowledge(
        sender_agent_id="demo_expert",
        receiver_agents=["demo_learner_1", "demo_learner_2"],
        knowledge_data=expert_knowledge,
        knowledge_type="best_practices"
    )
    
    # Verificar resultados
    successful_shares = sum(1 for r in responses if hasattr(r, 'status') and r.status.value == "completed")
    print(f"✅ Conhecimento compartilhado com sucesso: {successful_shares}/2 agentes")
    
    # Verificar se conhecimento foi recebido
    for learner, name in [(learner1, "learner_1"), (learner2, "learner_2")]:
        if hasattr(learner, 'shared_knowledge') and 'best_practices' in learner.shared_knowledge:
            print(f"🎓 {name} recebeu conhecimento de {learner.shared_knowledge['best_practices']['source']}")
    
    return responses


async def demo_state_synchronization():
    """Demonstra sincronização de estado entre agentes"""
    print("\n" + "="*60)
    print("🔄 DEMO: Sincronização de Estado A2A")
    print("="*60)
    
    # Criar agentes
    agent1 = DemoValidatorAgent("demo_sync_agent_1")
    agent2 = DemoValidatorAgent("demo_sync_agent_2")
    
    # Obter integração A2A
    a2a_integration = EvoluxA2AIntegration()
    
    # Preparar dados de estado
    shared_state = {
        'execution_metrics': {
            'total_tasks': 45,
            'completed_tasks': 42,
            'failed_tasks': 3,
            'success_rate': 0.93
        },
        'resource_usage': {
            'cpu_percent': 15.5,
            'memory_mb': 256,
            'disk_io': 'low'
        },
        'last_update': datetime.utcnow().isoformat()
    }
    
    # Executar sincronização
    print("🔄 Sincronizando estado entre 2 agentes...")
    
    responses = await a2a_integration.sync_agent_state(
        agent1_id="demo_sync_agent_1",
        agent2_id="demo_sync_agent_2",
        state_data=shared_state
    )
    
    # Verificar resultados
    successful_syncs = sum(1 for r in responses if hasattr(r, 'status') and r.status.value == "completed")
    print(f"✅ Sincronização concluída: {successful_syncs}/2 handoffs bem-sucedidos")
    
    # Verificar estado sincronizado
    for agent, name in [(agent1, "agent_1"), (agent2, "agent_2")]:
        if hasattr(agent, 'synced_state'):
            sync_time = agent.synced_state['synced_at'].strftime('%H:%M:%S')
            print(f"🎯 {name} sincronizado às {sync_time}")
    
    return responses


async def demo_system_metrics():
    """Demonstra métricas do sistema A2A"""
    print("\n" + "="*60)
    print("📊 DEMO: Métricas do Sistema A2A")
    print("="*60)
    
    coordinator = get_handoff_coordinator()
    metrics = await coordinator.get_system_metrics()
    
    print("📈 Métricas Gerais:")
    print(f"   • Total de handoffs: {metrics['total_handoffs']}")
    print(f"   • Handoffs ativos: {metrics['active_handoffs']}")
    print(f"   • Agentes registrados: {metrics['registered_agents']}")
    print(f"   • Duração média: {metrics['average_duration_ms']:.1f}ms")
    print(f"   • Taxa de sucesso: {metrics['success_rate']:.1%}")
    
    if metrics['validation_rules']:
        print("\n🔍 Regras de Validação:")
        for rule_type, count in metrics['validation_rules'].items():
            print(f"   • {rule_type}: {count} regras")
    
    return metrics


async def main():
    """Executa todas as demonstrações A2A"""
    print("🚀 INICIANDO DEMONSTRAÇÃO DO SISTEMA PARALLEL HANDOFF A2A")
    print("=" * 80)
    
    try:
        # Executar todas as demonstrações
        await demo_task_delegation()
        await demo_context_transfer()
        await demo_knowledge_sharing()
        await demo_state_synchronization()
        await demo_system_metrics()
        
        print("\n" + "="*80)
        print("🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("O sistema Parallel Handoff A2A está funcionando perfeitamente.")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRO na demonstração: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())