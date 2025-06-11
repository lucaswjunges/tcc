import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional, Union

from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext, Task, ArtifactState
from evolux_engine.schemas.contracts import (
    TaskType,
    ExecutionResult,
    ArtifactChange,
    TaskDetailsCreateFile,
    TaskDetailsModifyFile,
    TaskDetailsExecuteCommand,
    # Adicionar outros TaskDetails conforme necessário
)
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService
# Assumindo que os prompts específicos para execução serão gerenciados aqui ou importados
from .executor_prompts import (
    get_file_content_generation_prompt,
    get_command_generation_prompt,
    get_file_modification_prompt,
)


class TaskExecutorAgent:
    """
    O TaskExecutorAgent é responsável por executar uma única tarefa genérica
    da task_queue, interpretando seu tipo e interagindo com LLMs ou
    serviços do sistema conforme necessário.
    """

    def __init__(
        self,
        executor_llm_client: LLMClient,  # LLM para gerar conteúdo/comandos
        project_context: ProjectContext,
        file_service: FileService,
        shell_service: ShellService,
        agent_id: str,
    ):
        self.executor_llm = executor_llm_client
        self.project_context = project_context
        self.file_service = file_service
        self.shell_service = shell_service
        self.agent_id = agent_id
        logger.info(
            f"TaskExecutorAgent inicializado para o projeto ID: {self.project_context.project_id}, Agent ID: {self.agent_id}"
        )

    async def _generate_llm_json_response(
        self, messages: List[Dict[str, str]], expected_json_key: str
    ) -> Optional[Any]:
        """Gera uma resposta do LLM e tenta parsear um JSON, retornando o valor de expected_json_key."""
        try:
            response_text = await self.executor_llm.generate_response(
                messages, timeout=180, max_tokens=4096 # Ajustar tokens conforme a necessidade
            )
            if not response_text:
                logger.error(f"TaskExecutorAgent (ID: {self.agent_id}): Nenhuma resposta recebida da LLM.")
                return None

            logger.debug(f"TaskExecutorAgent (ID: {self.agent_id}): Resposta bruta da LLM: {response_text[:500]}...")

            # Tenta encontrar o JSON na resposta
            json_start_index = response_text.find("{")
            json_end_index = response_text.rfind("}") + 1

            if json_start_index != -1 and json_end_index != -1:
                json_str = response_text[json_start_index:json_end_index]
                try:
                    parsed_response = json.loads(json_str)
                    if expected_json_key not in parsed_response:
                        logger.error(f"TaskExecutorAgent (ID: {self.agent_id}): Chave '{expected_json_key}' não encontrada na resposta JSON da LLM. Resposta: {json_str}")
                        # Salvar para depuração
                        raw_response_path = self.project_context.get_project_path(f"executor_json_key_error_{uuid.uuid4()}.txt")
                        self.file_service.save_file(raw_response_path, response_text)
                        logger.info(f"Resposta bruta salva em: {raw_response_path}")
                        return None
                    return parsed_response[expected_json_key]
                except json.JSONDecodeError as e:
                    logger.error(
                        f"TaskExecutorAgent (ID: {self.agent_id}): Falha ao decodificar JSON da resposta da LLM. Erro: {e}. Resposta: {json_str}"
                    )
                    raw_response_path = self.project_context.get_project_path(f"executor_json_decode_error_{uuid.uuid4()}.txt")
                    self.file_service.save_file(raw_response_path, response_text)
                    logger.info(f"Resposta bruta salva em: {raw_response_path}")
                    return None
            else:
                # Se não for JSON, e a tarefa for gerar conteúdo, pode ser que a LLM deu o conteúdo direto
                # Isso é um fallback, o ideal é a LLM sempre responder JSON
                if expected_json_key == "file_content": # Suposição para CREATE_FILE/MODIFY_FILE
                     logger.warning(f"TaskExecutorAgent (ID: {self.agent_id}): Resposta da LLM não é JSON, mas esperava 'file_content'. Usando resposta bruta como conteúdo.")
                     return response_text
                logger.error(f"TaskExecutorAgent (ID: {self.agent_id}): Nenhum JSON válido encontrado na resposta da LLM. Resposta: {response_text[:500]}...")
                return None

        except asyncio.TimeoutError:
            logger.error(f"TaskExecutorAgent (ID: {self.agent_id}): Timeout ao consultar LLM.")
            return None
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutorAgent (ID: {self.agent_id}): Erro inesperado ao consultar LLM.")
            return None


    async def _execute_create_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsCreateFile):
            return ExecutionResult(
                command_executed=f"Internal: CREATE_FILE task type mismatch for task {task.task_id}",
                exit_code=1,
                stderr="Detalhes da tarefa não correspondem ao tipo CREATE_FILE.",
            )

        details: TaskDetailsCreateFile = task.details
        file_path_in_artifacts = details.file_path # Assumindo que o planner dá o caminho relativo à pasta artifacts
        full_file_path = self.project_context.get_artifact_path(file_path_in_artifacts)

        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}): Executando CREATE_FILE para '{full_file_path}' (Tarefa: {task.task_id})"
        )

        # Preparar contexto para o LLM (se houver arquivos relevantes)
        context_files_content = {}
        # Aqui você poderia adicionar lógica para buscar conteúdo de arquivos que são dependências
        # por exemplo, se a guideline menciona "baseado no arquivo X.py"

        user_prompt_content = get_file_content_generation_prompt(
            file_path=file_path_in_artifacts,
            guideline=details.content_guideline,
            project_goal=self.project_context.project_goal,
            existing_artifacts=self.project_context.get_artifacts_structure_summary(),
            context_files=context_files_content
        )

        messages = [
            # Poderia ter um system_prompt aqui também, instruindo sobre a geração de código/texto
            {"role": "system", "content": "Você é uma IA assistente especializada em gerar conteúdo para arquivos. Responda APENAS com o conteúdo do arquivo solicitado, dentro de um objeto JSON com a chave 'file_content'. Não adicione explicações ou markdown fora do JSON."},
            {"role": "user", "content": user_prompt_content},
        ]

        file_content = await self._generate_llm_json_response(messages, "file_content")

        if file_content is None:
            return ExecutionResult(
                command_executed=f"LLM content generation for {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Falha ao gerar conteúdo da LLM para o arquivo {file_path_in_artifacts}.",
            )

        try:
            self.file_service.save_file(full_file_path, file_content)
            logger.info(
                f"TaskExecutorAgent (ID: {self.agent_id}): Arquivo '{full_file_path}' criado/atualizado com sucesso."
            )
            artifact_change = ArtifactChange(path=file_path_in_artifacts, change_type="created")
            # Atualizar o artifacts_state no ProjectContext
            file_hash = self.file_service.get_file_hash(full_file_path)
            self.project_context.update_artifact_state(
                file_path_in_artifacts,
                ArtifactState(hash=file_hash, summary=f"Arquivo {file_path_in_artifacts} criado/sobrescrito.")
            )
            await self.project_context.save_context() # Salvar após a modificação

            return ExecutionResult(
                command_executed=f"CREATE_FILE {file_path_in_artifacts}",
                exit_code=0,
                stdout=f"Arquivo {file_path_in_artifacts} criado com sucesso.",
                artifacts_changed=[artifact_change],
            )
        except Exception as e:
            logger.opt(exception=True).error(
                f"TaskExecutorAgent (ID: {self.agent_id}): Erro ao salvar arquivo {full_file_path}."
            )
            return ExecutionResult(
                command_executed=f"CREATE_FILE {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Erro ao salvar arquivo {full_file_path}: {e}",
            )

    async def _execute_modify_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsModifyFile):
            return ExecutionResult(
                command_executed=f"Internal: MODIFY_FILE task type mismatch for task {task.task_id}",
                exit_code=1,
                stderr="Detalhes da tarefa não correspondem ao tipo MODIFY_FILE.",
            )

        details: TaskDetailsModifyFile = task.details
        file_path_in_artifacts = details.file_path
        full_file_path = self.project_context.get_artifact_path(file_path_in_artifacts)

        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}): Executando MODIFY_FILE para '{full_file_path}' (Tarefa: {task.task_id})"
        )

        if not os.path.exists(full_file_path):
            logger.error(f"TaskExecutorAgent (ID: {self.agent_id}): Arquivo a ser modificado não existe: {full_file_path}")
            return ExecutionResult(
                command_executed=f"MODIFY_FILE {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Arquivo a ser modificado não encontrado: {file_path_in_artifacts}",
            )

        try:
            current_content = self.file_service.read_file(full_file_path)
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutorAgent (ID: {self.agent_id}): Erro ao ler arquivo existente {full_file_path}.")
            return ExecutionResult(
                command_executed=f"MODIFY_FILE {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Erro ao ler arquivo {full_file_path} para modificação: {e}",
            )

        user_prompt_content = get_file_modification_prompt(
            file_path=file_path_in_artifacts,
            current_content=current_content,
            guideline=details.modification_guideline,
            project_goal=self.project_context.project_goal
        )

        messages = [
            {"role": "system", "content": "Você é uma IA assistente especializada em modificar arquivos de código ou texto. Dada a guideline e o conteúdo atual, forneça APENAS o conteúdo COMPLETO e MODIFICADO do arquivo, dentro de um objeto JSON com a chave 'modified_content'. Não inclua diffs ou explicações fora do JSON."},
            {"role": "user", "content": user_prompt_content},
        ]

        modified_content = await self._generate_llm_json_response(messages, "modified_content")

        if modified_content is None:
            return ExecutionResult(
                command_executed=f"LLM content modification for {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Falha ao gerar conteúdo modificado da LLM para o arquivo {file_path_in_artifacts}.",
            )

        try:
            self.file_service.save_file(full_file_path, modified_content)
            logger.info(
                f"TaskExecutorAgent (ID: {self.agent_id}): Arquivo '{full_file_path}' modificado com sucesso."
            )
            artifact_change = ArtifactChange(path=file_path_in_artifacts, change_type="modified")
            
            file_hash = self.file_service.get_file_hash(full_file_path)
            self.project_context.update_artifact_state(
                file_path_in_artifacts,
                ArtifactState(hash=file_hash, summary=f"Arquivo {file_path_in_artifacts} modificado.")
            )
            await self.project_context.save_context()

            return ExecutionResult(
                command_executed=f"MODIFY_FILE {file_path_in_artifacts}",
                exit_code=0,
                stdout=f"Arquivo {file_path_in_artifacts} modificado com sucesso.",
                artifacts_changed=[artifact_change],
            )
        except Exception as e:
            logger.opt(exception=True).error(
                f"TaskExecutorAgent (ID: {self.agent_id}): Erro ao salvar arquivo modificado {full_file_path}."
            )
            return ExecutionResult(
                command_executed=f"MODIFY_FILE {file_path_in_artifacts}",
                exit_code=1,
                stderr=f"Erro ao salvar arquivo modificado {full_file_path}: {e}",
            )


    async def _execute_command(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsExecuteCommand):
            return ExecutionResult(
                command_executed=f"Internal: EXECUTE_COMMAND task type mismatch for task {task.task_id}",
                exit_code=1,
                stderr="Detalhes da tarefa não correspondem ao tipo EXECUTE_COMMAND.",
            )
        details: TaskDetailsExecuteCommand = task.details
        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}): Preparando para executar comando descrito como '{details.command_description}' (Tarefa: {task.task_id})"
        )

        user_prompt_command_gen = get_command_generation_prompt(
            description=details.command_description,
            expected_outcome=details.expected_outcome,
            os_info="Ubuntu Linux", # Pode ser pego do sistema ou configurado
            project_artifacts_structure=self.project_context.get_artifacts_structure_summary()
        )
        messages = [
            {"role": "system", "content": "Você é uma IA assistente que traduz descrições de tarefas em comandos shell precisos e seguros para um ambiente Ubuntu. Responda APENAS com um objeto JSON contendo a chave 'command_to_execute' com o comando exato. Não inclua explicações ou markdown fora do JSON."},
            {"role": "user", "content": user_prompt_command_gen},
        ]

        command_to_execute = await self._generate_llm_json_response(messages, "command_to_execute")

        if not command_to_execute or not isinstance(command_to_execute, str):
            logger.error(
                f"TaskExecutorAgent (ID: {self.agent_id}): LLM não forneceu um comando válido para execução."
            )
            return ExecutionResult(
                command_executed=details.command_description, # Usar a descrição se o comando não foi gerado
                exit_code=1,
                stderr="Falha ao gerar comando da LLM.",
            )
        
        logger.info(f"TaskExecutorAgent (ID: {self.agent_id}): Comando gerado pela LLM: '{command_to_execute}'")

        # TODO: Integrar SecurityGateway aqui antes de executar
        # if not await security_gateway.is_safe(command_to_execute):
        #     return ExecutionResult(...)

        try:
            # Executar o comando no diretório de artefatos do projeto
            working_dir = self.project_context.get_project_path("artifacts")
            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)

            # O ShellService deve retornar um dict com 'stdout', 'stderr', 'exit_code'
            shell_result = await self.shell_service.execute_command(
                command_to_execute,
                working_directory=working_dir,
                timeout=task.details.get("timeout_seconds", 300) # Se timeout estiver nos detalhes
            )
            
            logger.info(
                f"TaskExecutorAgent (ID: {self.agent_id}): Comando '{command_to_execute}' executado. Exit code: {shell_result['exit_code']}"
            )
            logger.debug(f"Stdout: {shell_result['stdout']}")
            logger.debug(f"Stderr: {shell_result['stderr']}")

            # Heurística simples para detectar mudanças em artefatos.
            # Uma abordagem mais robusta seria comparar hashes de arquivos antes e depois,
            # ou ter o comando explicitando os artefatos que modifica.
            artifacts_changed = []
            if shell_result['exit_code'] == 0 and ("create" in command_to_execute.lower() or "touch" in command_to_execute.lower() or ">" in command_to_execute):
                 # Tentar listar arquivos para ver se algo mudou, ou confiar na validação posterior
                 # Por simplicidade, vamos deixar vazio por enquanto e depender da VALIDATE_ARTIFACT
                 pass


            return ExecutionResult(
                command_executed=command_to_execute,
                exit_code=shell_result["exit_code"],
                stdout=shell_result["stdout"],
                stderr=shell_result["stderr"],
                artifacts_changed=artifacts_changed, # Melhorar detecção de artefatos
            )
        except Exception as e:
            logger.opt(exception=True).error(
                f"TaskExecutorAgent (ID: {self.agent_id}): Erro ao executar comando '{command_to_execute}'."
            )
            return ExecutionResult(
                command_executed=command_to_execute,
                exit_code=1,
                stderr=f"Erro ao executar comando: {e}",
            )


    async def execute_task(self, task: Task) -> ExecutionResult:
        """
        Executa uma tarefa com base no seu tipo.
        """
        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}) iniciando execução da tarefa: {task.task_id} ({task.type.value}: {task.description})"
        )
        
        execution_result: ExecutionResult

        if task.type == TaskType.CREATE_FILE:
            execution_result = await self._execute_create_file(task)
        elif task.type == TaskType.MODIFY_FILE:
            execution_result = await self._execute_modify_file(task)
        elif task.type == TaskType.EXECUTE_COMMAND:
            execution_result = await self._execute_command(task)
        # elif task.type == TaskType.VALIDATE_ARTIFACT:
        #     # A validação é geralmente feita por um SemanticValidatorAgent separado
        #     # Mas se o TaskExecutorAgent for responsável por uma validação mais simples (e.g. existe arquivo)
        #     # poderia ser tratado aqui. Por enquanto, vamos assumir que é um passo separado.
        #     logger.warning(f"TaskExecutorAgent: Tipo de tarefa VALIDATE_ARTIFACT normalmente é tratado por outro agente. Marcando como sucesso preliminar.")
        #     return ExecutionResult(command_executed=task.description, exit_code=0, stdout="Validação delegada.")
        else:
            logger.error(
                f"TaskExecutorAgent (ID: {self.agent_id}): Tipo de tarefa desconhecido ou não suportado: {task.type.value}"
            )
            execution_result = ExecutionResult(
                command_executed=task.description,
                exit_code=1,
                stderr=f"Tipo de tarefa não suportado: {task.type.value}",
            )
        
        # Atualizar o histórico de execução no ProjectContext (pensar se isso é feito aqui ou no Orchestrator)
        # self.project_context.add_execution_to_history(task.task_id, execution_result)
        # await self.project_context.save_context()

        return execution_result


# Exemplo de como você pode organizar os prompts em executor_prompts.py
"""
# evolux_engine/src/agents/executor_prompts.py

def get_file_content_generation_prompt(
    file_path: str,
    guideline: str,
    project_goal: str,
    existing_artifacts: Optional[str] = None, # Ex: saida de `ls -R` ou um resumo
    context_files: Optional[Dict[str, str]] = None # Ex: {"common_utils.py": "conteudo..."}
) -> str:
    prompt = f"Gere o conteúdo COMPLETO para o arquivo '{file_path}'.\n"
    prompt += f"O objetivo geral do projeto é: '{project_goal}'.\n"
    if existing_artifacts:
        prompt += f"A estrutura atual de artefatos do projeto é:\n{existing_artifacts}\n"
    if context_files:
        prompt += "Considere o conteúdo dos seguintes arquivos relevantes como contexto:\n"
        for path, content in context_files.items():
            prompt += f"--- Conteúdo de {path} ---\n{content}\n---\n"
    prompt += f"\nGuideline específica para '{file_path}':\n{guideline}\n"
    prompt += "\nResponda APENAS com um objeto JSON contendo uma única chave 'file_content' com o conteúdo textual completo do arquivo. Não inclua explicações, markdown ou qualquer texto fora do objeto JSON."
    return prompt

def get_file_modification_prompt(
    file_path: str,
    current_content: str,
    guideline: str,
    project_goal: str
) -> str:
    prompt = f"Modifique o arquivo '{file_path}'.\n"
    prompt += f"O objetivo geral do projeto é: '{project_goal}'.\n"
    prompt += f"\nGuideline específica para a modificação em '{file_path}':\n{guideline}\n"
    prompt += f"\nConteúdo ATUAL do arquivo '{file_path}':\n```\n{current_content}\n```\n"
    prompt += "\nResponda APENAS com um objeto JSON contendo uma única chave 'modified_content' com o conteúdo COMPLETO e MODIFICADO do arquivo. Não forneça apenas o diff ou trechos. Forneça todo o arquivo com as modificações aplicadas."
    return prompt

def get_command_generation_prompt(
    description: str,
    expected_outcome: str,
    os_info: str = "Ubuntu Linux",
    project_artifacts_structure: Optional[str] = None
) -> str:
    prompt = f"Gere um comando shell para ser executado em um ambiente {os_info}.\n"
    prompt += f"Descrição da tarefa que o comando deve realizar: {description}\n"
    prompt += f"Resultado esperado após a execução do comando: {expected_outcome}\n"
    if project_artifacts_structure:
        prompt += f"A estrutura atual de artefatos do projeto (relativa ao diretório de trabalho do comando) é:\n{project_artifacts_structure}\n"
    prompt += "\nO comando deve ser seguro e evitar operações destrutivas desnecessárias. Assuma que o comando será executado no diretório raiz dos artefatos do projeto.\n"
    prompt += "Responda APENAS com um objeto JSON contendo uma única chave 'command_to_execute' com o comando shell exato a ser executado. Não inclua explicações ou markdown."
    return prompt
"""
