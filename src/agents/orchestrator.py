import asyncio
from typing import Optional, List
import uuid

from loguru import logger

from evolux_engine.models.project_context import ProjectContext, Task, TaskStatus, ProjectStatus
from evolux_engine.schemas.contracts import ExecutionResult, ValidationResult
from evolux_engine.services.config_manager import ConfigManager # Assumindo que você tem um
from evolux_engine.services.llm_client import LLMClient # Para passar para os agentes
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService
# from evolux_engine.services.security_gateway import SecurityGateway # Futuramente
# from evolux_engine.services.backup_system import BackupSystem # Futuramente
# from evolux_engine.services.observability_service import ObservabilityService # Futuramente
# from evolux_engine.services.criteria_engine import CriteriaEngine # Futuramente

from .planner import PlannerAgent
from .task_executor import TaskExecutorAgent # Criaremos a seguir
from .semantic_validator import SemanticValidatorAgent # Criaremos a seguir


class Orchestrator:
    """
    O Orchestrator gerencia o ciclo de vida completo de um projeto,
    coordenando os diferentes agentes (Planner, Executor, Validator)
    para alcançar o objetivo do projeto de forma iterativa.
    """

    def __init__(
        self,
        project_context: ProjectContext,
        config_manager: ConfigManager, # Para carregar configs globais, API keys, modelos padrão
        # Adicionar outros serviços conforme são implementados
    ):
        self.project_context = project_context
        self.config_manager = config_manager
        self.agent_id = f"orchestrator-{self.project_context.project_id}"

        # Inicializar serviços e clientes LLM
        # (Idealmente, as chaves de API e URLs seriam gerenciadas pelo ConfigManager
        #  e passadas para o LLMClient de forma segura)

        # Cliente LLM para o Planner (geralmente um modelo mais robusto)
        self.planner_llm_client = LLMClient(
            provider=self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter"),
            api_key=self.config_manager.get_api_key(
                self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter")
            ),
            model_name=self.config_manager.get_global_setting("DEFAULT_MODEL_PLANNER"),
        )

        # Cliente LLM para o Executor (pode ser um modelo mais rápido/barato para geração de conteúdo/comando)
        self.executor_llm_client = LLMClient(
            provider=self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter"),
            api_key=self.config_manager.get_api_key(
                self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter")
            ),
            # O TaskExecutorAgent pode querer modelos diferentes para conteúdo vs comando
            # Por enquanto, um modelo genérico para o executor. Isso pode ser refinado.
            model_name=self.config_manager.get_global_setting("DEFAULT_MODEL_EXECUTOR_CONTENT_GEN"),
        )

        # Cliente LLM para o Validator (geralmente um modelo robusto para raciocínio)
        self.validator_llm_client = LLMClient(
            provider=self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter"),
            api_key=self.config_manager.get_api_key(
                self.config_manager.get_global_setting("DEFAULT_LLM_PROVIDER", "openrouter")
            ),
            model_name=self.config_manager.get_global_setting("DEFAULT_MODEL_VALIDATOR"),
        )

        # Inicializar serviços que os agentes usarão
        self.file_service = FileService(project_base_dir=self.project_context.workspace_path) # workspace_path precisa estar no context
        self.shell_service = ShellService() # Adicionar config de segurança aqui no futuro

        # Inicializar agentes
        self.planner_agent = PlannerAgent(
            planner_llm_client=self.planner_llm_client,
            project_context=self.project_context,
            agent_id=f"planner-{self.project_context.project_id}"
        )
        self.task_executor_agent = TaskExecutorAgent(
            executor_llm_client=self.executor_llm_client,
            project_context=self.project_context,
            file_service=self.file_service,
            shell_service=self.shell_service, # Passar o shell service
            agent_id=f"task_executor-{self.project_context.project_id}"
        )
        self.semantic_validator_agent = SemanticValidatorAgent(
            validator_llm_client=self.validator_llm_client,
            project_context=self.project_context,
            file_service=self.file_service, # Validator pode precisar ler artefatos
            agent_id=f"validator-{self.project_context.project_id}"
        )

        # self.criteria_engine = CriteriaEngine(project_context=self.project_context) # Implementar depois
        # self.backup_system = BackupSystem(project_context=self.project_context) # Implementar depois
        # self.observability_service = ObservabilityService(project_context=self.project_context) # Implementar depois

        logger.info(f"Orchestrator (ID: {self.agent_id}) inicializado para projeto '{self.project_context.project_name}'.")

    async def _get_next_task(self) -> Optional[Task]:
        """
        Obtém a próxima tarefa PENDING da task_queue que não tenha dependências PENDING ou IN_PROGRESS.
        Marca a tarefa como WAITING_FOR_DEPENDENCIES se suas dependências não estiverem completas.
        """
        # Criar um mapa de status de tarefas para consulta rápida de dependências
        task_statuses: Dict[str, TaskStatus] = {
            task.task_id: task.status for task in self.project_context.task_queue
        }
        task_statuses.update(
            {task.task_id: task.status for task in self.project_context.completed_tasks}
        )

        for task_index, task in enumerate(self.project_context.task_queue):
            if task.status == TaskStatus.PENDING:
                dependencies_met = True
                for dep_id in task.dependencies:
                    if dep_id not in task_statuses or task_statuses[dep_id] != TaskStatus.COMPLETED:
                        dependencies_met = False
                        break
                
                if dependencies_met:
                    logger.info(f"Orchestrator: Próxima tarefa selecionada: {task.task_id} - {task.description}")
                    return task
                else:
                    # Se as dependências não foram atendidas e a tarefa ainda não foi marcada
                    if task.status != TaskStatus.WAITING_FOR_DEPENDENCIES:
                        logger.info(f"Orchestrator: Tarefa {task.task_id} aguardando dependências.")
                        # Não vamos modificar o status aqui diretamente para evitar complexidade no loop
                        # O Orchestrator pode simplesmente pular e tentar mais tarde.
                        # Ou, se quisermos, podemos atualizar o status:
                        # task.status = TaskStatus.WAITING_FOR_DEPENDENCIES
                        # self.project_context.task_queue[task_index] = task # Atualiza na lista
        return None

    async def run_project_cycle(self) -> ProjectStatus:
        """
        Executa o ciclo principal do projeto: planejar (se necessário), executar tarefas, validar.
        """
        logger.info(f"Orchestrator (ID: {self.agent_id}): Iniciando ciclo do projeto '{self.project_context.project_name}'.")

        # Fase 1: Planejamento (se ainda não foi feito)
        if self.project_context.status == ProjectStatus.INITIALIZING or not self.project_context.task_queue:
            logger.info(f"Orchestrator (ID: {self.agent_id}): Fase de Planejamento Inicial.")
            self.project_context.status = ProjectStatus.PLANNING
            await self.project_context.save_context()
            
            plan_successful = await self.planner_agent.generate_initial_plan()
            if not plan_successful or not self.project_context.task_queue:
                logger.error(f"Orchestrator (ID: {self.agent_id}): Falha no planejamento inicial. Encerrando.")
                self.project_context.status = ProjectStatus.PLANNING_FAILED
                await self.project_context.save_context()
                return self.project_context.status
            
            logger.info(f"Orchestrator (ID: {self.agent_id}): Plano inicial gerado com {len(self.project_context.task_queue)} tarefas.")
            self.project_context.status = ProjectStatus.PLANNED # Ou READY_TO_EXECUTE
            await self.project_context.save_context()

        # Loop principal de execução de tarefas
        iteration_count = self.project_context.metrics.total_iterations
        max_project_iterations = self.project_context.engine_config.max_project_iterations

        while self.project_context.status not in [
            ProjectStatus.COMPLETED_SUCCESSFULLY,
            ProjectStatus.COMPLETED_WITH_FAILURES,
            ProjectStatus.FAILED,
            ProjectStatus.PLANNING_FAILED
        ]:
            if iteration_count >= max_project_iterations:
                logger.warning(f"Orchestrator (ID: {self.agent_id}): Limite máximo de iterações do projeto ({max_project_iterations}) atingido.")
                self.project_context.status = ProjectStatus.FAILED # Ou COMPLETED_WITH_FAILURES
                break

            iteration_count += 1
            self.project_context.metrics.total_iterations = iteration_count
            logger.info(f"--- Iniciando Iteração do Projeto #{iteration_count} ---")
            self.project_context.status = ProjectStatus.RUNNING
            
            current_task = await self._get_next_task()

            if not current_task:
                if any(t.status == TaskStatus.IN_PROGRESS or t.status == TaskStatus.WAITING_FOR_DEPENDENCIES for t in self.project_context.task_queue):
                    logger.info("Orchestrator: Nenhuma tarefa PENDING com dependências resolvidas no momento. Aguardando conclusão de tarefas em progresso/dependentes.")
                    await asyncio.sleep(5) # Esperar um pouco antes de verificar novamente
                    # TODO: Implementar um mecanismo de detecção de deadlock/ciclo de dependência aqui
                    continue
                else:
                    logger.info(f"Orchestrator (ID: {self.agent_id}): Nenhuma tarefa restante na fila ou todas aguardando dependências que não serão resolvidas. Verificando conclusão do projeto.")
                    break # Sai do loop para verificar a conclusão do projeto

            current_task.status = TaskStatus.IN_PROGRESS
            current_task.attempt_number = current_task.retries + 1 # Usar retries para contar tentativas
            await self.project_context.save_context() # Salva alteração de status da tarefa

            logger.info(f"Orchestrator: Processando Tarefa ID: {current_task.task_id}, Descrição: {current_task.description}")

            # 1. Executar Tarefa
            execution_result: ExecutionResult = await self.task_executor_agent.execute_task(current_task)
            current_task.execution_history.append(execution_result) # Armazena o resultado da execução

            # 2. Validar Resultado da Execução (Semântica)
            if execution_result.success: # Se a execução em si não falhou (exit_code 0)
                logger.info(f"Orchestrator: Execução da tarefa {current_task.task_id} bem-sucedida. Validando semanticamente...")
                validation_result: ValidationResult = await self.semantic_validator_agent.validate_task_output(
                    task=current_task,
                    execution_output=execution_result.stdout or "", # Passar stdout relevante
                    # Pode precisar passar também artifacts_changed ou artifacts_state
                )
            else: # Execução falhou
                logger.warning(f"Orchestrator: Execução da tarefa {current_task.task_id} falhou. Exit code: {execution_result.exit_code}. Stderr: {execution_result.stderr}")
                validation_result = ValidationResult(
                    validation_passed=False,
                    identified_issues=[f"Execução direta da tarefa falhou: {execution_result.stderr or 'Erro desconhecido na execução.'}"],
                    suggested_improvements=[f"Corrigir o erro de execução: {execution_result.stderr or 'Sem detalhes do erro.'}"]
                )
            
            current_task.validation_history.append(validation_result)

            # 3. Decidir Próximo Passo
            if validation_result.validation_passed:
                logger.info(
                    f"Orchestrator: Tarefa {current_task.task_id} concluída e validada com sucesso!"
                )
                current_task.status = TaskStatus.COMPLETED
                self.project_context.task_queue.remove(current_task) # Mover da fila principal
                self.project_context.completed_tasks.append(current_task)
            else:
                logger.warning(
                    f"Orchestrator: Validação semântica para tarefa {current_task.task_id} falhou. Problemas: {validation_result.identified_issues}"
                )
                current_task.retries += 1
                if current_task.retries >= current_task.max_retries:
                    logger.error(
                        f"Orchestrator: Tarefa {current_task.task_id} excedeu o número máximo de tentativas ({current_task.max_retries})."
                    )
                    # Estratégia de escalonamento: tentar replanejar a tarefa
                    # Esta é uma simplificação. O replanejamento pode ser mais complexo.
                    error_feedback_for_planner = (
                        f"A tarefa '{current_task.description}' (ID: {current_task.task_id}) falhou {current_task.retries} vezes. "
                        f"Últimos problemas identificados: {'; '.join(validation_result.identified_issues)}. "
                        f"Últimas sugestões: {'; '.join(validation_result.suggested_improvements)}."
                        f"Resultado da última execução (exit code {execution_result.exit_code}):\n"
                        f"STDOUT: {execution_result.stdout[:500]}...\nSTDERR: {execution_result.stderr[:500]}..."
                    )
                    self.project_context.current_error_feedback_for_planner = error_feedback_for_planner
                    
                    logger.info(f"Orchestrator: Solicitando replanejamento para a tarefa {current_task.task_id} ao PlannerAgent.")
                    new_sub_tasks: Optional[List[Task]] = await self.planner_agent.replan_task(
                        failed_task=current_task,
                        error_feedback=error_feedback_for_planner
                    )

                    if new_sub_tasks:
                        logger.info(f"Orchestrator: PlannerAgent retornou {len(new_sub_tasks)} novas sub-tarefas.")
                        # Remover a tarefa falha da fila principal
                        self.project_context.task_queue.remove(current_task)
                        current_task.status = TaskStatus.FAILED # Marcar a original como falha (foi substituída)
                        self.project_context.completed_tasks.append(current_task) # Mover para 'completed' com status FAILED

                        # Adicionar novas sub-tarefas ao início da fila de tarefas
                        # É importante que as dependências dessas novas tarefas estejam corretas
                        # (ex: se referirem a IDs de tarefas já completas, ou entre si)
                        self.project_context.task_queue = new_sub_tasks + self.project_context.task_queue
                        logger.info(f"Orchestrator: Novas sub-tarefas adicionadas à fila. Continuando o processamento.")
                    else:
                        logger.error(f"Orchestrator: PlannerAgent não conseguiu replanejar a tarefa {current_task.task_id}. Marcando como falha definitiva.")
                        current_task.status = TaskStatus.FAILED
                        # Potencialmente mover para uma lista de 'failed_tasks' no context
                else:
                    logger.info(
                        f"Orchestrator: Tarefa {current_task.task_id} será tentada novamente (tentativa {current_task.retries}/{current_task.max_retries})."
                    )
                    current_task.status = TaskStatus.PENDING # Volta para pendente para ser pega novamente
                    # O feedback da validação já está no current_task.validation_history e pode ser usado
                    # pelo TaskExecutorAgent ou pelo prompt Engine para a próxima tentativa.
            
            # Salvar contexto após cada processamento de tarefa
            await self.project_context.save_context()

            # Verificação de conclusão do projeto (simplificada)
            # if not self.project_context.task_queue and await self.criteria_engine.is_project_complete():
            if not self.project_context.task_queue and not any(t.status == TaskStatus.PENDING or t.status == TaskStatus.IN_PROGRESS or t.status == TaskStatus.WAITING_FOR_DEPENDENCIES for t in self.project_context.task_queue):
                logger.info(f"Orchestrator (ID: {self.agent_id}): Fila de tarefas vazia. Verificando critérios de conclusão final.")
                # TODO: Chamada ao CriteriaEngine para validação final
                # if await self.criteria_engine.is_project_fully_validated():
                #    self.project_context.status = ProjectStatus.COMPLETED_SUCCESSFULLY
                # else:
                #    self.project_context.status = ProjectStatus.COMPLETED_WITH_FAILURES

                # Simplesmente marcar como concluído por agora, a validação final pode ser uma tarefa `VALIDATE_ARTIFACT` no fim do plano
                if any(task.status == TaskStatus.FAILED for task in self.project_context.completed_tasks):
                     self.project_context.status = ProjectStatus.COMPLETED_WITH_FAILURES
                else:
                    self.project_context.status = ProjectStatus.COMPLETED_SUCCESSFULLY

                logger.info(f"Orchestrator: Projeto '{self.project_context.project_name}' atingiu o estado: {self.project_context.status.value}")
                # await self.backup_system.create_final_backup()
                break 
                
        # Fim do loop while
        logger.info(f"Orchestrator (ID: {self.agent_id}): Ciclo do projeto '{self.project_context.project_name}' finalizado com status: {self.project_context.status.value}.")
        await self.project_context.save_context()
        return self.project_context.status

