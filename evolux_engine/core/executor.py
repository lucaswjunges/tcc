import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional, List, Union

from loguru import logger
from evolux_engine.utils.string_utils import extract_json_from_llm_response, sanitize_llm_response, extract_content_from_json_response

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.core.iterative_refiner import IterativeRefiner, RefinementStrategy
from evolux_engine.models.project_context import ProjectContext, ArtifactState
from evolux_engine.schemas.contracts import Task
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
from evolux_engine.security.security_gateway import SecurityGateway
from evolux_engine.execution.secure_executor import SecureExecutor
from evolux_engine.llms.model_router import ModelRouter

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
        security_gateway: Optional[SecurityGateway] = None,
        secure_executor: Optional[SecureExecutor] = None,
        model_router: Optional[ModelRouter] = None,
        agent_id: str = "task_executor",
        enable_iterative_refinement: bool = True,
        reviewer_llm_client: Optional[LLMClient] = None,
        validator_llm_client: Optional[LLMClient] = None
    ):
        self.executor_llm = executor_llm_client
        self.project_context = project_context
        self.file_service = file_service
        self.shell_service = shell_service
        self.security_gateway = security_gateway
        self.secure_executor = secure_executor
        self.model_router = model_router
        self.agent_id = agent_id
        self.enable_refinement = enable_iterative_refinement
        
        # Inicializar refinador iterativo se habilitado
        if enable_iterative_refinement and reviewer_llm_client and validator_llm_client:
            from evolux_engine.prompts.prompt_engine import PromptEngine
            self.prompt_engine = PromptEngine()
            self.iterative_refiner = IterativeRefiner(
                primary_llm=executor_llm_client,
                reviewer_llm=reviewer_llm_client,
                validator_llm=validator_llm_client,
                prompt_engine=self.prompt_engine,
                project_context=project_context
            )
        else:
            self.iterative_refiner = None
        
        logger.info(
            f"TaskExecutorAgent (ID: {self.agent_id}) inicializado para o projeto ID: {self.project_context.project_id}. Refinamento iterativo: {self.enable_refinement}"
        )
    
    def _build_project_context(self, task: Task) -> str:
        """Constrói contexto rico do projeto para injetar nas LLMs"""
        context_parts = []
        
        # Objetivo do projeto
        context_parts.append(f"OBJETIVO DO PROJETO: {self.project_context.project_goal}")
        
        # Tipo de projeto
        if self.project_context.project_type:
            context_parts.append(f"TIPO: {self.project_context.project_type}")
        
        # Arquivos já existentes
        existing_files = self._get_existing_files_summary()
        if existing_files:
            context_parts.append(f"ARQUIVOS EXISTENTES:\n{existing_files}")
        
        # Tarefas concluídas relacionadas
        related_tasks = self._get_related_completed_tasks(task)
        if related_tasks:
            context_parts.append(f"TAREFAS RELACIONADAS CONCLUÍDAS:\n{related_tasks}")
        
        # Padrões identificados no projeto
        patterns = self._identify_project_patterns()
        if patterns:
            context_parts.append(f"PADRÕES DO PROJETO:\n{patterns}")
        
        return "\n\n".join(context_parts)
    
    def _get_existing_files_summary(self) -> str:
        """Retorna resumo dos arquivos existentes com conteúdo relevante"""
        if not self.project_context.artifacts_state:
            return "Nenhum arquivo criado ainda."
        
        summary_lines = []
        artifacts_dir = self.project_context.workspace_path / "artifacts"
        
        for file_path, artifact_state in self.project_context.artifacts_state.items():
            summary_lines.append(f"- {file_path}")
            
            # Adicionar resumo do conteúdo se for arquivo pequeno
            try:
                full_path = artifacts_dir / file_path
                if full_path.exists() and full_path.stat().st_size < 1000:  # Só arquivos pequenos
                    content = full_path.read_text(encoding='utf-8')
                    if file_path.endswith('.py'):
                        # Extrair imports e classes/funções principais
                        lines = content.split('\n')
                        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
                        classes = [line.strip() for line in lines if line.strip().startswith('class ')]
                        functions = [line.strip() for line in lines if line.strip().startswith('def ')]
                        
                        if imports:
                            summary_lines.append(f"  Imports: {', '.join(imports[:3])}")
                        if classes:
                            summary_lines.append(f"  Classes: {', '.join([c.split('(')[0].replace('class ', '') for c in classes])}")
                        if functions:
                            summary_lines.append(f"  Funções: {', '.join([f.split('(')[0].replace('def ', '') for f in functions[:3]])}")
            except:
                pass  # Ignora erros de leitura
        
        return '\n'.join(summary_lines)
    
    def _get_related_completed_tasks(self, current_task: Task) -> str:
        """Identifica tarefas concluídas relacionadas à tarefa atual"""
        if not self.project_context.completed_tasks:
            return ""
        
        related_lines = []
        current_keywords = set(current_task.description.lower().split())
        
        for task in self.project_context.completed_tasks[-5:]:  # Últimas 5 tarefas
            task_keywords = set(task.description.lower().split())
            overlap = current_keywords & task_keywords
            
            if len(overlap) >= 2:  # Pelo menos 2 palavras em comum
                related_lines.append(f"- {task.description} ✓")
                if hasattr(task.details, 'file_path'):
                    related_lines.append(f"  Arquivo: {task.details.file_path}")
        
        return '\n'.join(related_lines) if related_lines else ""
    
    def _identify_project_patterns(self) -> str:
        """Identifica padrões no projeto baseado nos arquivos existentes"""
        patterns = []
        
        if not self.project_context.artifacts_state:
            return ""
        
        file_paths = list(self.project_context.artifacts_state.keys())
        
        # Padrão Flask
        if any('app.py' in path for path in file_paths):
            patterns.append("- Aplicação Flask detectada")
            if any('models.py' in path for path in file_paths):
                patterns.append("- Arquitetura MVC com modelos separados")
            if any('templates/' in path for path in file_paths):
                patterns.append("- Templates HTML organizados em diretório")
        
        # Padrão de dependências
        if any('requirements.txt' in path for path in file_paths):
            patterns.append("- Gerenciamento de dependências Python")
        
        # Padrão de documentação
        if any('README.md' in path for path in file_paths):
            patterns.append("- Documentação do projeto presente")
        
        return '\n'.join(patterns) if patterns else ""

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
            
            # Tentar com modelo principal primeiro, depois fallback se falhar
            llm_response_text = None
            
            try:
                # Usar timeout e parâmetros otimizados para performance
                llm_response_text = await asyncio.wait_for(
                    self.executor_llm.generate_response(
                        messages,
                        max_tokens=2048,  # Reduzido para melhor performance
                        temperature=0.3   # Mais determinístico
                    ),
                    timeout=60.0  # Timeout de 1 minuto
                )
            except Exception as e:
                logger.warning(f"Modelo principal {self.executor_llm.model_name} falhou: {str(e)[:100]}...")
                
                # Tentar modelo de fallback se disponível
                from evolux_engine.llms.model_router import ModelRouter, TaskCategory
                router = ModelRouter()
                fallback_model = router.get_fallback_model(self.executor_llm.model_name, TaskCategory.CODE_GENERATION)
                
                if fallback_model and fallback_model != self.executor_llm.model_name:
                    logger.info(f"Tentando modelo de fallback: {fallback_model}")
                    try:
                        # Criar cliente temporário para fallback
                        from evolux_engine.llms.llm_client import LLMClient
                        from evolux_engine.services.config_manager import ConfigManager
                        
                        config_manager = ConfigManager()
                        fallback_provider = router.available_models[fallback_model].provider
                        fallback_api_key = config_manager.get_api_key(fallback_provider)
                        
                        if fallback_api_key:
                            fallback_client = LLMClient(
                                provider=fallback_provider,
                                api_key=fallback_api_key,
                                model_name=fallback_model
                            )
                            
                            llm_response_text = await asyncio.wait_for(
                                fallback_client.generate_response(messages, max_tokens=2048, temperature=0.3),
                                timeout=60.0
                            )
                            logger.info(f"Sucesso com modelo de fallback: {fallback_model}")
                    except Exception as fallback_error:
                        logger.error(f"Fallback também falhou: {str(fallback_error)[:100]}...")
                
                if not llm_response_text:
                    raise e  # Re-raise original exception if fallback also failed
            latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # TODO: Registrar LLMCallMetrics no ProjectContext.iteration_history
            # Isso precisaria de acesso ao log da iteração atual, melhor feito pelo Orchestrator

            if not llm_response_text:
                logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Nenhuma resposta da LLM.")
                return None

            # Sanitiza a resposta primeiro
            sanitized_response = sanitize_llm_response(llm_response_text)
            logger.debug(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Resposta bruta LLM: {sanitized_response[:500]}...")

            # Usa a função avançada para extrair conteúdo
            content = extract_content_from_json_response(sanitized_response, expected_json_key)
            
            if content is not None:
                logger.info(f"Conteúdo extraído com sucesso para chave '{expected_json_key}' ({len(str(content))} caracteres)")
                return content
            
            # Fallback: tenta extrair JSON tradicionalmente
            json_str = extract_json_from_llm_response(sanitized_response)
            
            if json_str:
                try:
                    # Handle JSON with unicode characters properly
                    parsed_response = json.loads(json_str, strict=False)
                    if expected_json_key not in parsed_response:
                        error_msg = f"Chave '{expected_json_key}' não encontrada no JSON da LLM. Resposta: {json_str}"
                        logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                        return None
                    return parsed_response[expected_json_key]
                except json.JSONDecodeError as e:
                    error_msg = f"Falha ao decodificar JSON da LLM. Erro: {e}. JSON Tentado: {json_str[:500]}..."
                    logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                    return None
            else:
                # Fallback para CREATE_FILE/MODIFY_FILE se não for JSON, mas a LLM pode ter retornado conteúdo direto
                if expected_json_key in ["file_content", "modified_content"]:
                    logger.warning(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Resposta da LLM não é JSON, mas esperava '{expected_json_key}'. Usando resposta bruta como conteúdo.")
                    return sanitized_response
                
                error_msg = f"Nenhum JSON válido encontrado na resposta da LLM. Resposta: {sanitized_response[:500]}..."
                logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): {error_msg}")
                return None

        except asyncio.TimeoutError:
            logger.error(f"TaskExecutor (ID: {self.agent_id}, Ação: {action_description}): Timeout ao consultar LLM (60s).")
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

        # Use relative path for FileService (which handles workspace internally)
        relative_file_path = os.path.join("artifacts", details.file_path)
        
        # Construir contexto rico do projeto
        project_context_str = self._build_project_context(task)
        
        user_prompt = get_file_content_generation_prompt(
            file_path=details.file_path,
            guideline=details.content_guideline,
            project_goal=self.project_context.project_goal,
            project_type=self.project_context.project_type,
            existing_artifacts_summary=self.project_context.get_artifacts_structure_summary(),
            project_context=project_context_str
        )
        messages = [{"role": "system", "content": FILE_MANIPULATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]

        file_content = await self._invoke_llm_for_json_output(messages, "file_content", action_desc)

        if file_content is None:
            return ExecutionResult(exit_code=1, stderr=f"Falha ao gerar conteúdo da LLM para {details.file_path}.")

        try:
            self.file_service.save_file(relative_file_path, str(file_content)) # Garantir que é string
            artifact_change = ArtifactChange(path=relative_file_path, change_type=ArtifactChangeType.CREATED)
            file_hash = self.file_service.get_file_hash(relative_file_path)
            self.project_context.update_artifact_state(
                relative_file_path,
                ArtifactState(path=relative_file_path, hash=file_hash, summary=f"Arquivo criado/sobrescrito: {details.file_path}")
            )
            await self.project_context.save_context()
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} criado/atualizado.", artifacts_changed=[artifact_change])
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao salvar {relative_file_path}: {e}")
            return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo {details.file_path}: {e}")

    async def _execute_modify_file(self, task: Task) -> ExecutionResult:
        if not isinstance(task.details, TaskDetailsModifyFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa MODIFY_FILE inválidos.")
        details: TaskDetailsModifyFile = task.details

        action_desc = f"modificação de conteúdo para {details.file_path}"
        logger.info(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): {action_desc}")
        
        # Use relative path for FileService (which handles workspace internally)
        relative_file_path = os.path.join("artifacts", details.file_path)
        full_file_path = self.project_context.get_artifact_path(details.file_path)

        if not os.path.exists(full_file_path):
            return ExecutionResult(exit_code=1, stderr=f"Arquivo a ser modificado não encontrado: {details.file_path}")

        try:
            current_content = self.file_service.read_file(relative_file_path)
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
            old_hash = self.file_service.get_file_hash(relative_file_path)
            self.file_service.save_file(relative_file_path, str(modified_content))
            new_hash = self.file_service.get_file_hash(relative_file_path)
            artifact_change = ArtifactChange(path=relative_file_path, change_type=ArtifactChangeType.MODIFIED, old_hash=old_hash, new_hash=new_hash)
            
            self.project_context.update_artifact_state(
                relative_file_path,
                ArtifactState(path=relative_file_path, hash=new_hash, summary=f"Arquivo modificado: {details.file_path}")
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

        # Use relative path for FileService (which handles workspace internally)
        relative_file_path = os.path.join("artifacts", details.file_path)
        full_file_path = self.project_context.get_artifact_path(details.file_path)
        if not os.path.exists(full_file_path):
            logger.warning(f"TaskExecutor (ID: {self.agent_id}): Arquivo a ser deletado não existe: {full_file_path}. Considerando sucesso.")
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} já não existia.")
        
        try:
            old_hash = self.project_context.artifacts_state.get(relative_file_path, ArtifactState(path=relative_file_path)).hash
            self.file_service.delete_file(relative_file_path)
            artifact_change = ArtifactChange(path=relative_file_path, change_type=ArtifactChangeType.DELETED, old_hash=old_hash)
            
            self.project_context.remove_artifact_state(relative_file_path)
            await self.project_context.save_context()
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} deletado.", artifacts_changed=[artifact_change])
        except Exception as e:
            logger.opt(exception=True).error(f"TaskExecutor (ID: {self.agent_id}): Erro ao deletar arquivo {relative_file_path}: {e}")
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

        # Integração com SecurityGateway para validação de comando
        if self.security_gateway:
            try:
                is_safe = await self.security_gateway.is_command_safe(command_to_execute, details.working_directory)
                if not is_safe:
                    logger.error(f"TaskExecutor: Comando '{command_to_execute}' bloqueado pelo SecurityGateway.")
                    return ExecutionResult(command_executed=command_to_execute, exit_code=1, stderr="Comando bloqueado por razões de segurança.")
            except Exception as e:
                logger.warning(f"Erro no SecurityGateway, permitindo comando: {e}")
                # Em caso de erro no gateway, ser permissivo mas logar

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

            # Usar SecureExecutor se disponível, senão fallback para shell_service
            if self.secure_executor:
                try:
                    shell_result = await self.secure_executor.execute_secure_command(
                        command_to_execute,
                        working_directory=working_dir,
                        timeout_seconds=details.timeout_seconds
                    )
                except Exception as e:
                    logger.warning(f"Erro no SecureExecutor, usando shell_service: {e}")
                    shell_result = await self.shell_service.execute_command(
                        command_to_execute,
                        working_directory=working_dir,
                        timeout=details.timeout_seconds
                    )
            else:
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
                    relative_artifact_path = os.path.join("artifacts", artifact_path_rel)
                    if os.path.exists(full_artifact_path):
                        new_hash = self.file_service.get_file_hash(relative_artifact_path)
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


    async def execute_task(self, task: Task, use_refinement: bool = None) -> ExecutionResult:
        """
        Executa uma tarefa com base no seu tipo, opcionalmente usando refinamento iterativo.
        """
        logger.info(
            f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Iniciando execução - Tipo: {task.type.value}, Desc: {task.description}"
        )
        
        if not task.details:
            logger.error(f"TaskExecutor (ID: {self.agent_id}, Tarefa: {task.task_id}): Tarefa não possui detalhes. Não pode ser executada.")
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa ausentes.")

        # Determinar se deve usar refinamento
        should_refine = (
            use_refinement if use_refinement is not None 
            else self.enable_refinement and self.iterative_refiner is not None
        )
        
        # Executar com refinamento iterativo se habilitado
        if should_refine and self._should_use_refinement_for_task(task):
            logger.info(f"Using iterative refinement for task {task.task_id}")
            return await self._execute_with_refinement(task)
        
        # Execução padrão
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
        
        return execution_result
    
    def _should_use_refinement_for_task(self, task: Task) -> bool:
        """
        Determina se uma tarefa deve usar refinamento iterativo baseado em sua complexidade.
        """
        # Usar refinamento para tarefas críticas ou complexas
        complex_keywords = [
            "api", "database", "authentication", "security", "algorithm", 
            "optimization", "performance", "integration", "architecture"
        ]
        
        task_desc_lower = task.description.lower()
        is_complex = any(keyword in task_desc_lower for keyword in complex_keywords)
        
        # Sempre usar refinamento para CREATE_FILE e MODIFY_FILE de código crítico
        is_code_task = task.type in [TaskType.CREATE_FILE, TaskType.MODIFY_FILE]
        
        return is_complex or is_code_task
    
    async def _execute_with_refinement(self, task: Task) -> ExecutionResult:
        """
        Executa tarefa usando refinamento iterativo.
        """
        try:
            # Determinar estratégia de refinamento baseada no tipo de tarefa
            if task.type in [TaskType.CREATE_FILE, TaskType.MODIFY_FILE]:
                strategy = RefinementStrategy.ITERATIVE_IMPROVEMENT
            elif task.type == TaskType.EXECUTE_COMMAND:
                strategy = RefinementStrategy.CROSS_VALIDATION  
            else:
                strategy = RefinementStrategy.SINGLE_PASS
            
            # Executar refinamento
            refinement_result = await self.iterative_refiner.refine_task_iteratively(
                task, strategy
            )
            
            # Log do resultado do refinamento
            logger.info(
                f"Refinement completed for task {task.task_id}: "
                f"{refinement_result.total_iterations} iterations, "
                f"final score: {refinement_result.final_quality_score:.2f}, "
                f"converged: {refinement_result.convergence_achieved}"
            )
            
            return refinement_result.final_result
            
        except Exception as e:
            logger.error(f"Error in iterative refinement: {e}")
            # Fallback para execução padrão
            return await self._execute_standard_task(task)
    
    async def _execute_standard_task(self, task: Task) -> ExecutionResult:
        """
        Executa tarefa usando método padrão (sem refinamento).
        """
        exec_func_map = {
            TaskType.CREATE_FILE: self._execute_create_file,
            TaskType.MODIFY_FILE: self._execute_modify_file,
            TaskType.DELETE_FILE: self._execute_delete_file,
            TaskType.EXECUTE_COMMAND: self._execute_command,
        }
        
        if task.type in exec_func_map:
            return await exec_func_map[task.type](task)
        else:
            return ExecutionResult(
                command_executed=task.description,
                exit_code=1,
                stderr=f"Tipo de tarefa não suportado: {task.type.value}"
            )

