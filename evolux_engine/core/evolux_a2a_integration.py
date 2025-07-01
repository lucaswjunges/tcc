#!/usr/bin/env python3
"""
Integração do Sistema A2A com Agentes do Evolux
==============================================

Implementa a integração do sistema Parallel Handoff A2A com os agentes
existentes do Evolux (Planner, Executor, Validator, Orchestrator).

Funcionalidades:
- Adaptadores para agentes existentes
- Handoffs específicos do domínio Evolux
- Coordenação de tarefas entre agentes
- Transferência de contexto de projeto
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from evolux_engine.core.agent_handoff import (
    AgentHandoffCoordinator, HandoffRequest, HandoffResponse, 
    HandoffType, HandoffStatus, get_handoff_coordinator,
    auto_register_agent, handoff_capable
)
from evolux_engine.schemas.contracts import Task, ProjectContext, ExecutionResult, ValidationResult
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("evolux_a2a")


@dataclass
class EvoluxHandoffContext:
    """Contexto específico para handoffs no Evolux"""
    project_context: Optional[ProjectContext] = None
    current_task: Optional[Task] = None
    execution_results: List[ExecutionResult] = None
    validation_results: List[ValidationResult] = None
    agent_state: Dict[str, Any] = None
    shared_knowledge: Dict[str, Any] = None


class EvoluxA2AIntegration:
    """
    Integração principal do sistema A2A com o Evolux
    """
    
    def __init__(self):
        self.coordinator = get_handoff_coordinator()
        self.setup_validation_rules()
        self.setup_evolux_handoff_types()
        logger.info("EvoluxA2AIntegration inicializada")
    
    def setup_validation_rules(self):
        """Configura regras de validação específicas do Evolux"""
        
        # Validação para transferência de contexto
        async def validate_context_transfer(request: HandoffRequest) -> Dict[str, Any]:
            payload = request.data_payload
            errors = []
            warnings = []
            
            if 'project_context' not in payload:
                errors.append("project_context é obrigatório para transferência de contexto")
            
            if 'current_task' in payload:
                task = payload['current_task']
                if not isinstance(task, dict) or 'task_id' not in task:
                    warnings.append("current_task tem formato inválido")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        
        # Validação para delegação de tarefa
        async def validate_task_delegation(request: HandoffRequest) -> Dict[str, Any]:
            payload = request.data_payload
            errors = []
            
            if 'task' not in payload:
                errors.append("task é obrigatório para delegação")
            
            if 'execution_context' not in payload:
                warnings = ["execution_context recomendado para melhor delegação"]
            else:
                warnings = []
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        
        # Registrar validações
        self.coordinator.add_validation_rule(HandoffType.CONTEXT_TRANSFER, validate_context_transfer)
        self.coordinator.add_validation_rule(HandoffType.TASK_DELEGATION, validate_task_delegation)
    
    def setup_evolux_handoff_types(self):
        """Define tipos de handoff específicos do Evolux"""
        # Os tipos base já estão definidos no enum, mas podemos adicionar lógica específica
        pass
    
    async def transfer_project_context(self, 
                                     sender_agent_id: str, 
                                     receiver_agent_id: str,
                                     project_context: ProjectContext,
                                     include_task_queue: bool = True,
                                     include_execution_history: bool = False) -> HandoffResponse:
        """Transfere contexto de projeto entre agentes"""
        
        # Preparar payload
        payload = {
            "project_context": {
                "project_id": project_context.project_id,
                "project_name": project_context.project_name,
                "project_goal": project_context.project_goal,
                "workspace_path": str(getattr(project_context, 'workspace_path', '/tmp/default')),
                "current_phase": getattr(project_context, 'current_phase', 'active')
            }
        }
        
        if include_task_queue:
            payload["task_queue"] = [task.__dict__ for task in project_context.task_queue]
        
        if include_execution_history:
            payload["execution_history"] = [result.__dict__ for result in project_context.execution_history]
        
        # Criar request
        request = HandoffRequest(
            handoff_id=f"ctx_transfer_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            handoff_type=HandoffType.CONTEXT_TRANSFER,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            data_payload=payload,
            metadata={
                "project_id": project_context.project_id,
                "transfer_type": "project_context",
                "include_task_queue": include_task_queue,
                "include_execution_history": include_execution_history
            }
        )
        
        logger.info(f"Transferindo contexto do projeto {project_context.project_id} de {sender_agent_id} para {receiver_agent_id}")
        return await self.coordinator.initiate_handoff(request)
    
    async def delegate_task(self,
                          sender_agent_id: str,
                          receiver_agent_id: str,
                          task: Task,
                          execution_context: Dict[str, Any] = None,
                          priority: int = 5) -> HandoffResponse:
        """Delega uma tarefa específica para outro agente"""
        
        payload = {
            "task": {
                "task_id": task.task_id,
                "description": task.description,
                "type": task.type.value,
                "status": task.status.value,
                "details": task.details.__dict__ if task.details else None,
                "dependencies": task.dependencies,
                "acceptance_criteria": task.acceptance_criteria
            }
        }
        
        if execution_context:
            payload["execution_context"] = execution_context
        
        request = HandoffRequest(
            handoff_id=f"task_delegation_{task.task_id}_{datetime.utcnow().strftime('%H%M%S')}",
            handoff_type=HandoffType.TASK_DELEGATION,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            data_payload=payload,
            priority=priority,
            metadata={
                "task_id": task.task_id,
                "task_type": task.type.value,
                "delegation_reason": "workload_distribution"
            }
        )
        
        logger.info(f"Delegando tarefa {task.task_id} de {sender_agent_id} para {receiver_agent_id}")
        return await self.coordinator.initiate_handoff(request)
    
    async def sync_agent_state(self,
                             agent1_id: str,
                             agent2_id: str,
                             state_data: Dict[str, Any]) -> List[HandoffResponse]:
        """Sincroniza estado entre dois agentes"""
        
        # Criar requests bidirecionais
        requests = [
            HandoffRequest(
                handoff_id=f"state_sync_{agent1_id}_{agent2_id}_{datetime.utcnow().strftime('%H%M%S')}",
                handoff_type=HandoffType.STATE_SYNC,
                sender_agent_id=agent1_id,
                receiver_agent_id=agent2_id,
                data_payload={"state": state_data, "sync_direction": "1_to_2"},
                requires_acknowledgment=True
            ),
            HandoffRequest(
                handoff_id=f"state_sync_{agent2_id}_{agent1_id}_{datetime.utcnow().strftime('%H%M%S')}",
                handoff_type=HandoffType.STATE_SYNC,
                sender_agent_id=agent2_id,
                receiver_agent_id=agent1_id,
                data_payload={"state": state_data, "sync_direction": "2_to_1"},
                requires_acknowledgment=True
            )
        ]
        
        # Executar sincronização paralela
        logger.info(f"Sincronizando estado entre {agent1_id} e {agent2_id}")
        responses = await asyncio.gather(
            *[self.coordinator.initiate_handoff(req) for req in requests],
            return_exceptions=True
        )
        
        return responses
    
    async def share_knowledge(self,
                            sender_agent_id: str,
                            receiver_agents: List[str],
                            knowledge_data: Dict[str, Any],
                            knowledge_type: str = "general") -> List[HandoffResponse]:
        """Compartilha conhecimento com múltiplos agentes"""
        
        requests = []
        for receiver_id in receiver_agents:
            request = HandoffRequest(
                handoff_id=f"knowledge_share_{sender_agent_id}_{receiver_id}_{datetime.utcnow().strftime('%H%M%S')}",
                handoff_type=HandoffType.KNOWLEDGE_SHARE,
                sender_agent_id=sender_agent_id,
                receiver_agent_id=receiver_id,
                data_payload={
                    "knowledge": knowledge_data,
                    "knowledge_type": knowledge_type,
                    "source_agent": sender_agent_id
                },
                metadata={
                    "knowledge_type": knowledge_type,
                    "broadcast": True,
                    "recipients_count": len(receiver_agents)
                }
            )
            requests.append(request)
        
        logger.info(f"Compartilhando conhecimento '{knowledge_type}' de {sender_agent_id} para {len(receiver_agents)} agentes")
        responses = await asyncio.gather(
            *[self.coordinator.initiate_handoff(req) for req in requests],
            return_exceptions=True
        )
        
        return responses
    
    async def setup_collaborative_work(self,
                                     agents: List[str],
                                     work_context: Dict[str, Any],
                                     coordination_agent: str = None) -> List[HandoffResponse]:
        """Configura trabalho colaborativo entre múltiplos agentes"""
        
        if not coordination_agent:
            coordination_agent = agents[0]  # Primeiro agente como coordenador
        
        requests = []
        for agent_id in agents:
            if agent_id != coordination_agent:
                request = HandoffRequest(
                    handoff_id=f"collab_setup_{coordination_agent}_{agent_id}_{datetime.utcnow().strftime('%H%M%S')}",
                    handoff_type=HandoffType.COLLABORATIVE_WORK,
                    sender_agent_id=coordination_agent,
                    receiver_agent_id=agent_id,
                    data_payload={
                        "work_context": work_context,
                        "collaboration_role": "participant",
                        "coordinator": coordination_agent,
                        "all_participants": agents
                    },
                    metadata={
                        "collaboration_type": "multi_agent",
                        "participants_count": len(agents),
                        "coordinator": coordination_agent
                    }
                )
                requests.append(request)
        
        logger.info(f"Configurando trabalho colaborativo com {len(agents)} agentes, coordenador: {coordination_agent}")
        responses = await asyncio.gather(
            *[self.coordinator.initiate_handoff(req) for req in requests],
            return_exceptions=True
        )
        
        return responses


# Mixins para adicionar capacidades A2A aos agentes existentes
class A2ACapableMixin:
    """Mixin para adicionar capacidades A2A a agentes existentes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a2a_integration = EvoluxA2AIntegration()
        self.handoff_state = {}
        self.received_handoffs = {}
    
    async def prepare_handoff(self, request: HandoffRequest) -> Dict[str, Any]:
        """Prepara o agente para enviar handoff"""
        logger.info(f"Agente {self.__class__.__name__} preparando handoff {request.handoff_id}")
        
        # Salvar estado atual para possível rollback
        self.handoff_state[request.handoff_id] = {
            "timestamp": datetime.utcnow(),
            "agent_state": getattr(self, '__dict__', {}),
            "request": request
        }
        
        return {"status": "prepared", "agent_type": self.__class__.__name__}
    
    async def prepare_receive_handoff(self, request: HandoffRequest) -> Dict[str, Any]:
        """Prepara o agente para receber handoff"""
        logger.info(f"Agente {self.__class__.__name__} preparando para receber handoff {request.handoff_id}")
        
        # Verificar se pode processar este tipo de handoff
        can_handle = self._can_handle_handoff_type(request.handoff_type)
        
        return {
            "status": "ready" if can_handle else "not_ready",
            "can_handle": can_handle,
            "agent_type": self.__class__.__name__
        }
    
    async def send_handoff_data(self, request: HandoffRequest) -> Dict[str, Any]:
        """Envia dados do handoff"""
        logger.info(f"Agente {self.__class__.__name__} enviando dados do handoff {request.handoff_id}")
        
        # Implementação específica pode ser sobrescrita
        return {
            "data_sent": True,
            "payload_size": len(json.dumps(request.data_payload, default=str)),
            "sender": self.__class__.__name__
        }
    
    async def receive_handoff_data(self, request: HandoffRequest) -> Dict[str, Any]:
        """Recebe dados do handoff"""
        logger.info(f"Agente {self.__class__.__name__} recebendo dados do handoff {request.handoff_id}")
        
        # Armazenar dados recebidos
        self.received_handoffs[request.handoff_id] = {
            "data": request.data_payload,
            "metadata": request.metadata,
            "received_at": datetime.utcnow(),
            "sender": request.sender_agent_id
        }
        
        # Processar handoff baseado no tipo
        await self._process_received_handoff(request)
        
        return {
            "data_received": True,
            "handoff_id": request.handoff_id,
            "receiver": self.__class__.__name__
        }
    
    async def acknowledge_handoff(self, request: HandoffRequest, transfer_result: Dict[str, Any]) -> Dict[str, Any]:
        """Confirma recebimento e processamento do handoff"""
        logger.info(f"Agente {self.__class__.__name__} confirmando handoff {request.handoff_id}")
        
        # Validar se dados foram processados corretamente
        validation_result = await self._validate_received_data(request)
        
        return {
            "acknowledged": validation_result["valid"],
            "validation": validation_result,
            "processing_status": "completed" if validation_result["valid"] else "failed",
            "receiver": self.__class__.__name__
        }
    
    async def rollback_handoff(self, request: HandoffRequest):
        """Executa rollback do handoff"""
        logger.warning(f"Agente {self.__class__.__name__} executando rollback do handoff {request.handoff_id}")
        
        # Restaurar estado anterior se disponível
        if request.handoff_id in self.handoff_state:
            saved_state = self.handoff_state[request.handoff_id]
            # Implementação específica de rollback pode ser sobrescrita
            logger.info(f"Rollback executado para handoff {request.handoff_id}")
            del self.handoff_state[request.handoff_id]
        
        # Remover dados recebidos se existirem
        if request.handoff_id in self.received_handoffs:
            del self.received_handoffs[request.handoff_id]
    
    def _can_handle_handoff_type(self, handoff_type: HandoffType) -> bool:
        """Verifica se o agente pode processar este tipo de handoff"""
        # Implementação base - pode ser sobrescrita
        capabilities = getattr(self, '_handoff_capabilities', ['all'])
        return 'all' in capabilities or f'handle_{handoff_type.value}' in capabilities
    
    async def _process_received_handoff(self, request: HandoffRequest):
        """Processa handoff recebido - implementação específica por agente"""
        # Implementação base - deve ser sobrescrita pelos agentes específicos
        pass
    
    async def _validate_received_data(self, request: HandoffRequest) -> Dict[str, Any]:
        """Valida dados recebidos - implementação específica por agente"""
        # Implementação base
        return {"valid": True, "errors": [], "warnings": []}


# Singleton da integração
_evolux_a2a_integration = None

def get_evolux_a2a_integration() -> EvoluxA2AIntegration:
    """Obtém instância singleton da integração A2A do Evolux"""
    global _evolux_a2a_integration
    if _evolux_a2a_integration is None:
        _evolux_a2a_integration = EvoluxA2AIntegration()
    return _evolux_a2a_integration