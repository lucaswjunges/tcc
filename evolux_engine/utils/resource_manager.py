# Gerenciador de Recursos Assíncronos para Prevenir Vazamentos

import asyncio
import time
import weakref
from typing import Dict, Any, Set, Optional, Callable, AsyncContextManager
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("resource_manager")

@dataclass
class ResourceInfo:
    """Informações sobre um recurso gerenciado"""
    resource_id: str
    resource_type: str
    created_at: float
    cleanup_func: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AsyncResourceManager:
    """
    Gerenciador de recursos assíncronos que garante limpeza adequada
    e previne vazamentos de memória e recursos
    """
    
    def __init__(self, max_resources: int = 1000, cleanup_interval: int = 300):
        self.max_resources = max_resources
        self.cleanup_interval = cleanup_interval
        
        # Recursos ativos
        self.active_resources: Dict[str, ResourceInfo] = {}
        self.resource_refs: Set[weakref.ref] = set()
        
        # Estatísticas
        self.total_created = 0
        self.total_cleaned = 0
        self.forced_cleanups = 0
        
        # Task de limpeza periódica
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Inicia o gerenciador de recursos"""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("AsyncResourceManager started", max_resources=self.max_resources)
    
    async def stop(self):
        """Para o gerenciador e limpa todos os recursos"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Limpar todos os recursos ativos
        await self.cleanup_all()
        logger.info("AsyncResourceManager stopped")
    
    @asynccontextmanager
    async def manage_resource(self, 
                             resource_id: str, 
                             resource_type: str, 
                             cleanup_func: Optional[Callable] = None,
                             **metadata) -> AsyncContextManager[str]:
        """Context manager para recursos com cleanup automático"""
        
        # Verificar limite de recursos
        if len(self.active_resources) >= self.max_resources:
            await self._force_cleanup_oldest()
        
        # Registrar recurso
        resource_info = ResourceInfo(
            resource_id=resource_id,
            resource_type=resource_type,
            created_at=time.time(),
            cleanup_func=cleanup_func,
            metadata=metadata
        )
        
        self.active_resources[resource_id] = resource_info
        self.total_created += 1
        
        logger.debug("Resource registered", 
                    resource_id=resource_id, 
                    type=resource_type,
                    active_count=len(self.active_resources))
        
        try:
            yield resource_id
        finally:
            await self.cleanup_resource(resource_id)
    
    async def cleanup_resource(self, resource_id: str) -> bool:
        """Limpa um recurso específico"""
        resource_info = self.active_resources.get(resource_id)
        if not resource_info:
            return False
        
        try:
            # Executar função de limpeza se definida
            if resource_info.cleanup_func:
                if asyncio.iscoroutinefunction(resource_info.cleanup_func):
                    await resource_info.cleanup_func()
                else:
                    resource_info.cleanup_func()
            
            # Remover da lista ativa
            del self.active_resources[resource_id]
            self.total_cleaned += 1
            
            logger.debug("Resource cleaned up", 
                        resource_id=resource_id,
                        type=resource_info.resource_type,
                        age_seconds=time.time() - resource_info.created_at)
            
            return True
            
        except Exception as e:
            logger.error("Failed to cleanup resource", 
                        resource_id=resource_id,
                        error=str(e))
            
            # Remove anyway to prevent leak
            self.active_resources.pop(resource_id, None)
            return False
    
    async def cleanup_all(self):
        """Limpa todos os recursos ativos"""
        resource_ids = list(self.active_resources.keys())
        
        cleanup_tasks = [
            self.cleanup_resource(resource_id) 
            for resource_id in resource_ids
        ]
        
        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            
            logger.info("Bulk cleanup completed",
                       total=len(cleanup_tasks),
                       successful=successful,
                       failed=len(cleanup_tasks) - successful)
    
    async def cleanup_by_type(self, resource_type: str) -> int:
        """Limpa todos os recursos de um tipo específico"""
        matching_resources = [
            resource_id for resource_id, info in self.active_resources.items()
            if info.resource_type == resource_type
        ]
        
        cleanup_tasks = [
            self.cleanup_resource(resource_id)
            for resource_id in matching_resources
        ]
        
        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            
            logger.info("Type-specific cleanup completed",
                       resource_type=resource_type,
                       total=len(cleanup_tasks),
                       successful=successful)
            
            return successful
        
        return 0
    
    async def cleanup_old_resources(self, max_age_seconds: int = 3600) -> int:
        """Limpa recursos mais velhos que o tempo especificado"""
        current_time = time.time()
        old_resources = [
            resource_id for resource_id, info in self.active_resources.items()
            if current_time - info.created_at > max_age_seconds
        ]
        
        if not old_resources:
            return 0
        
        cleanup_tasks = [
            self.cleanup_resource(resource_id)
            for resource_id in old_resources
        ]
        
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        
        logger.warning("Old resources cleaned up",
                      max_age_seconds=max_age_seconds,
                      total=len(cleanup_tasks),
                      successful=successful)
        
        return successful
    
    async def _force_cleanup_oldest(self, count: int = 10):
        """Força limpeza dos recursos mais antigos"""
        if not self.active_resources:
            return
        
        # Ordenar por idade (mais antigos primeiro)
        sorted_resources = sorted(
            self.active_resources.items(),
            key=lambda x: x[1].created_at
        )
        
        oldest_resources = sorted_resources[:count]
        
        cleanup_tasks = [
            self.cleanup_resource(resource_id)
            for resource_id, _ in oldest_resources
        ]
        
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        
        self.forced_cleanups += successful
        
        logger.warning("Forced cleanup of oldest resources",
                      count=count,
                      successful=successful)
    
    async def _periodic_cleanup(self):
        """Task de limpeza periódica"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._running:
                    break
                
                # Limpar recursos antigos (mais de 1 hora)
                cleaned = await self.cleanup_old_resources(3600)
                
                if cleaned > 0:
                    logger.info("Periodic cleanup completed", resources_cleaned=cleaned)
                
                # Limpar weak references mortas
                self._cleanup_dead_refs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic cleanup", error=str(e))
    
    def _cleanup_dead_refs(self):
        """Remove weak references mortas"""
        dead_refs = {ref for ref in self.resource_refs if ref() is None}
        self.resource_refs -= dead_refs
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do gerenciador"""
        resource_types = {}
        current_time = time.time()
        
        for info in self.active_resources.values():
            resource_types[info.resource_type] = resource_types.get(info.resource_type, 0) + 1
        
        avg_age = 0
        if self.active_resources:
            total_age = sum(current_time - info.created_at for info in self.active_resources.values())
            avg_age = total_age / len(self.active_resources)
        
        return {
            'active_resources': len(self.active_resources),
            'total_created': self.total_created,
            'total_cleaned': self.total_cleaned,
            'forced_cleanups': self.forced_cleanups,
            'cleanup_efficiency': self.total_cleaned / max(1, self.total_created),
            'average_age_seconds': avg_age,
            'resource_types': resource_types,
            'max_resources': self.max_resources,
            'running': self._running
        }

# Instância global do gerenciador
_global_resource_manager: Optional[AsyncResourceManager] = None

async def get_resource_manager() -> AsyncResourceManager:
    """Obtém a instância global do gerenciador de recursos"""
    global _global_resource_manager
    
    if _global_resource_manager is None:
        _global_resource_manager = AsyncResourceManager()
        await _global_resource_manager.start()
    
    return _global_resource_manager

async def cleanup_global_resources():
    """Limpa o gerenciador global de recursos"""
    global _global_resource_manager
    
    if _global_resource_manager:
        await _global_resource_manager.stop()
        _global_resource_manager = None