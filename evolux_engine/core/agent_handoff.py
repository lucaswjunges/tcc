#!/usr/bin/env python3
"""
Sistema de Parallel Handoff Agent-to-Agent (A2A)
==============================================

Implementa transferência paralela e coordenada de controle, estado ou dados
entre agentes, permitindo colaboração em tempo real com rastreabilidade completa.

Funcionalidades:
- Handoff paralelo de contexto entre agentes
- Coordenação de estado sincronizada
- Auditoria completa de transferências
- Rollback seguro em caso de falhas
- Validação de integridade de dados
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import logging

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import Task, ProjectContext

logger = get_structured_logger("agent_handoff")


class HandoffType(Enum):
    """Tipos de handoff entre agentes"""
    CONTEXT_TRANSFER = "context_transfer"      # Transferência de contexto de projeto
    TASK_DELEGATION = "task_delegation"        # Delegação de tarefa específica
    STATE_SYNC = "state_sync"                  # Sincronização de estado
    KNOWLEDGE_SHARE = "knowledge_share"        # Compartilhamento de conhecimento
    COLLABORATIVE_WORK = "collaborative_work"  # Trabalho colaborativo paralelo


class HandoffStatus(Enum):
    """Status do handoff"""
    INITIATED = "initiated"           # Handoff iniciado
    COORDINATING = "coordinating"     # Coordenando entre agentes
    TRANSFERRING = "transferring"     # Transferindo dados/estado
    VALIDATING = "validating"         # Validando integridade
    COMPLETED = "completed"           # Handoff completado
    FAILED = "failed"                 # Handoff falhou
    ROLLED_BACK = "rolled_back"       # Rollback executado


class AgentRole(Enum):
    """Papéis dos agentes no handoff"""
    SENDER = "sender"                 # Agente que envia
    RECEIVER = "receiver"             # Agente que recebe
    COORDINATOR = "coordinator"       # Agente coordenador
    VALIDATOR = "validator"           # Agente validador


@dataclass
class HandoffMetadata:
    """Metadados do handoff para auditoria"""
    handoff_id: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    data_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    agent_versions: Dict[str, str] = field(default_factory=dict)
    context_snapshot: Optional[str] = None


@dataclass
class HandoffRequest:
    """Solicitação de handoff entre agentes"""
    handoff_id: str
    handoff_type: HandoffType
    sender_agent_id: str
    receiver_agent_id: str
    data_payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, onde 10 é mais prioritário
    timeout_seconds: int = 300
    requires_acknowledgment: bool = True
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class HandoffResponse:
    """Resposta de handoff"""
    handoff_id: str
    status: HandoffStatus
    receiver_agent_id: str
    acknowledgment_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: int = 0
    validation_results: Dict[str, Any] = field(default_factory=dict)


class AgentHandoffCoordinator:
    """
    Coordenador central para handoffs entre agentes
    """
    
    def __init__(self):
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.handoff_history: List[HandoffMetadata] = []
        self.agent_registry: Dict[str, Any] = {}
        self.coordination_lock = asyncio.Lock()
        self.validation_rules: Dict[HandoffType, List[Callable]] = {}
        self.rollback_handlers: Dict[str, Callable] = {}
        
        logger.info("AgentHandoffCoordinator inicializado")
    
    def register_agent(self, agent_id: str, agent_instance: Any, capabilities: List[str] = None):
        """Registra um agente no sistema de handoff"""
        self.agent_registry[agent_id] = {
            "instance": agent_instance,
            "capabilities": capabilities or [],
            "registered_at": datetime.utcnow(),
            "active_handoffs": []
        }
        logger.info(f"Agente {agent_id} registrado com capacidades: {capabilities}")
    
    def add_validation_rule(self, handoff_type: HandoffType, validator_func: Callable):
        """Adiciona regra de validação para tipo de handoff"""
        if handoff_type not in self.validation_rules:
            self.validation_rules[handoff_type] = []
        self.validation_rules[handoff_type].append(validator_func)
        logger.info(f"Regra de validação adicionada para {handoff_type.value}")
    
    async def initiate_handoff(self, request: HandoffRequest) -> HandoffResponse:
        """Inicia um handoff entre agentes"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Iniciando handoff {request.handoff_id}: {request.sender_agent_id} -> {request.receiver_agent_id}")
            
            # Validar agentes
            if not await self._validate_agents(request):
                return HandoffResponse(
                    handoff_id=request.handoff_id,
                    status=HandoffStatus.FAILED,
                    receiver_agent_id=request.receiver_agent_id,
                    error_message="Validação de agentes falhou"
                )
            
            # Executar handoff coordenado
            async with self.coordination_lock:
                self.active_handoffs[request.handoff_id] = request
                
                response = await self._execute_parallel_handoff(request)
                
                # Registrar na auditoria
                metadata = HandoffMetadata(
                    handoff_id=request.handoff_id,
                    timestamp=start_time,
                    duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    data_size_bytes=len(json.dumps(request.data_payload, default=str)),
                    agent_versions={
                        request.sender_agent_id: "1.0",
                        request.receiver_agent_id: "1.0"
                    }
                )
                self.handoff_history.append(metadata)
                
                # Remover do active_handoffs se completado
                if response.status in [HandoffStatus.COMPLETED, HandoffStatus.FAILED, HandoffStatus.ROLLED_BACK]:
                    self.active_handoffs.pop(request.handoff_id, None)
                
                return response
                
        except Exception as e:
            logger.error(f"Erro no handoff {request.handoff_id}: {e}")
            return HandoffResponse(
                handoff_id=request.handoff_id,
                status=HandoffStatus.FAILED,
                receiver_agent_id=request.receiver_agent_id,
                error_message=str(e)
            )
    
    async def _validate_agents(self, request: HandoffRequest) -> bool:
        """Valida se os agentes estão disponíveis e compatíveis"""
        sender_available = request.sender_agent_id in self.agent_registry
        receiver_available = request.receiver_agent_id in self.agent_registry
        
        if not sender_available:
            logger.error(f"Agente sender {request.sender_agent_id} não encontrado")
            return False
            
        if not receiver_available:
            logger.error(f"Agente receiver {request.receiver_agent_id} não encontrado")
            return False
        
        # Verificar capacidades específicas se necessário
        receiver_capabilities = self.agent_registry[request.receiver_agent_id]["capabilities"]
        required_capability = f"handle_{request.handoff_type.value}"
        
        if required_capability not in receiver_capabilities and "all" not in receiver_capabilities:
            logger.warning(f"Agente {request.receiver_agent_id} não tem capacidade {required_capability}")
        
        return True
    
    async def _execute_parallel_handoff(self, request: HandoffRequest) -> HandoffResponse:
        """Executa o handoff paralelo coordenado"""
        try:
            # Fase 1: Preparação paralela
            logger.info(f"Handoff {request.handoff_id}: Fase de preparação")
            preparation_tasks = [
                self._prepare_sender(request),
                self._prepare_receiver(request)
            ]
            prep_results = await asyncio.gather(*preparation_tasks, return_exceptions=True)
            
            # Verificar se preparação foi bem-sucedida
            for result in prep_results:
                if isinstance(result, Exception):
                    raise result
            
            # Fase 2: Validação de dados
            logger.info(f"Handoff {request.handoff_id}: Fase de validação")
            validation_result = await self._validate_handoff_data(request)
            if not validation_result["valid"]:
                raise ValueError(f"Validação falhou: {validation_result['errors']}")
            
            # Fase 3: Transferência coordenada
            logger.info(f"Handoff {request.handoff_id}: Fase de transferência")
            transfer_result = await self._execute_coordinated_transfer(request)
            
            # Fase 4: Confirmação e finalização
            logger.info(f"Handoff {request.handoff_id}: Fase de confirmação")
            if request.requires_acknowledgment:
                ack_result = await self._get_acknowledgment(request, transfer_result)
                if not ack_result["acknowledged"]:
                    # Rollback se necessário
                    await self._execute_rollback(request)
                    return HandoffResponse(
                        handoff_id=request.handoff_id,
                        status=HandoffStatus.ROLLED_BACK,
                        receiver_agent_id=request.receiver_agent_id,
                        error_message="Acknowledgment falhou"
                    )
            
            logger.info(f"Handoff {request.handoff_id} completado com sucesso")
            return HandoffResponse(
                handoff_id=request.handoff_id,
                status=HandoffStatus.COMPLETED,
                receiver_agent_id=request.receiver_agent_id,
                acknowledgment_data=transfer_result,
                validation_results=validation_result
            )
            
        except Exception as e:
            logger.error(f"Erro na execução do handoff {request.handoff_id}: {e}")
            await self._execute_rollback(request)
            return HandoffResponse(
                handoff_id=request.handoff_id,
                status=HandoffStatus.FAILED,
                receiver_agent_id=request.receiver_agent_id,
                error_message=str(e)
            )
    
    async def _prepare_sender(self, request: HandoffRequest) -> Dict[str, Any]:
        """Prepara o agente sender para o handoff"""
        sender = self.agent_registry[request.sender_agent_id]["instance"]
        
        if hasattr(sender, 'prepare_handoff'):
            return await sender.prepare_handoff(request)
        
        return {"status": "ready", "preparation_time": datetime.utcnow()}
    
    async def _prepare_receiver(self, request: HandoffRequest) -> Dict[str, Any]:
        """Prepara o agente receiver para o handoff"""
        receiver = self.agent_registry[request.receiver_agent_id]["instance"]
        
        if hasattr(receiver, 'prepare_receive_handoff'):
            return await receiver.prepare_receive_handoff(request)
        
        return {"status": "ready", "preparation_time": datetime.utcnow()}
    
    async def _validate_handoff_data(self, request: HandoffRequest) -> Dict[str, Any]:
        """Valida os dados do handoff"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Executar regras de validação específicas do tipo
        if request.handoff_type in self.validation_rules:
            for validator in self.validation_rules[request.handoff_type]:
                try:
                    result = await validator(request) if asyncio.iscoroutinefunction(validator) else validator(request)
                    if not result.get("valid", True):
                        validation_results["valid"] = False
                        validation_results["errors"].extend(result.get("errors", []))
                    validation_results["warnings"].extend(result.get("warnings", []))
                except Exception as e:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Erro na validação: {e}")
        
        # Validações básicas
        if not request.data_payload:
            validation_results["warnings"].append("Payload de dados vazio")
        
        return validation_results
    
    async def _execute_coordinated_transfer(self, request: HandoffRequest) -> Dict[str, Any]:
        """Executa a transferência coordenada entre agentes"""
        sender = self.agent_registry[request.sender_agent_id]["instance"]
        receiver = self.agent_registry[request.receiver_agent_id]["instance"]
        
        transfer_tasks = []
        
        # Sender: envia dados
        if hasattr(sender, 'send_handoff_data'):
            transfer_tasks.append(sender.send_handoff_data(request))
        
        # Receiver: recebe dados
        if hasattr(receiver, 'receive_handoff_data'):
            transfer_tasks.append(receiver.receive_handoff_data(request))
        
        # Execução paralela coordenada
        if transfer_tasks:
            results = await asyncio.gather(*transfer_tasks, return_exceptions=True)
            
            # Verificar resultados
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise result
            
            return {"transfer_results": results, "status": "completed"}
        
        # Fallback: transferência básica
        return {
            "data_transferred": request.data_payload,
            "status": "completed",
            "method": "basic_transfer"
        }
    
    async def _get_acknowledgment(self, request: HandoffRequest, transfer_result: Dict[str, Any]) -> Dict[str, Any]:
        """Obtém confirmação do agente receiver"""
        receiver = self.agent_registry[request.receiver_agent_id]["instance"]
        
        if hasattr(receiver, 'acknowledge_handoff'):
            try:
                ack_result = await receiver.acknowledge_handoff(request, transfer_result)
                return {"acknowledged": True, "details": ack_result}
            except Exception as e:
                logger.error(f"Erro na confirmação: {e}")
                return {"acknowledged": False, "error": str(e)}
        
        # Acknowledgment automático se método não implementado
        return {"acknowledged": True, "method": "automatic"}
    
    async def _execute_rollback(self, request: HandoffRequest):
        """Executa rollback em caso de falha"""
        try:
            logger.warning(f"Executando rollback para handoff {request.handoff_id}")
            
            # Rollback no sender
            sender = self.agent_registry[request.sender_agent_id]["instance"]
            if hasattr(sender, 'rollback_handoff'):
                await sender.rollback_handoff(request)
            
            # Rollback no receiver
            receiver = self.agent_registry[request.receiver_agent_id]["instance"]
            if hasattr(receiver, 'rollback_handoff'):
                await receiver.rollback_handoff(request)
            
            logger.info(f"Rollback completado para handoff {request.handoff_id}")
            
        except Exception as e:
            logger.error(f"Erro no rollback: {e}")
    
    def get_handoff_status(self, handoff_id: str) -> Optional[HandoffStatus]:
        """Obtém status de um handoff"""
        if handoff_id in self.active_handoffs:
            return HandoffStatus.TRANSFERRING
        
        # Buscar no histórico
        for metadata in self.handoff_history:
            if metadata.handoff_id == handoff_id:
                return HandoffStatus.COMPLETED
        
        return None
    
    def get_agent_handoff_history(self, agent_id: str) -> List[HandoffMetadata]:
        """Obtém histórico de handoffs de um agente"""
        return [
            metadata for metadata in self.handoff_history
            if agent_id in metadata.agent_versions
        ]
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema de handoff"""
        total_handoffs = len(self.handoff_history)
        active_handoffs = len(self.active_handoffs)
        
        if total_handoffs > 0:
            avg_duration = sum(h.duration_ms or 0 for h in self.handoff_history) / total_handoffs
            success_rate = len([h for h in self.handoff_history if h.duration_ms is not None]) / total_handoffs
        else:
            avg_duration = 0
            success_rate = 0
        
        return {
            "total_handoffs": total_handoffs,
            "active_handoffs": active_handoffs,
            "registered_agents": len(self.agent_registry),
            "average_duration_ms": avg_duration,
            "success_rate": success_rate,
            "validation_rules": {ht.value: len(rules) for ht, rules in self.validation_rules.items()}
        }


# Singleton global do coordenador
_handoff_coordinator = None

def get_handoff_coordinator() -> AgentHandoffCoordinator:
    """Obtém instância singleton do coordenador de handoff"""
    global _handoff_coordinator
    if _handoff_coordinator is None:
        _handoff_coordinator = AgentHandoffCoordinator()
    return _handoff_coordinator


@asynccontextmanager
async def handoff_session(sender_id: str, receiver_id: str, handoff_type: HandoffType):
    """Context manager para sessão de handoff"""
    coordinator = get_handoff_coordinator()
    handoff_id = str(uuid.uuid4())
    
    logger.info(f"Iniciando sessão de handoff {handoff_id}")
    
    try:
        yield handoff_id, coordinator
        logger.info(f"Sessão de handoff {handoff_id} finalizada com sucesso")
    except Exception as e:
        logger.error(f"Erro na sessão de handoff {handoff_id}: {e}")
        # Cleanup automático se necessário
        if handoff_id in coordinator.active_handoffs:
            await coordinator._execute_rollback(coordinator.active_handoffs[handoff_id])
        raise


# Decoradores utilitários
def handoff_capable(*capabilities):
    """Decorator para marcar métodos capazes de handoff"""
    def decorator(cls):
        if not hasattr(cls, '_handoff_capabilities'):
            cls._handoff_capabilities = []
        cls._handoff_capabilities.extend(capabilities)
        return cls
    return decorator


def auto_register_agent(agent_id: str, capabilities: List[str] = None):
    """Decorator para auto-registro de agentes"""
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            coordinator = get_handoff_coordinator()
            coordinator.register_agent(agent_id, self, capabilities or getattr(cls, '_handoff_capabilities', []))
        
        cls.__init__ = new_init
        return cls
    return decorator