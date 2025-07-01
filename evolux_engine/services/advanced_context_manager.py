import json
import asyncio
import pickle
import gzip
import shutil
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import threading
from collections import defaultdict, deque
import uuid

from evolux_engine.models.project_context import ProjectContext
from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.config.advanced_config import AdvancedSystemConfig

logger = get_structured_logger("advanced_context_manager")

class ContextStatus(Enum):
    """Status do contexto"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"

class PersistenceFormat(Enum):
    """Formatos de persistência"""
    JSON = "json"
    PICKLE = "pickle"
    COMPRESSED = "compressed"

@dataclass
class ContextSnapshot:
    """Snapshot de um contexto em um momento específico"""
    snapshot_id: str
    context_id: str
    timestamp: datetime
    version: int
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None

@dataclass
class ContextIndex:
    """Índice de contextos para busca rápida"""
    context_id: str
    project_name: str
    project_goal: str
    status: ContextStatus
    created_at: datetime
    last_modified: datetime
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    file_count: int = 0

@dataclass
class CacheEntry:
    """Entrada do cache de contextos"""
    context: ProjectContext
    last_accessed: datetime
    access_count: int = 0
    dirty: bool = False

class AdvancedContextManager:
    """
    Gerenciador de contexto enterprise-grade com:
    - Persistência multi-formato (JSON, Pickle, Compressed)
    - Cache inteligente com LRU
    - Versionamento e snapshots
    - Indexação e busca avançada
    - Backup automático
    - Compressão e otimização
    - Monitoramento e métricas
    - Transações e integridade
    """
    
    def __init__(self, config: AdvancedSystemConfig):
        self.config = config
        self.base_dir = Path(config.project_base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache settings
        self.cache_size = 100  # Maximum contexts in memory
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_access_order = deque()
        
        # Index for fast search
        self.context_index: Dict[str, ContextIndex] = {}
        self.index_path = self.base_dir / ".context_index.json"
        
        # Versioning
        self.snapshots: Dict[str, List[ContextSnapshot]] = defaultdict(list)
        self.snapshots_dir = self.base_dir / ".snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Backup settings
        self.backup_dir = self.base_dir / ".backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.backup_interval = timedelta(hours=config.backup_interval_hours)
        self.last_backup = datetime.now()
        
        # Threading
        self._lock = threading.RLock()
        self._background_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Metrics
        self.metrics = {
            'contexts_created': 0,
            'contexts_loaded': 0,
            'contexts_saved': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'snapshots_created': 0,
            'backups_created': 0
        }
        
        # Load existing index
        self._load_index()
        
        # Start background tasks if configured
        if config.backup_enabled:
            self._start_background_tasks()
        
        logger.info("AdvancedContextManager initialized")
    
    def _start_background_tasks(self):
        """Inicia tarefas em background"""
        self._background_thread = threading.Thread(
            target=self._background_loop,
            daemon=True
        )
        self._background_thread.start()
    
    def _background_loop(self):
        """Loop de tarefas em background"""
        while not self._shutdown_event.is_set():
            try:
                # Auto-save dirty cache entries
                self._auto_save_dirty_cache()
                
                # Backup if needed
                if self._should_create_backup():
                    self._create_automatic_backup()
                
                # Cleanup old snapshots
                self._cleanup_old_snapshots()
                
                # Update index
                self._save_index()
                
            except Exception as e:
                logger.error(f"Error in background loop: {str(e)}")
            
            # Wait before next iteration
            self._shutdown_event.wait(300)
    
    def create_new_project_context(self, 
                                 goal: str,
                                 project_name: Optional[str] = None,
                                 tags: Optional[Set[str]] = None,
                                 template_id: Optional[str] = None) -> ProjectContext:
        """Cria novo contexto de projeto com recursos avançados"""
        
        with self._lock:
            # Generate unique ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            goal_hash = hashlib.sha256(goal.encode()).hexdigest()[:8]
            project_id = f"proj_{timestamp}_{goal_hash}"
            
            # Determine project name
            if not project_name:
                project_name = self._generate_project_name(goal)
            
            # Create workspace
            workspace_path = self.base_dir / project_id
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Create directory structure
            self._create_workspace_structure(workspace_path)
            
            # Create context
            context = ProjectContext(
                project_id=project_id,
                project_name=project_name,
                project_goal=goal,
                workspace_path=workspace_path
            )
            
            # Apply template if specified
            if template_id:
                self._apply_context_template(context, template_id)
            
            # Create initial snapshot
            snapshot = self._create_snapshot(context, "Initial creation")
            
            # Update index
            self.context_index[project_id] = ContextIndex(
                context_id=project_id,
                project_name=project_name,
                project_goal=goal,
                status=ContextStatus.ACTIVE,
                created_at=datetime.now(),
                last_modified=datetime.now(),
                tags=tags or set(),
                size_bytes=0,
                file_count=0
            )
            
            # Add to cache
            self._add_to_cache(context)
            
            # Save immediately
            self.save_project_context(context)
            
            # Update metrics
            self.metrics['contexts_created'] += 1
            
            logger.info(f"New project context created for project_id: {project_id}, project_name: {project_name}, workspace: {str(workspace_path)}")
            
            return context
    
    def load_project_context(self, 
                           project_id: str,
                           version: Optional[int] = None) -> ProjectContext:
        """Carrega contexto com cache e versionamento"""
        
        with self._lock:
            # Check cache first
            if project_id in self.cache and version is None:
                cache_entry = self.cache[project_id]
                cache_entry.last_accessed = datetime.now()
                cache_entry.access_count += 1
                self._update_cache_order(project_id)
                self.metrics['cache_hits'] += 1
                
                logger.debug(f"Context loaded from cache for project_id: {project_id}")
                return cache_entry.context
            
            # Load from disk
            self.metrics['cache_misses'] += 1
            
            if version is not None:
                # Load specific version from snapshot
                context = self._load_context_from_snapshot(project_id, version)
            else:
                # Load latest version
                context = self._load_context_from_disk(project_id)
            
            # Add to cache if it's the latest version
            if version is None:
                self._add_to_cache(context)
            
            # Update metrics
            self.metrics['contexts_loaded'] += 1
            
            # Update index access time
            if project_id in self.context_index:
                self.context_index[project_id].last_modified = datetime.now()
            
            logger.info(f"Project context loaded for project_id: {project_id}, version: {version}")
            
            return context
    
    def save_project_context(self, 
                           context: ProjectContext,
                           create_snapshot: bool = False,
                           snapshot_message: Optional[str] = None) -> bool:
        """Salva contexto com opções avançadas"""
        
        try:
            with self._lock:
                # Validate context
                if not self._validate_context(context):
                    logger.error(f"Context validation failed for project_id: {context.project_id}")
                    return False
                
                # Save to disk
                success = self._save_context_to_disk(context)
                if not success:
                    return False
                
                # Update cache
                if context.project_id in self.cache:
                    self.cache[context.project_id].context = context
                    self.cache[context.project_id].dirty = False
                
                # Create snapshot if requested
                if create_snapshot:
                    self._create_snapshot(context, snapshot_message or "Manual snapshot")
                
                # Update index
                self._update_context_index(context)
                
                # Update metrics
                self.metrics['contexts_saved'] += 1
                
                logger.info(f"Project context saved for project_id: {context.project_id}, snapshot_created: {create_snapshot}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to save project context for project_id: {context.project_id}, error: {str(e)}")
            return False
    
    def _load_context_from_disk(self, project_id: str) -> ProjectContext:
        """Carrega contexto do disco"""
        context_path = self.base_dir / project_id / "context.json"
        
        if not context_path.exists():
            # Try compressed format
            compressed_path = self.base_dir / project_id / "context.json.gz"
            if compressed_path.exists():
                with gzip.open(compressed_path, 'rt') as f:
                    data = json.load(f)
            else:
                raise FileNotFoundError(f"No project found with ID '{project_id}'")
        else:
            with open(context_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Convert to ProjectContext
        context = ProjectContext(**data)
        return context
    
    def _save_context_to_disk(self, context: ProjectContext) -> bool:
        """Salva contexto no disco"""
        try:
            project_path = self.base_dir / context.project_id
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Prepare data
            data = context.model_dump()
            
            # Choose format based on size
            json_data = json.dumps(data, indent=2, default=str)
            data_size = len(json_data.encode('utf-8'))
            
            if data_size > 100 * 1024:  # > 100KB, use compression
                context_path = project_path / "context.json.gz"
                with gzip.open(context_path, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
            else:
                context_path = project_path / "context.json"
                with open(context_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save context to disk for project_id: {context.project_id}, error: {str(e)}")
            return False
    
    def _create_snapshot(self, 
                       context: ProjectContext,
                       message: str = "") -> ContextSnapshot:
        """Cria snapshot do contexto"""
        
        snapshot_id = str(uuid.uuid4())
        version = len(self.snapshots[context.project_id]) + 1
        
        # Create snapshot data
        data = context.model_dump()
        data_json = json.dumps(data, default=str)
        checksum = hashlib.sha256(data_json.encode()).hexdigest()
        
        snapshot = ContextSnapshot(
            snapshot_id=snapshot_id,
            context_id=context.project_id,
            timestamp=datetime.now(),
            version=version,
            data=data,
            metadata={"message": message},
            checksum=checksum
        )
        
        # Save snapshot to disk
        snapshot_path = self.snapshots_dir / f"{context.project_id}_{version}.json.gz"
        with gzip.open(snapshot_path, 'wt', encoding='utf-8') as f:
            json.dump({
                'snapshot_id': snapshot_id,
                'context_id': context.project_id,
                'timestamp': snapshot.timestamp.isoformat(),
                'version': version,
                'data': data,
                'metadata': snapshot.metadata,
                'checksum': checksum
            }, f, indent=2, default=str)
        
        # Add to memory
        self.snapshots[context.project_id].append(snapshot)
        
        # Update metrics
        self.metrics['snapshots_created'] += 1
        
        logger.debug(f"Context snapshot created for project_id: {context.project_id}, version: {version}, message: {message}")
        
        return snapshot
    
    def _load_context_from_snapshot(self, project_id: str, version: int) -> ProjectContext:
        """Carrega contexto de um snapshot específico"""
        
        # Check in memory first
        for snapshot in self.snapshots[project_id]:
            if snapshot.version == version:
                return ProjectContext(**snapshot.data)
        
        # Load from disk
        snapshot_path = self.snapshots_dir / f"{project_id}_{version}.json.gz"
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot version {version} not found for project {project_id}")
        
        with gzip.open(snapshot_path, 'rt', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        return ProjectContext(**snapshot_data['data'])
    
    def _add_to_cache(self, context: ProjectContext):
        """Adiciona contexto ao cache com LRU"""
        
        project_id = context.project_id
        
        # Check if cache is full
        if len(self.cache) >= self.cache_size and project_id not in self.cache:
            # Remove LRU item
            lru_id = self.cache_access_order.popleft()
            if lru_id in self.cache:
                # Save if dirty
                if self.cache[lru_id].dirty:
                    self.save_project_context(self.cache[lru_id].context)
                del self.cache[lru_id]
        
        # Add/update cache entry
        self.cache[project_id] = CacheEntry(
            context=context,
            last_accessed=datetime.now(),
            access_count=1
        )
        
        self._update_cache_order(project_id)
    
    def _update_cache_order(self, project_id: str):
        """Atualiza ordem de acesso do cache"""
        if project_id in self.cache_access_order:
            self.cache_access_order.remove(project_id)
        self.cache_access_order.append(project_id)
    
    def _validate_context(self, context: ProjectContext) -> bool:
        """Valida integridade do contexto"""
        try:
            # Check required fields
            if not context.project_id or not context.project_name:
                return False
            
            # Check workspace path exists
            if not context.workspace_path or not Path(context.workspace_path).exists():
                return False
            
            return True
            
        except Exception:
            return False
    
    def _update_context_index(self, context: ProjectContext):
        """Atualiza índice do contexto"""
        project_id = context.project_id
        
        if project_id in self.context_index:
            index_entry = self.context_index[project_id]
            index_entry.last_modified = datetime.now()
            index_entry.project_name = context.project_name
            
            # Update size and file count
            workspace_path = Path(context.workspace_path)
            if workspace_path.exists():
                total_size = sum(f.stat().st_size for f in workspace_path.rglob('*') if f.is_file())
                file_count = len(list(workspace_path.rglob('*')))
                index_entry.size_bytes = total_size
                index_entry.file_count = file_count
    
    def search_contexts(self, 
                       query: Optional[str] = None,
                       tags: Optional[Set[str]] = None,
                       status: Optional[ContextStatus] = None,
                       created_after: Optional[datetime] = None,
                       limit: int = 50) -> List[ContextIndex]:
        """Busca contextos baseado em critérios"""
        
        results = []
        
        for context_index in self.context_index.values():
            # Filter by query
            if query and query.lower() not in context_index.project_name.lower() and query.lower() not in context_index.project_goal.lower():
                continue
            
            # Filter by tags
            if tags and not tags.intersection(context_index.tags):
                continue
            
            # Filter by status
            if status and context_index.status != status:
                continue
            
            # Filter by creation date
            if created_after and context_index.created_at < created_after:
                continue
            
            results.append(context_index)
        
        # Sort by last modified (newest first)
        results.sort(key=lambda x: x.last_modified, reverse=True)
        
        return results[:limit]
    
    def list_all_contexts(self) -> List[ContextIndex]:
        """Lista todos os contextos"""
        return list(self.context_index.values())
    
    def delete_project_context(self, project_id: str, archive_first: bool = True) -> bool:
        """Deleta contexto do projeto"""
        
        try:
            with self._lock:
                # Archive first if requested
                if archive_first:
                    self.archive_project_context(project_id)
                
                # Remove from cache
                if project_id in self.cache:
                    del self.cache[project_id]
                    if project_id in self.cache_access_order:
                        self.cache_access_order.remove(project_id)
                
                # Remove workspace directory
                workspace_path = self.base_dir / project_id
                if workspace_path.exists():
                    shutil.rmtree(workspace_path)
                
                # Remove snapshots
                for snapshot in self.snapshots[project_id]:
                    snapshot_path = self.snapshots_dir / f"{project_id}_{snapshot.version}.json.gz"
                    if snapshot_path.exists():
                        snapshot_path.unlink()
                
                del self.snapshots[project_id]
                
                # Remove from index
                if project_id in self.context_index:
                    del self.context_index[project_id]
                
                logger.info(f"Project context deleted for project_id: {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete project context for project_id: {project_id}, error: {str(e)}")
            return False
    
    def archive_project_context(self, project_id: str) -> bool:
        """Arquiva contexto do projeto"""
        
        try:
            # Update status in index
            if project_id in self.context_index:
                self.context_index[project_id].status = ContextStatus.ARCHIVED
            
            # Create archive
            archive_path = self.backup_dir / f"{project_id}_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            workspace_path = self.base_dir / project_id
            
            if workspace_path.exists():
                shutil.make_archive(
                    str(archive_path.with_suffix('')),
                    'gztar',
                    workspace_path
                )
            
            logger.info(f"Project context archived for project_id: {project_id}, archive_path: {str(archive_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive project context for project_id: {project_id}, error: {str(e)}")
            return False
    
    def get_context_history(self, project_id: str) -> List[ContextSnapshot]:
        """Obtém histórico de snapshots do contexto"""
        return self.snapshots.get(project_id, [])
    
    def restore_context_from_snapshot(self, project_id: str, version: int) -> bool:
        """Restaura contexto de um snapshot"""
        
        try:
            # Load snapshot
            context = self._load_context_from_snapshot(project_id, version)
            
            # Save as current version
            success = self.save_project_context(context, create_snapshot=True, 
                                              snapshot_message=f"Restored from version {version}")
            
            if success:
                logger.info(f"Context restored from snapshot for project_id: {project_id}, version: {version}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to restore context from snapshot for project_id: {project_id}, version: {version}, error: {str(e)}")
            return False
    
    def _create_workspace_structure(self, workspace_path: Path):
        """Cria estrutura de diretórios do workspace"""
        (workspace_path / "artifacts").mkdir(exist_ok=True)
        (workspace_path / "logs").mkdir(exist_ok=True)
        (workspace_path / "backups").mkdir(exist_ok=True)
        (workspace_path / "temp").mkdir(exist_ok=True)
    
    def _generate_project_name(self, goal: str) -> str:
        """Gera nome do projeto baseado no goal"""
        # Extract key words from goal
        words = goal.lower().split()
        key_words = [w for w in words if len(w) > 3 and w.isalpha()][:3]
        
        if key_words:
            return " ".join(word.title() for word in key_words) + " Project"
        else:
            return "New Project"
    
    def _apply_context_template(self, context: ProjectContext, template_id: str):
        """Aplica template ao contexto"""
        # Implementation would load and apply template
        logger.debug(f"Template applied to context for project_id: {context.project_id}, template_id: {template_id}")
    
    def _auto_save_dirty_cache(self):
        """Salva automaticamente contextos modificados no cache"""
        dirty_contexts = [
            entry.context for entry in self.cache.values()
            if entry.dirty
        ]
        
        for context in dirty_contexts:
            self.save_project_context(context)
    
    def _should_create_backup(self) -> bool:
        """Verifica se deve criar backup"""
        return (datetime.now() - self.last_backup) >= self.backup_interval
    
    def _create_automatic_backup(self):
        """Cria backup automático"""
        try:
            backup_name = f"contexts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            
            # Create backup of entire contexts directory
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'gztar',
                self.base_dir,
                '.'
            )
            
            self.last_backup = datetime.now()
            self.metrics['backups_created'] += 1
            
            logger.info(f"Automatic backup created at: {str(backup_path)}")
            
        except Exception as e:
            logger.error(f"Failed to create automatic backup: {str(e)}")
    
    def _cleanup_old_snapshots(self):
        """Limpa snapshots antigos"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for project_id, snapshots in self.snapshots.items():
            old_snapshots = [s for s in snapshots if s.timestamp < cutoff_date]
            
            for snapshot in old_snapshots:
                # Keep at least 3 snapshots per project
                if len(snapshots) - len(old_snapshots) >= 3:
                    snapshot_path = self.snapshots_dir / f"{project_id}_{snapshot.version}.json.gz"
                    if snapshot_path.exists():
                        snapshot_path.unlink()
                    
                    snapshots.remove(snapshot)
    
    def _load_index(self):
        """Carrega índice de contextos"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for context_id, index_data in data.items():
                    # Convert timestamp strings back to datetime
                    index_data['created_at'] = datetime.fromisoformat(index_data['created_at'])
                    index_data['last_modified'] = datetime.fromisoformat(index_data['last_modified'])
                    index_data['status'] = ContextStatus(index_data['status'])
                    index_data['tags'] = set(index_data['tags'])
                    index_data['dependencies'] = set(index_data['dependencies'])
                    
                    self.context_index[context_id] = ContextIndex(**index_data)
                
                logger.debug(f"Context index loaded with {len(self.context_index)} contexts")
                
            except Exception as e:
                logger.error(f"Failed to load context index: {str(e)}")
    
    def _save_index(self):
        """Salva índice de contextos"""
        try:
            data = {}
            for context_id, index_entry in self.context_index.items():
                data[context_id] = {
                    'context_id': index_entry.context_id,
                    'project_name': index_entry.project_name,
                    'project_goal': index_entry.project_goal,
                    'status': index_entry.status.value,
                    'created_at': index_entry.created_at.isoformat(),
                    'last_modified': index_entry.last_modified.isoformat(),
                    'tags': list(index_entry.tags),
                    'dependencies': list(index_entry.dependencies),
                    'size_bytes': index_entry.size_bytes,
                    'file_count': index_entry.file_count
                }
            
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save context index: {str(e)}")
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do manager"""
        with self._lock:
            return {
                'total_contexts': len(self.context_index),
                'cached_contexts': len(self.cache),
                'total_snapshots': sum(len(snapshots) for snapshots in self.snapshots.values()),
                'cache_hit_rate': self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses']),
                'metrics': self.metrics.copy(),
                'storage_stats': self._get_storage_stats(),
                'backup_info': {
                    'last_backup': self.last_backup.isoformat(),
                    'backup_interval_hours': self.backup_interval.total_seconds() / 3600,
                    'backups_created': self.metrics['backups_created']
                }
            }
    
    def _get_storage_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de armazenamento"""
        total_size = 0
        total_files = 0
        
        for path in self.base_dir.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
                total_files += 1
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'total_files': total_files,
            'contexts_count': len(list(self.base_dir.glob('proj_*')))
        }
    
    def cleanup_and_shutdown(self):
        """Limpa recursos e fecha o manager"""
        logger.info("Shutting down AdvancedContextManager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for background thread
        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=10)
        
        # Save all dirty cache entries
        with self._lock:
            self._auto_save_dirty_cache()
            
            # Save index
            self._save_index()
        
        logger.info("AdvancedContextManager shutdown complete")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.cleanup_and_shutdown()
