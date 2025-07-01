# Async Orchestrator com paralelização massiva de tarefas

import asyncio
from typing import Optional, List, Dict, Set, Any, Callable
from loguru import logger
from dataclasses import dataclass
from datetime import datetime
import time
from enum import Enum

from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, TaskStatus, ProjectStatus, ExecutionResult, ValidationResult
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.llms.async_llm_client import AsyncLLMClient, LLMRequest
from evolux_engine.llms.model_router import ModelRouter, TaskCategory
from evolux_engine.prompts.prompt_engine import PromptEngine
from evolux_engine.services.async_file_service import AsyncFileService
from evolux_engine.services.shell_service import ShellService
from evolux_engine.utils.resource_manager import get_resource_manager
from evolux_engine.services.backup_system import BackupSystem
from evolux_engine.services.advanced_monitoring import get_metrics_collector, LLMMetrics, TaskMetrics
from evolux_engine.services.criteria_engine import CriteriaEngine
from evolux_engine.security.security_gateway import SecurityGateway, SecurityLevel
from evolux_engine.execution.secure_executor import SecureExecutor
from evolux_engine.services.enterprise_observability import EnterpriseObservabilityService
from .planner import PlannerAgent
from .async_executor import AsyncTaskExecutorAgent
from .validator import SemanticValidatorAgent

class TaskBatch:
    """Batch de tarefas para execução paralela"""
    
    def __init__(self, tasks: List[Task], batch_id: str):
        self.tasks = tasks
        self.batch_id = batch_id
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.results: Dict[str, ExecutionResult] = {}
        self.validations: Dict[str, ValidationResult] = {}

class TaskDependencyGraph:
    """Grafo de dependências para paralelização inteligente"""
    
    def __init__(self, tasks: List[Task]):
        self.tasks = {task.task_id: task for task in tasks}
        self.dependencies = self._build_dependency_graph(tasks)
        self.reverse_deps = self._build_reverse_dependencies()
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, Set[str]]:
        """Constrói grafo de dependências"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = set(task.dependencies)
        return graph
    
    def _build_reverse_dependencies(self) -> Dict[str, Set[str]]:
        """Constrói dependências reversas (quem depende de mim)"""
        reverse = {task_id: set() for task_id in self.tasks}
        for task_id, deps in self.dependencies.items():
            for dep_id in deps:
                if dep_id in reverse:
                    reverse[dep_id].add(task_id)
        return reverse
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[Task]:
        """Retorna tarefas prontas para execução (dependências satisfeitas)"""
        ready = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                deps_satisfied = all(dep_id in completed_tasks for dep_id in self.dependencies[task_id])
                if deps_satisfied:
                    ready.append(task)
        return ready
    
    def get_parallel_batches(self, completed_tasks: Set[str]) -> List[List[Task]]:
        """Organiza tarefas em batches paralelos"""
        batches = []
        remaining_tasks = {tid: task for tid, task in self.tasks.items() 
                          if task.status == TaskStatus.PENDING}
        local_completed = completed_tasks.copy()
        
        while remaining_tasks:
            # Encontrar tarefas prontas nesta iteração
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                deps_satisfied = all(dep_id in local_completed for dep_id in self.dependencies[task_id])
                if deps_satisfied:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Deadlock - alguma dependência circular ou faltando
                logger.warning("Possible circular dependency detected", 
                             remaining_tasks=list(remaining_tasks.keys()))
                break
            
            batches.append(ready_tasks)
            
            # Marcar como "completed" para próxima iteração
            for task in ready_tasks:
                local_completed.add(task.task_id)
                del remaining_tasks[task.task_id]
        
        return batches

@dataclass
class ParallelExecutionMetrics:
    """Métricas de execução paralela"""
    total_tasks: int = 0
    parallel_tasks: int = 0
    sequential_tasks: int = 0
    avg_batch_size: float = 0.0
    parallelization_efficiency: float = 0.0  # 0-1, quanto foi paralelizado
    total_execution_time: float = 0.0
    theoretical_sequential_time: float = 0.0
    speedup_factor: float = 1.0

class AsyncOrchestrator:
    """
    Orchestrator assíncrono com paralelização massiva:
    - Executa tarefas independentes em paralelo
    - Analise de dependências inteligente
    - Load balancing entre recursos
    - Execução adaptativa baseada em performance
    - Observabilidade completa
    """
    
    def __init__(self, project_context: ProjectContext, config_manager: ConfigManager):
        self.project_context = project_context
        self.config_manager = config_manager
        self.agent_id = f"async-orchestrator-{self.project_context.project_id}"
        
        # Configurações de paralelização
        self.max_parallel_tasks = config_manager.get_global_setting("max_parallel_tasks", 5)
        self.max_llm_concurrent = config_manager.get_global_setting("max_llm_concurrent", 10)
        self.enable_adaptive_batching = config_manager.get_global_setting("adaptive_batching", True)
        
        # Controle de concorrência com fair scheduling
        self.task_semaphore = asyncio.Semaphore(self.max_parallel_tasks)
        self.llm_semaphore = asyncio.Semaphore(self.max_llm_concurrent)
        
        # Queue de prioridades para tarefas
        self.priority_queue = asyncio.PriorityQueue()
        self.high_priority_tasks = set()
        
        # Pool de conexões reutilizáveis
        self.connection_pool = {}
        
        # Cache de resultados de dependências
        self.dependency_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Métricas
        self.parallel_metrics = ParallelExecutionMetrics()
        
        # Resource manager para prevenir vazamentos
        self.resource_manager = None  # Será inicializado no start()
        
        # Monitoring avançado
        self.metrics_collector = get_metrics_collector()
        
        # Inicializar componentes
        self._initialize_async_components()
        
        logger.info(f"AsyncOrchestrator initialized",
                   agent_id=self.agent_id,
                   max_parallel=self.max_parallel_tasks,
                   max_llm_concurrent=self.max_llm_concurrent)

    def _initialize_async_components(self):
        """Inicializa componentes assíncronos"""
        
        # LLM Clients assíncronos
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)
        
        if not api_key:
            raise ValueError(f"API Key para o provedor '{provider}' não foi encontrada.")
        
        # Múltiplos clientes LLM para diferentes tipos de tarefa
        self.planner_llm = AsyncLLMClient(
            provider=provider,
            api_key=api_key,
            model_name=self.config_manager.get_default_model_for("planner"),
            max_concurrent=5,
            cache_enabled=True
        )
        
        self.executor_llm = AsyncLLMClient(
            provider=provider,
            api_key=api_key,
            model_name=self.config_manager.get_default_model_for("executor_content_gen"),
            max_concurrent=self.max_llm_concurrent,
            cache_enabled=True
        )
        
        self.validator_llm = AsyncLLMClient(
            provider=provider,
            api_key=api_key,
            model_name=self.config_manager.get_default_model_for("validator"),
            max_concurrent=5,
            cache_enabled=True
        )
        
        # File Service assíncrono
        workspace_dir = self.project_context.workspace_path
        self.async_file_service = AsyncFileService(
            workspace_path=str(workspace_dir),
            max_concurrent_ops=20
        )
        
        # Outros componentes (mantendo compatibilidade)
        self.shell_service = ShellService(workspace_path=str(workspace_dir))
        self.model_router = ModelRouter()
        self.prompt_engine = PromptEngine()
        self.backup_system = BackupSystem()
        self.criteria_engine = CriteriaEngine()
        
        # Segurança e observabilidade
        security_level_str = self.config_manager.get_global_setting("security_level", "strict")
        security_level = SecurityLevel(security_level_str)
        self.security_gateway = SecurityGateway(security_level=security_level)
        self.secure_executor = SecureExecutor(security_gateway=self.security_gateway)
        
        from evolux_engine.config.advanced_config import AdvancedSystemConfig
        advanced_config = AdvancedSystemConfig()
        self.observability = EnterpriseObservabilityService(config=advanced_config)
        
        # Agentes
        self.planner_agent = PlannerAgent(
            context_manager=None,
            task_db=None,
            artifact_store=None,
            project_context=self.project_context
        )
        
        self.async_executor_agent = AsyncTaskExecutorAgent(
            async_llm_client=self.executor_llm,
            project_context=self.project_context,
            async_file_service=self.async_file_service,
            shell_service=self.shell_service,
            security_gateway=self.security_gateway,
            secure_executor=self.secure_executor,
            model_router=self.model_router,
            agent_id=f"async-executor-{self.project_context.project_id}"
        )
        
        self.semantic_validator_agent = SemanticValidatorAgent(
            validator_llm_client=self.validator_llm,  # Converter para async internamente
            project_context=self.project_context,
            file_service=None  # Usar async_file_service
        )

    async def start(self):
        """Inicia componentes assíncronos"""
        await self.planner_llm.start()
        await self.executor_llm.start()
        await self.validator_llm.start()
        
        # Iniciar resource manager
        self.resource_manager = await get_resource_manager()
        
        # Iniciar monitoring avançado
        self.metrics_collector.start_collection(interval=10.0)
        
        # Iniciar observabilidade
        if hasattr(self.observability, 'start_monitoring'):
            self.observability.start_monitoring()

    async def close(self):
        """Limpa recursos assíncronos"""
        await self.planner_llm.close()
        await self.executor_llm.close()
        await self.validator_llm.close()
        await self.async_file_service.close()
        
        # Parar monitoring
        self.metrics_collector.stop_collection()
        
        if hasattr(self.observability, 'stop_monitoring'):
            self.observability.stop_monitoring()

    async def run_project_cycle_parallel(self) -> ProjectStatus:
        """
        Executa ciclo do projeto com máxima paralelização
        """
        logger.info(f"AsyncOrchestrator: Iniciando ciclo paralelo do projeto '{self.project_context.project_name}'")
        
        start_time = time.time()
        
        try:
            # Inicializar componentes
            await self.start()
            
            # Fase 1: Planejamento (se necessário)
            if not self.project_context.task_queue:
                logger.info("Fase de Planejamento Inicial")
                self.project_context.status = ProjectStatus.PLANNING
                await self.project_context.save_context()
                
                plan_successful = await self.planner_agent.generate_initial_plan()
                if not plan_successful:
                    logger.error("Falha no planejamento inicial")
                    self.project_context.status = ProjectStatus.PLANNING_FAILED
                    await self.project_context.save_context()
                    return self.project_context.status
                
                self.project_context.status = ProjectStatus.PLANNED
                await self.project_context.save_context()
            
            # Fase 2: Execução Paralela
            await self._execute_tasks_in_parallel()
            
            # Fase 3: Conclusão
            await self._finalize_project()
            
            # Calcular métricas finais
            self.parallel_metrics.total_execution_time = time.time() - start_time
            self._calculate_performance_metrics()
            
            logger.info("Ciclo paralelo concluído",
                       total_time=self.parallel_metrics.total_execution_time,
                       speedup=self.parallel_metrics.speedup_factor,
                       efficiency=self.parallel_metrics.parallelization_efficiency)
            
            return self.project_context.status
            
        finally:
            await self.close()

    async def _execute_tasks_in_parallel(self):
        """Executa tarefas com paralelização inteligente"""
        
        logger.info("🚀 Iniciando execução paralela de tarefas")
        
        completed_task_ids = {task.task_id for task in self.project_context.completed_tasks}
        max_iterations = self.project_context.engine_config.max_project_iterations
        
        for iteration in range(max_iterations):
            self.project_context.metrics.total_iterations = iteration + 1
            
            # Construir grafo de dependências
            dependency_graph = TaskDependencyGraph(self.project_context.task_queue)
            
            # Organizar em batches paralelos
            parallel_batches = dependency_graph.get_parallel_batches(completed_task_ids)
            
            if not parallel_batches:
                logger.info("Nenhuma tarefa executável encontrada")
                break
            
            logger.info(f"🔄 Iteração {iteration + 1}: {len(parallel_batches)} batches paralelos")
            
            # Executar cada batch
            for batch_idx, batch_tasks in enumerate(parallel_batches):
                if not batch_tasks:
                    continue
                
                batch_id = f"batch_{iteration}_{batch_idx}"
                logger.info(f"⚡ Executando batch {batch_id} com {len(batch_tasks)} tarefas")
                
                # Executar batch em paralelo
                batch_results = await self._execute_task_batch(batch_tasks, batch_id)
                
                # Processar resultados
                for task_id, (exec_result, validation_result) in batch_results.items():
                    task = next(t for t in batch_tasks if t.task_id == task_id)
                    
                    if validation_result.validation_passed:
                        logger.success(f"✅ Tarefa {task_id} concluída com sucesso")
                        task.status = TaskStatus.COMPLETED
                        completed_task_ids.add(task_id)
                        
                        # Mover para concluídas
                        self.project_context.completed_tasks.append(task)
                        self.project_context.task_queue = [
                            t for t in self.project_context.task_queue if t.task_id != task_id
                        ]
                    else:
                        logger.warning(f"❌ Validação falhou para tarefa {task_id}")
                        await self._handle_task_failure(task, validation_result)
                
                # Salvar contexto após cada batch
                await self.project_context.save_context()
                
                # Atualizar métricas
                self.parallel_metrics.total_tasks += len(batch_tasks)
                self.parallel_metrics.parallel_tasks += len(batch_tasks) if len(batch_tasks) > 1 else 0
                self.parallel_metrics.sequential_tasks += 1 if len(batch_tasks) == 1 else 0
            
            # Verificar se todas as tarefas foram concluídas
            pending_tasks = [t for t in self.project_context.task_queue if t.status == TaskStatus.PENDING]
            if not pending_tasks:
                logger.info("🎯 Todas as tarefas foram concluídas!")
                break

    async def _execute_task_batch(self, tasks: List[Task], batch_id: str) -> Dict[str, tuple[ExecutionResult, ValidationResult]]:
        """Executa um batch de tarefas em paralelo"""
        
        batch = TaskBatch(tasks, batch_id)
        batch.started_at = datetime.now()
        
        logger.info(f"Executando batch {batch_id}",
                   task_count=len(tasks),
                   task_ids=[t.task_id for t in tasks])
        
        # Função para executar uma tarefa individual
        async def execute_single_task(task: Task) -> tuple[str, tuple[ExecutionResult, ValidationResult]]:
            async with self.task_semaphore:  # Controle de concorrência
                
                # Gerenciar recursos da tarefa
                async with self.resource_manager.manage_resource(
                    resource_id=f"task_{task.task_id}",
                    resource_type="task_execution",
                    task_type=task.type.value,
                    priority=getattr(task, 'priority', 'normal')
                ):
                    # Observabilidade - início
                    start_time = time.time()
                    await self.observability.record_task_start(task.task_id, task.type.value)
                    
                    try:
                        # Marcar como em progresso
                        task.status = TaskStatus.IN_PROGRESS
                        
                        # Executar tarefa
                        execution_result = await self.async_executor_agent.execute_task_async(task)
                        
                        # Validar resultado
                        validation_result = await self.semantic_validator_agent.validate_task_output(task, execution_result)
                        
                        # Observabilidade - fim
                        duration = time.time() - start_time
                        await self.observability.record_task_completion(
                            task.task_id,
                            validation_result.validation_passed,
                            duration,
                            execution_result.exit_code
                        )
                        
                        # Registrar métricas de tarefa
                        task_metrics = TaskMetrics(
                            task_type=task.type.value,
                            execution_time_ms=duration * 1000,
                            success=validation_result.validation_passed,
                            parallel_count=1,  # Will be updated in batch processing
                            dependency_cache_hit=dependency_key in self.dependency_cache if hasattr(self, 'dependency_cache') else False,
                            resource_usage={
                                'memory_mb': execution_result.memory_usage_mb if hasattr(execution_result, 'memory_usage_mb') else 0,
                                'cpu_percent': execution_result.cpu_usage_percent if hasattr(execution_result, 'cpu_usage_percent') else 0
                            }
                        )
                        self.metrics_collector.record_task_metrics(task_metrics)
                        
                        return task.task_id, (execution_result, validation_result)
                        
                    except Exception as e:
                        logger.error(f"Erro na execução da tarefa {task.task_id}", error=str(e))
                        
                        # Criar resultado de erro
                        error_result = ExecutionResult(
                            exit_code=1,
                            stderr=f"Erro na execução: {str(e)}"
                        )
                        
                        error_validation = ValidationResult(
                            validation_passed=False,
                            confidence_score=0.0,
                            identified_issues=[str(e)],
                            suggested_improvements=["Verificar logs de erro"]
                        )
                        
                        return task.task_id, (error_result, error_validation)
        
        # Executar todas as tarefas do batch concorrentemente
        batch_results = await asyncio.gather(
            *[execute_single_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Processar resultados
        results_dict = {}
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Exceção no batch {batch_id}", error=str(result))
                continue
            
            task_id, (exec_result, validation_result) = result
            results_dict[task_id] = (exec_result, validation_result)
        
        batch.completed_at = datetime.now()
        
        # Log de conclusão do batch
        successful_tasks = sum(1 for _, (_, validation) in results_dict.items() if validation.validation_passed)
        logger.info(f"Batch {batch_id} concluído",
                   successful=successful_tasks,
                   total=len(tasks),
                   duration_seconds=(batch.completed_at - batch.started_at).total_seconds())
        
        return results_dict

    async def _execute_with_dependency_cache(self, task: Task) -> tuple:
        """Executa tarefa com cache de dependências"""
        
        # Verificar se dependências estão em cache
        dependency_key = self._get_dependency_cache_key(task)
        
        if dependency_key in self.dependency_cache:
            self.cache_hits += 1
            cached_result = self.dependency_cache[dependency_key]
            logger.debug("Dependency cache hit", task_id=task.task_id, key=dependency_key)
            
            # Ainda precisa executar a tarefa, mas com contexto otimizado
            return await self._execute_task_with_context(task, cached_result)
        
        # Cache miss - executar normalmente e salvar resultado
        self.cache_misses += 1
        result = await self.executor.execute_task_async(task)
        validation = await self.validator.validate_task_output(task, result)
        
        # Salvar no cache se execução foi bem-sucedida
        if validation.validation_passed:
            self.dependency_cache[dependency_key] = {
                'result': result,
                'validation': validation,
                'cached_at': datetime.now()
            }
            
            # Limitar tamanho do cache
            if len(self.dependency_cache) > 100:
                await self._evict_oldest_cache_entries()
        
        return result, validation
    
    def _get_dependency_cache_key(self, task: Task) -> str:
        """Gera chave de cache baseada nas dependências da tarefa"""
        import hashlib
        
        # Combinar task type, dependencies e parâmetros críticos
        cache_data = {
            'type': task.task_type.value,
            'dependencies': sorted(task.dependencies),
            'critical_params': {
                'description': task.description[:100],  # Primeiros 100 chars
                'expected_output': task.expected_output
            }
        }
        
        cache_str = str(cache_data)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    async def _execute_task_with_context(self, task: Task, cached_context: dict) -> tuple:
        """Executa tarefa usando contexto em cache"""
        
        # Usar resultado cached como contexto para otimizar execução
        task.execution_context = task.execution_context or {}
        task.execution_context['cached_dependencies'] = cached_context
        
        result = await self.executor.execute_task_async(task)
        validation = await self.validator.validate_task_output(task, result)
        
        return result, validation
    
    async def _evict_oldest_cache_entries(self, keep_count: int = 50):
        """Remove entradas mais antigas do cache"""
        
        if len(self.dependency_cache) <= keep_count:
            return
        
        # Ordenar por data de cache
        cache_items = list(self.dependency_cache.items())
        cache_items.sort(key=lambda x: x[1]['cached_at'])
        
        # Manter apenas as mais recentes
        entries_to_keep = cache_items[-keep_count:]
        
        self.dependency_cache = {
            key: value for key, value in entries_to_keep
        }
        
        logger.debug("Cache evicted old entries", 
                    kept=len(self.dependency_cache),
                    evicted=len(cache_items) - keep_count)

    async def _handle_task_failure(self, task: Task, validation_result: ValidationResult):
        """Gerencia falha de tarefa com replanejamento"""
        
        task.retries += 1
        
        if task.retries >= task.max_retries:
            logger.error(f"Tarefa {task.task_id} excedeu máximo de tentativas")
            
            # Tentar replanejamento
            issues_str = ', '.join(validation_result.identified_issues) if validation_result.identified_issues else "Motivos não especificados"
            error_feedback = f"Tarefa '{task.description}' falhou após {task.retries} tentativas. Últimos erros: {issues_str}"
            
            replan_count = getattr(task, 'replan_count', 0)
            if replan_count < 3:
                new_tasks = await self.planner_agent.replan_task(task, error_feedback)
                if new_tasks:
                    for new_task in new_tasks:
                        new_task.replan_count = replan_count + 1
                    
                    # Substituir tarefa antiga
                    self.project_context.task_queue = [
                        t for t in self.project_context.task_queue if t.task_id != task.task_id
                    ]
                    self.project_context.task_queue.extend(new_tasks)
                    
                    logger.info(f"Tarefa replanejada: {len(new_tasks)} novas tarefas")
                else:
                    task.status = TaskStatus.FAILED
                    self.project_context.failed_tasks.append(task)
            else:
                task.status = TaskStatus.FAILED
                self.project_context.failed_tasks.append(task)
        else:
            logger.info(f"Tarefa {task.task_id} será tentada novamente (tentativa {task.retries + 1})")
            task.status = TaskStatus.PENDING

    async def _finalize_project(self):
        """Finaliza projeto com backup e relatórios"""
        
        logger.info("🏁 Finalizando projeto")
        
        # Verificação final
        completion_report = self.criteria_engine.check_completion(self.project_context)
        
        # Backup final
        artifacts_dir = str(self.project_context.workspace_path / "artifacts")
        backup_description = f"Backup final - Status: {completion_report.status.value}"
        
        try:
            backup_path = self.backup_system.create_snapshot(
                self.project_context,
                artifacts_dir,
                backup_description
            )
            logger.info(f"📦 Backup final criado: {backup_path}")
        except Exception as e:
            logger.error(f"Falha ao criar backup final: {e}")
        
        # Determinar status final
        if completion_report.status.value == "completed":
            final_status = ProjectStatus.COMPLETED_SUCCESSFULLY
        else:
            final_status = ProjectStatus.COMPLETED_WITH_FAILURES
        
        self.project_context.status = final_status
        await self.project_context.save_context()

    def _calculate_performance_metrics(self):
        """Calcula métricas de performance da paralelização"""
        
        if self.parallel_metrics.total_tasks > 0:
            # Eficiência de paralelização
            parallel_ratio = self.parallel_metrics.parallel_tasks / self.parallel_metrics.total_tasks
            self.parallel_metrics.parallelization_efficiency = parallel_ratio
            
            # Tamanho médio de batch
            if self.parallel_metrics.parallel_tasks > 0:
                # Estimativa baseada no número de tarefas paralelas
                estimated_batches = max(1, self.parallel_metrics.parallel_tasks // self.max_parallel_tasks)
                self.parallel_metrics.avg_batch_size = self.parallel_metrics.parallel_tasks / estimated_batches
            
            # Speedup estimado (simplificado)
            # Em um cenário ideal, paralelização deveria reduzir tempo
            if parallel_ratio > 0:
                self.parallel_metrics.speedup_factor = 1 + (parallel_ratio * (self.max_parallel_tasks - 1))
            else:
                self.parallel_metrics.speedup_factor = 1.0
        
        logger.info("📊 Métricas de Performance",
                   **self.parallel_metrics.__dict__)
                   
        # Coletar métricas de LLM
        self._collect_llm_metrics()

    def _collect_llm_metrics(self):
        """Coleta e registra métricas dos clientes LLM"""
        
        # Métricas do executor LLM
        if hasattr(self.executor_llm, 'get_metrics'):
            executor_metrics = self.executor_llm.get_metrics()
            llm_metrics = LLMMetrics(
                provider=self.executor_llm.provider.value,
                model=self.executor_llm.model_name,
                requests_per_minute=executor_metrics.get('total_requests', 0) * 60 / max(1, self.parallel_metrics.total_execution_time),
                avg_latency_ms=executor_metrics.get('avg_latency_ms', 0),
                success_rate=executor_metrics.get('success_rate', 0),
                tokens_per_second=executor_metrics.get('total_tokens', 0) / max(1, self.parallel_metrics.total_execution_time),
                cost_per_hour=executor_metrics.get('total_cost_usd', 0) * 3600 / max(1, self.parallel_metrics.total_execution_time),
                circuit_breaker_state=executor_metrics.get('circuit_breaker', {}).get('state', 'unknown')
            )
            self.metrics_collector.record_llm_metrics(llm_metrics)
            
        # Métricas do planner LLM
        if hasattr(self.planner_llm, 'get_metrics'):
            planner_metrics = self.planner_llm.get_metrics()
            llm_metrics = LLMMetrics(
                provider=self.planner_llm.provider.value,
                model=self.planner_llm.model_name,
                requests_per_minute=planner_metrics.get('total_requests', 0) * 60 / max(1, self.parallel_metrics.total_execution_time),
                avg_latency_ms=planner_metrics.get('avg_latency_ms', 0),
                success_rate=planner_metrics.get('success_rate', 0),
                tokens_per_second=planner_metrics.get('total_tokens', 0) / max(1, self.parallel_metrics.total_execution_time),
                cost_per_hour=planner_metrics.get('total_cost_usd', 0) * 3600 / max(1, self.parallel_metrics.total_execution_time),
                circuit_breaker_state=planner_metrics.get('circuit_breaker', {}).get('state', 'unknown')
            )
            self.metrics_collector.record_llm_metrics(llm_metrics)
            
        # Métricas do validator LLM
        if hasattr(self.validator_llm, 'get_metrics'):
            validator_metrics = self.validator_llm.get_metrics()
            llm_metrics = LLMMetrics(
                provider=self.validator_llm.provider.value,
                model=self.validator_llm.model_name,
                requests_per_minute=validator_metrics.get('total_requests', 0) * 60 / max(1, self.parallel_metrics.total_execution_time),
                avg_latency_ms=validator_metrics.get('avg_latency_ms', 0),
                success_rate=validator_metrics.get('success_rate', 0),
                tokens_per_second=validator_metrics.get('total_tokens', 0) / max(1, self.parallel_metrics.total_execution_time),
                cost_per_hour=validator_metrics.get('total_cost_usd', 0) * 3600 / max(1, self.parallel_metrics.total_execution_time),
                circuit_breaker_state=validator_metrics.get('circuit_breaker', {}).get('state', 'unknown')
            )
            self.metrics_collector.record_llm_metrics(llm_metrics)

    async def get_parallel_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de paralelização"""
        llm_metrics = {}
        
        # Coletar métricas dos LLM clients
        if hasattr(self.executor_llm, 'get_metrics'):
            llm_metrics['executor'] = self.executor_llm.get_metrics()
        if hasattr(self.planner_llm, 'get_metrics'):
            llm_metrics['planner'] = self.planner_llm.get_metrics()
        if hasattr(self.validator_llm, 'get_metrics'):
            llm_metrics['validator'] = self.validator_llm.get_metrics()
        
        # Métricas do file service
        file_metrics = self.async_file_service.get_metrics()
        
        return {
            'parallel_execution': self.parallel_metrics.__dict__,
            'llm_clients': llm_metrics,
            'file_service': file_metrics,
            'resource_manager': self.resource_manager.get_stats() if self.resource_manager else {},
            'dependency_cache': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
                'size': len(self.dependency_cache)
            },
            'advanced_monitoring': self.metrics_collector.get_dashboard_data(),
            'observability': self.observability.get_performance_metrics().__dict__ if hasattr(self.observability, 'get_performance_metrics') else {}
        }