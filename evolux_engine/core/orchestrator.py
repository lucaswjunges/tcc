import asyncio
from typing import Optional, List, Dict
from loguru import logger

# --- Imports Corrigidos para a Nova Estrutura ---
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, TaskStatus, ProjectStatus, ExecutionResult, ValidationResult
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService
from .planner import PlannerAgent
from .executor import TaskExecutorAgent
from .validator import SemanticValidatorAgent

class Orchestrator:
    """
    O Orchestrator gerencia o ciclo de vida completo de um projeto,
    coordenando os diferentes agentes (Planner, Executor, Validator)
    para alcançar o objetivo do projeto de forma iterativa.
    """

    def __init__(self, project_context: ProjectContext, config_manager: ConfigManager):
        self.project_context = project_context
        self.config_manager = config_manager
        self.agent_id = f"orchestrator-{self.project_context.project_id}"

        # --- Bloco de Inicialização Corrigido ---
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)

        # Validação para garantir que a chave de API foi carregada
        if not api_key:
            raise ValueError(f"API Key para o provedor '{provider}' não foi encontrada. Verifique seu arquivo .env.")

        self.planner_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("planner")
        )
        self.executor_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("executor_content_gen")
        )
        self.validator_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("validator")
        )

        # O workspace path agora é um objeto Path no ProjectContext
        workspace_dir = self.project_context.workspace_path
        self.file_service = FileService(workspace_path=str(workspace_dir))
        self.shell_service = ShellService(workspace_path=str(workspace_dir))
        
        # Passando o project_context para o planner agent
        self.planner_agent = PlannerAgent(
            context_manager=None,
            task_db=None,
            artifact_store=None,
            project_context=self.project_context
        )
        self.task_executor_agent = TaskExecutorAgent(
            executor_llm_client=self.executor_llm_client,
            project_context=self.project_context,
            file_service=self.file_service,
            shell_service=self.shell_service,
            agent_id=f"executor-{self.project_context.project_id}"
        )
        self.semantic_validator_agent = SemanticValidatorAgent(
            validator_llm_client=self.validator_llm_client,
            project_context=self.project_context,
            file_service=self.file_service
        )
        # --- Fim do Bloco de Inicialização Corrigido ---

        logger.info(f"Orchestrator (ID: {self.agent_id}) inicializado para projeto '{self.project_context.project_name}'.")

    async def _get_next_task(self) -> Optional[Task]:
        """
        Obtém a próxima tarefa PENDING da task_queue que não tenha dependências PENDING ou IN_PROGRESS.
        """
        task_statuses: Dict[str, TaskStatus] = {task.task_id: task.status for task in self.project_context.task_queue}
        task_statuses.update({task.task_id: task.status for task in self.project_context.completed_tasks})

        for task in self.project_context.task_queue:
            if task.status == TaskStatus.PENDING:
                dependencies_met = all(
                    task_statuses.get(dep_id) == TaskStatus.COMPLETED for dep_id in task.dependencies
                )
                
                if dependencies_met:
                    logger.info(f"Orchestrator: Próxima tarefa selecionada: {task.task_id} - {task.description}")
                    return task
        return None

    async def run_project_cycle(self) -> ProjectStatus:
        """
        Executa o ciclo principal do projeto: planejar (se necessário), executar tarefas, validar.
        """
        logger.info(f"Orchestrator (ID: {self.agent_id}): Iniciando ciclo do projeto '{self.project_context.project_name}'.")

        # Fase 1: Planejamento
        if not self.project_context.task_queue:
            logger.info(f"Orchestrator: Fase de Planejamento Inicial.")
            self.project_context.status = ProjectStatus.PLANNING
            await self.project_context.save_context()
            
            plan_successful = await self.planner_agent.generate_initial_plan()
            if not plan_successful:
                logger.error("Falha no planejamento inicial. Encerrando.")
                self.project_context.status = ProjectStatus.PLANNING_FAILED
                await self.project_context.save_context()
                return self.project_context.status
            
            self.project_context.status = ProjectStatus.PLANNED
            await self.project_context.save_context()

        # Loop principal de execução de tarefas
        max_iterations = self.project_context.engine_config.max_project_iterations
        while self.project_context.metrics.total_iterations < max_iterations:
            self.project_context.metrics.total_iterations += 1
            iteration = self.project_context.metrics.total_iterations
            logger.info(f"--- Iniciando Iteração do Projeto #{iteration} ---")
            
            current_task = await self._get_next_task()

            if not current_task:
                logger.info("Nenhuma tarefa executável encontrada. Verificando conclusão do projeto.")
                break

            current_task.status = TaskStatus.IN_PROGRESS
            await self.project_context.save_context()
            logger.info(f"Processando Tarefa: {current_task.task_id} - {current_task.description}")

            # 1. Executar Tarefa
            execution_result = await self.task_executor_agent.execute_task(current_task)
            # (Em uma implementação real, o resultado seria adicionado ao histórico da tarefa)

            # 2. Validar Resultado
            validation_result = await self.semantic_validator_agent.validate_task_output(current_task, execution_result)
            
            # 3. Decidir Próximo Passo
            if validation_result.validation_passed:
                logger.success(f"Tarefa {current_task.task_id} concluída e validada com sucesso!")
                current_task.status = TaskStatus.COMPLETED
                # Mover da fila principal para a de concluídas
                self.project_context.completed_tasks.append(current_task)
                self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
            else:
                logger.warning(f"Validação para tarefa {current_task.task_id} falhou: {validation_result.identified_issues}")
                current_task.retries += 1
                if current_task.retries >= current_task.max_retries:
                    logger.error(f"Tarefa {current_task.task_id} excedeu o máximo de tentativas.")
                    current_task.status = TaskStatus.FAILED
                    # Lógica de replanejamento seria acionada aqui
                    error_feedback = (f"Tarefa '{current_task.description}' falhou após {current_task.retries} tentativas. "
                                      f"Último erro: {validation_result.identified_issues}")
                    new_tasks = await self.planner_agent.replan_task(current_task, error_feedback)
                    if new_tasks:
                        # Substituir a tarefa antiga pelas novas
                        self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
                        self.project_context.task_queue = new_tasks + self.project_context.task_queue
                else:
                    logger.info(f"Tarefa {current_task.task_id} será tentada novamente.")
                    current_task.status = TaskStatus.PENDING # Volta para a fila

            await self.project_context.save_context()

        # Fim do loop
        final_status = ProjectStatus.COMPLETED_SUCCESSFULLY if not any(t.status == TaskStatus.FAILED for t in self.project_context.completed_tasks) else ProjectStatus.COMPLETED_WITH_FAILURES
        self.project_context.status = final_status
        await self.project_context.save_context()
        logger.info(f"Ciclo do projeto finalizado com status: {self.project_context.status.value}.")
        return self.project_context.status