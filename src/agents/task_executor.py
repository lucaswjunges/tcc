import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional, List, Union

from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext, Task, ArtifactState
from evolux_engine.schemas.contracts import (
    TaskType,
    ExecutionResult,
    ArtifactChange,
    ArtifactChangeType,
    TaskDetailsCreateFile,
    TaskDetailsModifyFile,
    TaskDetailsDeleteFile,
    TaskDetailsExecuteCommand,
    TaskDetailsValidateArtifact, # Embora a validação principal seja do ValidatorAgent
    TaskDetailsAnalyzeOutput,
    TaskDetailsPlanSubTasks, # Normalmente o Planner Agent lida com isso, mas o Executor pode invocar se uma tarefa é de 'planejar sub-passos'
    TaskDetailsHumanInterventionRequired,
    TaskDetailsGenericLLMQuery,
    LLMCallMetrics,
)
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService # Assumindo que ele retorna um dict com stdout, stderr, exit_code
# from evolux_engine.services.security_gateway import SecurityGateway # A ser implementado

# Prompts do executor_prompts.py
from .executor_prompts import (
    FILE_MANIPULATION_SYSTEM_PROMPT,
    get_file_content_generation_prompt,
    get_file_modification_prompt,
    COMMAND_GENERATION_SYSTEM_PROMPT,
    get_command_generation_prompt,
    # Adicionar prompts para outros tipos de tarefa (AnalyzeOutput, GenericLLMQuery) se necessário
)


class TaskExecutorAgent:
    """
    O TaskExecutorAgent é responsável por executar uma única tarefa genérica
    da task_queue, interpretando seu tipo e interagindo com LLMs ou
    serviços do sistema conforme necessário.
    """

    def __init__(
        self,
        executor_llm_client: LLMClient,
        project_context: ProjectContext,
        file_service: FileService,
        shell_service: ShellService,
        # security_gateway: SecurityGateway, # Adicionar quando implementado
        agent_id: str,
    ):
        self.executor_llm = executor_llm_client
        self.project_context = project_context
        self.file_service = file_service
        self.shell_service = shell_service
        # self.security_gateway = security_gateway
        self.agent_id = agent_id
        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}) inicializado para o projeto ID: {self.project_context.project_id}"
        )

    async def _invoke_llm_for_json_output(
        self,
        messages: List[Dict[str, str]],
        expected_json_key: str,
        action_description: str # Ex: "geração de conteúdo de arquivo", "geração de comando"
    ) -> Optional[Any]:
        """
        Invoca o LLM esperando uma resposta JSON e extrai um valor de uma chave específica.
        Salva a resposta bruta em caso de erro para depuração.
        """
        task_id_for_log = "geral_executor" # Usar se não estiver no contexto de uma tarefa específica

        try:
            start_time = asyncio.get_event_loop().time()
            # Usar o modelo definido para o executor no config do projeto ou global
            model_to_use = self.project_context.engine_config.default_executor_model or \
                           self.executor_llm.model_name # Fallback para o modelo padrão do cliente
            
            llm_response_text = await self.executor_llm.generate_response(
                messages,
                model_override=model_to_use, # Permite override do modelo aqui
                timeout=180,
                max_tokens=4096
            )
            latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # TODO: Registrar LLMCallMetrics no ProjectContext.iteration_history
            # Isso precisaria de acesso ao log da iteração atual, melhor feito pelo Orchestrator

            if not llm_response_text:
                logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Nenhuma resposta da LLM.")
                return None

            logger.debug(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Resposta bruta LLM: {llm_response_text[:500]}...")

            json_start_index = llm_response_text.find("{")
            json_end_index = llm_response_text.rfind("}") + 1

            if json_start_index != -1 and json_end_index != -1:
                json_str = llm_response_text[json_start_index:json_end_index]
                try:
                    parsed_response = json.loads(json_str)
                    if expected_json_key not in parsed_response:
                        error_msg = f"Chave '{expected_json_key}' não encontrada no JSON da LLM. Resposta: {json_str}"
                        logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                        # Salvar para depuração dentro do workspace da tarefa
                        # self.file_service.save_file(self.project_context.get_log_path(f"executor_error_json_key_{task_id_for_log}_{uuid.uuid4()}.txt"),error_msg + "\n\nRAW_RESPONSE:\n" + llm_response_text)
                        return None
                    return parsed_response[expected_json_key]
                except json.JSONDecodeError as e:
                    error_msg = f"Falha ao decodificar JSON da LLM. Erro: {e}. JSON Tentado: {json_str}"
                    logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                    # self.file_service.save_file(self.project_context.get_log_path(f"executor_error_json_decode_{task_id_for_log}_{uuid.uuid4()}.txt"), error_msg + "\n\nRAW_RESPONSE:\n" + llm_response_text)
                    return None
            else:
                # Fallback para CREATE_FILE/MODIFY_FILE se não for JSON, mas a LLM pode ter retornado conteúdo direto
                if expected_json_key in ["file_content", "modified_content"]:
                    logger.warning(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Resposta da LLM não é JSON, mas esperava '{expected_json_key}'. Usando resposta bruta como conteúdo.")
                    return llm_response_text
                
                error_msg = f"Nenhum JSON válido encontrado na resposta da LLM. Resposta: {llm_response_text[:500]}..."
                logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                # self.file_service.save_file(self.project_context.get_log_path(f"executor_error_no_json_{task_id_for_log}_{uuid.uuid4()}.txt"), error_msg + "\n\nRAW_RESPONSE:\n" + llm_response_text)
                return None

        except asyncio.TimeoutError:
            logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Timeout ao consultar LLM.")
            return None
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Erro inesperado ao consultar LLM.")
            return None


    async def _execute_create_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsCreateFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa CREATE_FILE inválidos.")
        details: TaskDetailsCreateFile = task.details
        
        action_desc = f"geração de conteúdo para {details.file_path}"
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): {action_desc}")

        full_file_path = self.project_context.get_artifact_path(details.file_path)
        
        # Preparar contexto para o LLM de geração de conteúdo
        # TODO: Melhorar obtenção de contexto de dependências ou arquivos relevantes
        existing_artifacts_summary = self.project_context.get_artifacts_structure_summary()

        user_prompt = get_file_content_generation_prompt(
            file_path=details.file_path,
            guideline=details.content_guideline,
            project_goal=self.project_context.project_goal,
            project_type=self.project_context.project_type,
            existing_artifacts_summary=existing_artifacts_summary
        )
        messages = [{"role": "system", "content": FILE_MANIPULATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]

        file_content = await self._invoke_llm_for_json_output(messages, "file_content", action_desc)

        if file_content is None:
            return ExecutionResult(exit_code=1, stderr=f"Falha ao gerar conteúdo da LLM para {details.file_path}.")

        try:
            self.file_service.save_file(full_file_path, str(file_content)) # Garantir que é string
            artifact_change = ArtifactChange(path=details.file_path, change_type=ArtifactChangeType.CREATED)
            file_hash = self.file_service.get_file_hash(full_file_path)
            self.project_context.update_artifact_state(
                details.file_path,
                ArtifactState(path=details.file_path, hash=file_hash, summary=f"Arquivo criado/sobrescrito: {details.file_path}")
            )
            await self.project_context.save_context()
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} criado/atualizado.", artifacts_changed=[artifact_change])
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao salvar {full_file_path}: {e}")
            return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo {details.file_path}: {e}")

    async def _execute_modify_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsModifyFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa MODIFY_FILE inválidos.")
        details: TaskDetailsModifyFile = task.details

        action_desc = f"modificação de conteúdo para {details.file_path}"
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): {action_desc}")
        
        full_file_path = self.project_context.get_artifact_path(details.file_path)

        if not os.path.exists(full_file_path):
            return ExecutionResult(exit_code=1, stderr=f"Arquivo a ser modificado não encontrado: {details.file_path}")

        try:
            current_content = self.file_service.read_file(full_file_path)
        except Exception as e:
            return ExecutionResult(exit_code=1, stderr=f"Erro ao ler arquivo {details.file_path} para modificação: {e}")

        user_prompt = get_file_modification_prompt(
            file_path=details.file_path,
            current_content=current_content,
            guideline=details.modification_guideline,
            project_goal=self.project_context.project_goal,
            project_type=self.project_context.project_type
        )
        messages = [{"role": "system", "content": FILE_MANIPULATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]
        
        modified_content = await self._invoke_llm_for_json_output(messages, "modified_content", action_desc)

        if modified_content is None:
            return ExecutionResult(exit_code=1, stderr=f"Falha ao gerar conteúdo modificado da LLM para {details.file_path}.")

        try:
            old_hash = self.file_service.get_file_hash(full_file_path)
            self.file_service.save_file(full_file_path, str(modified_content))
            new_hash = self.file_service.get_file_hash(full_file_path)
            artifact_change = ArtifactChange(path=details.file_path, change_type=ArtifactChangeType.MODIFIED, old_hash=old_hash, new_hash=new_hash)
            
            self.project_context.update_artifact_state(
                details.file_path,
                ArtifactState(path=details.file_path, hash=new_hash, summary=f"Arquivo modificado: {details.file_path}")
            )
            await self.project_context.save_context()
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} modificado.", artifacts_changed=[artifact_change])
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao salvar arquivo modificado {full_file_path}: {e}")
            return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo modificado {details.file_path}: {e}")

    async def _execute_delete_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsDeleteFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa DELETE_FILE inválidos.")
        details: TaskDetailsDeleteFile = task.details

        action_desc = f"deleção do arquivo {details.file_path}"
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): {action_desc}")

        full_file_path = self.project_context.get_artifact_path(details.file_path)
        if not os.path.exists(full_file_path):
            logger.warning(f"TaskExecutor (ID: {self.agent_id}): Arquivo a ser deletado não existe: {full_file_path}. Considerando sucesso.")
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} já não existia.")
        
        try:
            old_hash = self.project_context.artifacts_state.get(details.file_path, ArtifactState(path=details.file_path)).hash
            self.file_service.delete_file(full_file_path)
            artifact_change = ArtifactChange(path=details.file_path, change_type=ArtifactChangeType.DELETED, old_hash=old_hash)
            
            self.project_context.remove_artifact_state(details.file_path)
            await self.project_context.save_context()
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} deletado.", artifacts_changed=[artifact_change])
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao deletar arquivo {full_file_path}: {e}")
            return ExecutionResult(exit_code=1, stderr=f"Erro ao deletar arquivo {details.file_path}: {e}")

    async def _execute_command(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsExecuteCommand):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa EXECUTE_COMMAND inválidos.")
        details: TaskDetailsExecuteCommand = task.details

        action_desc = f"geração de comando para: {details.command_description}"
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): {action_desc}")

        user_prompt = get_command_generation_prompt(
            command_description=details.command_description,
            expected_outcome=details.expected_outcome,
            project_artifacts_structure=self.project_context.get_artifacts_structure_summary()
        )
        messages = [{"role": "system", "content": COMMAND_GENERATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]

        command_to_execute = await self._invoke_llm_for_json_output(messages, "command_to_execute", action_desc)

        if not command_to_execute or not isinstance(command_to_execute, str):
            return ExecutionResult(exit_code=1, stderr="Falha ao gerar comando da LLM.", command_executed=details.command_description)
        
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Comando gerado pela LLM: '{command_to_execute}'")

        # TODO: Integração com SecurityGateway
        # if not await self.security_gateway.is_command_safe(command_to_execute, details.working_directory):
        #     logger.error(f"TaskExecutor: Comando '{command_to_execute}' bloqueado pelo SecurityGateway.")
        #     return ExecutionResult(command_executed=command_to_execute, exit_code=1, stderr="Comando bloqueado por razões de segurança.")

        try:
            working_dir = self.project_context.get_project_path("artifacts") # Comando executa na pasta artifacts
            if details.working_directory: # Se um subdir específico for dado
                 # Cuidado para não permitir `../../` etc sem sanitização
                safe_subdir = os.path.normpath(os.path.join("/", details.working_directory)).lstrip("/")
                working_dir = os.path.join(working_dir, safe_subdir)

            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)
            
            # Capturar estado dos artefatos ANTES do comando (para diff simples)
            # hashes_before = {p: s.hash for p, s in self.project_context.artifacts_state.items() if s.hash}

            shell_result = await self.shell_service.execute_command(
                command_to_execute,
                working_directory=working_dir,
                timeout=details.timeout_seconds
            )
            
            # Capturar estado dos artefatos DEPOIS e calcular diff
            # Esta é uma forma simplificada. Idealmente, o ShellService ou SecureExecutor poderiam
            # monitorar acessos a arquivos para fornecer uma lista mais precisa de artefatos alterados.
            artifacts_changed: List[ArtifactChange] = []
            # TODO: Implementar uma forma mais robusta de detectar mudanças em artefatos após um comando.
            # Por exemplo, iterar sobre self.project_context.artifacts_state, recalcular hashes e comparar.
            # Ou, mais avançado, usar inotify/fswatch dentro de um container.

            # Provisoriamente, vamos re-hashear tudo se o comando for bem sucedido.
            if shell_result["exit_code"] == 0:
                 for artifact_path_rel, artifact_state_obj in list(self.project_context.artifacts_state.items()): # list() para poder modificar
                    full_artifact_path = self.project_context.get_artifact_path(artifact_path_rel)
                    if os.path.exists(full_artifact_path):
                        new_hash = self.file_service.get_file_hash(full_artifact_path)
                        if new_hash != artifact_state_obj.hash:
                            artifacts_changed.append(ArtifactChange(
                                path=artifact_path_rel,
                                change_type=ArtifactChangeType.MODIFIED,
                                old_hash=artifact_state_obj.hash,
                                new_hash=new_hash
                            ))
                            self.project_context.update_artifact_state(
                                artifact_path_rel,
                                ArtifactState(path=artifact_path_rel, hash=new_hash, summary=f"Modificado pelo comando: {command_to_execute}")
                            )
                    else: # Arquivo foi deletado pelo comando
                        artifacts_changed.append(ArtifactChange(
                            path=artifact_path_rel,
                            change_type=ArtifactChangeType.DELETED,
                            old_hash=artifact_state_obj.hash
                        ))
                        self.project_context.remove_artifact_state(artifact_path_rel)
                 await self.project_context.save_context()


            return ExecutionResult(
                command_executed=command_to_execute,
                exit_code=shell_result["exit_code"],
                stdout=shell_result["stdout"],
                stderr=shell_result["stderr"],
                artifacts_changed=artifacts_changed,
            )
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao executar comando '{command_to_execute}': {e}")
            return ExecutionResult(command_executed=command_to_execute, exit_code=1, stderr=f"Erro ao executar comando: {e}")


    async def execute_task(self, task: Task) -> ExecutionResult:
        """
        Executa uma tarefa com base no seu tipo.
        """
        logger.info(
            f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Iniciando execução - Tipo: {task.type.value}, Desc: {task.description}"
        )
        
        if not task.details:
            logger.error(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Tarefa não possui detalhes. Não pode ser executada.")
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa ausentes.")

        exec_func_map = {
            TaskType.CREATE_FILE: self._execute_create_file,
            TaskType.MODIFY_FILE: self._execute_modify_file,
            TaskType.DELETE_FILE: self._execute_delete_file,
            TaskType.EXECUTE_COMMAND: self._execute_command,
            # TaskType.VALIDATE_ARTIFACT: # Delegado ao SemanticValidatorAgent
            # TaskType.ANALYZE_OUTPUT: self._execute_analyze_output, # Implementar
            # TaskType.PLAN_SUB_TASKS: # Normalmente tratado pelo Orchestrator/Planner
            # TaskType.HUMAN_INTERVENTION_REQUIRED: # Tratado pelo Orchestrator
            # TaskType.GENERIC_LLM_QUERY: self._execute_generic_llm_query, # Implementar
        }

        if task.type in exec_func_map:
            execution_result = await exec_func_map[task.type](task)
        else:
            logger.error(
                f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Tipo de tarefa '{task.type.value}' não suportado para execução direta por este agente."
            )
            execution_result = ExecutionResult(
                command_executed=task.description,
                exit_code=1,
                stderr=f"Tipo de tarefa não suportado para execução: {task.type.value}",
            )
        
        # Para consistência, o Orchestrator deve adicionar o ExecutionResult ao histórico da tarefa.
        # O TaskExecutor apenas executa e retorna o resultado.
        return execution_result

