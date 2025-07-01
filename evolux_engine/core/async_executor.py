# Async Task Executor com execução concorrente e otimizada

import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional, List, Union
import time
from dataclasses import dataclass

from loguru import logger
from evolux_engine.utils.string_utils import extract_json_from_llm_response, sanitize_llm_response, extract_content_from_json_response

from evolux_engine.llms.async_llm_client import AsyncLLMClient, LLMRequest
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
    TaskDetailsValidateArtifact,
    TaskDetailsAnalyzeOutput,
    TaskDetailsPlanSubTasks,
    TaskDetailsHumanInterventionRequired,
    TaskDetailsGenericLLMQuery,
    LLMCallMetrics,
)
from evolux_engine.services.async_file_service import AsyncFileService, FileOperationResult
from evolux_engine.services.shell_service import ShellService
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
)

@dataclass
class AsyncExecutionMetrics:
    """Métricas de execução assíncrona"""
    total_executions: int = 0
    concurrent_executions: int = 0
    avg_execution_time_ms: float = 0.0
    file_operations: int = 0
    llm_calls: int = 0
    cache_hits: int = 0
    errors: int = 0

class AsyncTaskExecutorAgent:
    """
    Executor de tarefas assíncrono com recursos avançados:
    - Execução concorrente de múltiplas tarefas
    - File I/O não-bloqueante
    - LLM calls otimizados com cache
    - Batch processing para operações similares
    - Métricas detalhadas de performance
    """

    def __init__(
        self,
        async_llm_client: AsyncLLMClient,
        project_context: ProjectContext,
        async_file_service: AsyncFileService,
        shell_service: ShellService,
        security_gateway: Optional[SecurityGateway] = None,
        secure_executor: Optional[SecureExecutor] = None,
        model_router: Optional[ModelRouter] = None,
        agent_id: str = "async_task_executor",
        max_concurrent_tasks: int = 10
    ):
        self.async_llm = async_llm_client
        self.project_context = project_context
        self.async_file_service = async_file_service
        self.shell_service = shell_service
        self.security_gateway = security_gateway
        self.secure_executor = secure_executor
        self.model_router = model_router
        self.agent_id = agent_id
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Controle de concorrência
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Métricas
        self.metrics = AsyncExecutionMetrics()
        
        # Cache de contexto para reutilização
        self._context_cache = {}
        self._context_cache_time = 0
        
        logger.info(
            f"AsyncTaskExecutorAgent (ID: {self.agent_id}) inicializado",
            project_id=self.project_context.project_id,
            max_concurrent=max_concurrent_tasks
        )

    async def _build_project_context_async(self, task: Task) -> str:
        """Constrói contexto rico do projeto de forma assíncrona com cache"""
        
        # Verificar cache (válido por 60 segundos)
        current_time = time.time()
        if (current_time - self._context_cache_time) < 60 and self._context_cache:
            return self._context_cache.get('context', '')
        
        context_parts = []
        
        # Objetivo do projeto
        context_parts.append(f"OBJETIVO DO PROJETO: {self.project_context.project_goal}")
        
        # Tipo de projeto
        if self.project_context.project_type:
            context_parts.append(f"TIPO: {self.project_context.project_type}")
        
        # Arquivos existentes (de forma assíncrona)
        existing_files = await self._get_existing_files_summary_async()
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
        
        context = "\n\n".join(context_parts)
        
        # Atualizar cache
        self._context_cache = {'context': context}
        self._context_cache_time = current_time
        
        return context

    async def _get_existing_files_summary_async(self) -> str:
        """Retorna resumo dos arquivos existentes de forma assíncrona"""
        if not self.project_context.artifacts_state:
            return "Nenhum arquivo criado ainda."
        
        summary_lines = []
        
        # Buscar arquivos de forma assíncrona
        file_tasks = []
        for file_path, artifact_state in self.project_context.artifacts_state.items():
            summary_lines.append(f"- {file_path}")
            
            # Criar tarefa para ler arquivo pequeno
            if file_path.endswith('.py'):
                file_tasks.append(self._analyze_file_async(file_path))
        
        # Executar análises de arquivo concorrentemente
        if file_tasks:
            file_analyses = await asyncio.gather(*file_tasks, return_exceptions=True)
            
            for i, analysis in enumerate(file_analyses):
                if isinstance(analysis, str) and analysis:
                    summary_lines.append(analysis)
        
        return '\n'.join(summary_lines)

    async def _analyze_file_async(self, file_path: str) -> str:
        """Analisa um arquivo de forma assíncrona"""
        try:
            # Verificar tamanho primeiro
            stats = await self.async_file_service.get_file_stats(file_path)
            if not stats['exists'] or stats.get('size', 0) > 1000:
                return ""
            
            # Ler conteúdo
            content, result = await self.async_file_service.read_file(file_path)
            if not result.success or not content:
                return ""
            
            if file_path.endswith('.py'):
                # Extrair imports e classes/funções principais
                lines = content.split('\n')
                imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
                classes = [line.strip() for line in lines if line.strip().startswith('class ')]
                functions = [line.strip() for line in lines if line.strip().startswith('def ')]
                
                analysis_parts = []
                if imports:
                    analysis_parts.append(f"  Imports: {', '.join(imports[:3])}")
                if classes:
                    analysis_parts.append(f"  Classes: {', '.join([c.split('(')[0].replace('class ', '') for c in classes])}")
                if functions:
                    analysis_parts.append(f"  Funções: {', '.join([f.split('(')[0].replace('def ', '') for f in functions[:3]])}")
                
                return '\n'.join(analysis_parts)
            
            return ""
        except:
            return ""

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

    async def _invoke_llm_for_json_output_async(
        self,
        messages: List[Dict[str, str]],
        expected_json_key: str,
        action_description: str
    ) -> Optional[Any]:
        """
        Invoca o LLM de forma assíncrona esperando uma resposta JSON
        """
        
        try:
            start_time = time.time()
            
            # Criar request LLM
            llm_request = LLMRequest(
                messages=messages,
                model=self.async_llm.model_name,
                max_tokens=2048,
                temperature=0.3,
                timeout=60.0
            )
            
            # Fazer chamada assíncrona
            response = await self.async_llm.generate_response_detailed(llm_request)
            
            if not response.success:
                logger.error(f"LLM request failed: {response.error}")
                return None
            
            # Atualizar métricas
            self.metrics.llm_calls += 1
            if response.from_cache:
                self.metrics.cache_hits += 1
            
            latency_ms = response.latency_ms
            logger.debug(f"LLM response received",
                        action=action_description,
                        latency_ms=latency_ms,
                        tokens=response.tokens_used,
                        from_cache=response.from_cache)
            
            # Processar resposta
            content = extract_content_from_json_response(response.content, expected_json_key)
            
            if content is not None:
                logger.info(f"Conteúdo extraído com sucesso para chave '{expected_json_key}' ({len(str(content))} caracteres)")
                return content
            
            # Fallback: tenta extrair JSON tradicionalmente
            json_str = extract_json_from_llm_response(response.content)
            
            if json_str:
                try:
                    parsed_response = json.loads(json_str, strict=False)
                    if expected_json_key not in parsed_response:
                        logger.error(f"Chave '{expected_json_key}' não encontrada no JSON da LLM")
                        return None
                    return parsed_response[expected_json_key]
                except json.JSONDecodeError as e:
                    logger.error(f"Falha ao decodificar JSON da LLM: {e}")
                    return None
            else:
                # Fallback para CREATE_FILE/MODIFY_FILE se não for JSON, mas a LLM pode ter retornado conteúdo direto
                if expected_json_key in ["file_content", "modified_content"]:
                    logger.warning(f"Resposta da LLM não é JSON, usando resposta bruta como conteúdo")
                    return response.content
                
                logger.error(f"Nenhum JSON válido encontrado na resposta da LLM")
                return None

        except Exception as e:
            logger.error(f"Erro inesperado ao consultar LLM: {str(e)}")
            self.metrics.errors += 1
            return None

    async def _execute_create_file_async(self, task: Task) -> ExecutionResult:
        """Executa criação de arquivo de forma assíncrona"""
        if not isinstance(task.details, TaskDetailsCreateFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa CREATE_FILE inválidos.")
        
        details: TaskDetailsCreateFile = task.details
        action_desc = f"geração de conteúdo para {details.file_path}"
        logger.info(f"AsyncTaskExecutor: {action_desc}")

        # Construir contexto de forma assíncrona
        project_context_str = await self._build_project_context_async(task)
        
        user_prompt = get_file_content_generation_prompt(
            file_path=details.file_path,
            guideline=details.content_guideline,
            project_goal=self.project_context.project_goal,
            project_type=self.project_context.project_type,
            existing_artifacts_summary=self.project_context.get_artifacts_structure_summary(),
            project_context=project_context_str
        )
        
        messages = [
            {"role": "system", "content": FILE_MANIPULATION_SYSTEM_PROMPT}, 
            {"role": "user", "content": user_prompt}
        ]

        # Gerar conteúdo assincronamente
        file_content = await self._invoke_llm_for_json_output_async(messages, "file_content", action_desc)

        if file_content is None:
            return ExecutionResult(exit_code=1, stderr=f"Falha ao gerar conteúdo da LLM para {details.file_path}.")

        try:
            # Escrever arquivo de forma assíncrona
            file_result = await self.async_file_service.write_file(details.file_path, str(file_content))
            
            self.metrics.file_operations += 1
            
            if not file_result.success:
                return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo {details.file_path}: {file_result.error}")
            
            # Atualizar estado do artefato
            artifact_change = ArtifactChange(path=details.file_path, change_type=ArtifactChangeType.CREATED)
            
            # Calcular hash de forma assíncrona
            hash_value, hash_result = await self.async_file_service.get_file_hash(details.file_path)
            
            self.project_context.update_artifact_state(
                details.file_path,
                ArtifactState(
                    path=details.file_path, 
                    hash=hash_value if hash_result.success else "", 
                    summary=f"Arquivo criado: {details.file_path}"
                )
            )
            
            await self.project_context.save_context()
            
            return ExecutionResult(
                exit_code=0, 
                stdout=f"Arquivo {details.file_path} criado/atualizado.", 
                artifacts_changed=[artifact_change]
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo {details.file_path}: {e}")
            self.metrics.errors += 1
            return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo {details.file_path}: {e}")

    async def _execute_modify_file_async(self, task: Task) -> ExecutionResult:
        """Executa modificação de arquivo de forma assíncrona"""
        if not isinstance(task.details, TaskDetailsModifyFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa MODIFY_FILE inválidos.")
        
        details: TaskDetailsModifyFile = task.details
        action_desc = f"modificação de conteúdo para {details.file_path}"
        logger.info(f"AsyncTaskExecutor: {action_desc}")

        # Verificar se arquivo existe
        exists = await self.async_file_service.file_exists(details.file_path)
        if not exists:
            return ExecutionResult(exit_code=1, stderr=f"Arquivo a ser modificado não encontrado: {details.file_path}")

        try:
            # Ler arquivo atual de forma assíncrona
            current_content, read_result = await self.async_file_service.read_file(details.file_path)
            
            if not read_result.success:
                return ExecutionResult(exit_code=1, stderr=f"Erro ao ler arquivo {details.file_path}: {read_result.error}")

            user_prompt = get_file_modification_prompt(
                file_path=details.file_path,
                current_content=current_content,
                guideline=details.modification_guideline,
                project_goal=self.project_context.project_goal,
                project_type=self.project_context.project_type
            )
            
            messages = [
                {"role": "system", "content": FILE_MANIPULATION_SYSTEM_PROMPT}, 
                {"role": "user", "content": user_prompt}
            ]
            
            # Gerar conteúdo modificado
            modified_content = await self._invoke_llm_for_json_output_async(messages, "modified_content", action_desc)

            if modified_content is None:
                return ExecutionResult(exit_code=1, stderr=f"Falha ao gerar conteúdo modificado da LLM para {details.file_path}.")

            # Calcular hash antigo
            old_hash, _ = await self.async_file_service.get_file_hash(details.file_path)
            
            # Escrever arquivo modificado
            write_result = await self.async_file_service.write_file(details.file_path, str(modified_content))
            
            self.metrics.file_operations += 1
            
            if not write_result.success:
                return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo modificado {details.file_path}: {write_result.error}")
            
            # Calcular novo hash
            new_hash, _ = await self.async_file_service.get_file_hash(details.file_path)
            
            artifact_change = ArtifactChange(
                path=details.file_path, 
                change_type=ArtifactChangeType.MODIFIED, 
                old_hash=old_hash, 
                new_hash=new_hash
            )
            
            self.project_context.update_artifact_state(
                details.file_path,
                ArtifactState(
                    path=details.file_path, 
                    hash=new_hash, 
                    summary=f"Arquivo modificado: {details.file_path}"
                )
            )
            
            await self.project_context.save_context()
            
            return ExecutionResult(
                exit_code=0, 
                stdout=f"Arquivo {details.file_path} modificado.", 
                artifacts_changed=[artifact_change]
            )
            
        except Exception as e:
            logger.error(f"Erro ao modificar arquivo {details.file_path}: {e}")
            self.metrics.errors += 1
            return ExecutionResult(exit_code=1, stderr=f"Erro ao salvar arquivo modificado {details.file_path}: {e}")

    async def _execute_delete_file_async(self, task: Task) -> ExecutionResult:
        """Executa deleção de arquivo de forma assíncrona"""
        if not isinstance(task.details, TaskDetailsDeleteFile):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa DELETE_FILE inválidos.")
        
        details: TaskDetailsDeleteFile = task.details
        action_desc = f"deleção do arquivo {details.file_path}"
        logger.info(f"AsyncTaskExecutor: {action_desc}")

        # Verificar se arquivo existe
        exists = await self.async_file_service.file_exists(details.file_path)
        if not exists:
            logger.warning(f"Arquivo a ser deletado não existe: {details.file_path}. Considerando sucesso.")
            return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} já não existia.")
        
        try:
            # Obter hash antes da deleção
            old_hash = self.project_context.artifacts_state.get(
                details.file_path, 
                ArtifactState(path=details.file_path)
            ).hash
            
            # Deletar arquivo
            delete_result = await self.async_file_service.delete_file(details.file_path)
            
            self.metrics.file_operations += 1
            
            if not delete_result.success:
                return ExecutionResult(exit_code=1, stderr=f"Erro ao deletar arquivo {details.file_path}: {delete_result.error}")
            
            artifact_change = ArtifactChange(
                path=details.file_path, 
                change_type=ArtifactChangeType.DELETED, 
                old_hash=old_hash
            )
            
            self.project_context.remove_artifact_state(details.file_path)
            await self.project_context.save_context()
            
            return ExecutionResult(
                exit_code=0, 
                stdout=f"Arquivo {details.file_path} deletado.", 
                artifacts_changed=[artifact_change]
            )
            
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {details.file_path}: {e}")
            self.metrics.errors += 1
            return ExecutionResult(exit_code=1, stderr=f"Erro ao deletar arquivo {details.file_path}: {e}")

    async def _execute_command_async(self, task: Task) -> ExecutionResult:
        """Executa comando de forma assíncrona com validação de segurança"""
        if not isinstance(task.details, TaskDetailsExecuteCommand):
            return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa EXECUTE_COMMAND inválidos.")
        
        details: TaskDetailsExecuteCommand = task.details
        action_desc = f"geração de comando para: {details.command_description}"
        logger.info(f"AsyncTaskExecutor: {action_desc}")

        user_prompt = get_command_generation_prompt(
            command_description=details.command_description,
            expected_outcome=details.expected_outcome,
            project_artifacts_structure=self.project_context.get_artifacts_structure_summary()
        )
        
        messages = [
            {"role": "system", "content": COMMAND_GENERATION_SYSTEM_PROMPT}, 
            {"role": "user", "content": user_prompt}
        ]

        # Gerar comando
        command_to_execute = await self._invoke_llm_for_json_output_async(messages, "command_to_execute", action_desc)

        if not command_to_execute or not isinstance(command_to_execute, str):
            return ExecutionResult(exit_code=1, stderr="Falha ao gerar comando da LLM.", command_executed=details.command_description)
        
        logger.info(f"Comando gerado pela LLM: '{command_to_execute}'")

        # Validação de segurança assíncrona
        if self.security_gateway:
            try:
                is_safe = await self.security_gateway.is_command_safe(command_to_execute, details.working_directory)
                if not is_safe:
                    logger.error(f"Comando '{command_to_execute}' bloqueado pelo SecurityGateway.")
                    return ExecutionResult(
                        command_executed=command_to_execute, 
                        exit_code=1, 
                        stderr="Comando bloqueado por razões de segurança."
                    )
            except Exception as e:
                logger.warning(f"Erro no SecurityGateway, permitindo comando: {e}")

        try:
            # Determinar diretório de trabalho
            working_dir = self.project_context.get_project_path("artifacts")
            if details.working_directory:
                safe_subdir = os.path.normpath(os.path.join("/", details.working_directory)).lstrip("/")
                working_dir = os.path.join(working_dir, safe_subdir)

            if not os.path.exists(working_dir):
                os.makedirs(working_dir, exist_ok=True)
            
            # Executar comando (usando shell_service que já é otimizado)
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
            
            # Detectar mudanças em artefatos (de forma assíncrona)
            artifacts_changed: List[ArtifactChange] = []
            if shell_result["exit_code"] == 0:
                artifacts_changed = await self._detect_artifact_changes_async()
            
            return ExecutionResult(
                command_executed=command_to_execute,
                exit_code=shell_result["exit_code"],
                stdout=shell_result["stdout"],
                stderr=shell_result["stderr"],
                artifacts_changed=artifacts_changed,
            )
            
        except Exception as e:
            logger.error(f"Erro ao executar comando '{command_to_execute}': {e}")
            self.metrics.errors += 1
            return ExecutionResult(
                command_executed=command_to_execute, 
                exit_code=1, 
                stderr=f"Erro ao executar comando: {e}"
            )

    async def _detect_artifact_changes_async(self) -> List[ArtifactChange]:
        """Detecta mudanças em artefatos de forma assíncrona"""
        artifacts_changed = []
        
        try:
            # Obter lista atual de arquivos
            current_files, list_result = await self.async_file_service.list_files_async("artifacts")
            
            if not list_result.success:
                return artifacts_changed
            
            # Verificar mudanças em arquivos conhecidos
            check_tasks = []
            for artifact_path_rel, artifact_state_obj in list(self.project_context.artifacts_state.items()):
                check_tasks.append(self._check_file_changes_async(artifact_path_rel, artifact_state_obj))
            
            # Executar verificações concorrentemente
            if check_tasks:
                changes = await asyncio.gather(*check_tasks, return_exceptions=True)
                for change in changes:
                    if isinstance(change, ArtifactChange):
                        artifacts_changed.append(change)
            
            # Detectar arquivos novos
            known_files = set(self.project_context.artifacts_state.keys())
            current_files_set = set(current_files)
            new_files = current_files_set - known_files
            
            for new_file in new_files:
                if new_file.startswith('artifacts/'):
                    rel_path = new_file[10:]  # Remove 'artifacts/' prefix
                    hash_value, _ = await self.async_file_service.get_file_hash(new_file)
                    
                    artifacts_changed.append(ArtifactChange(
                        path=rel_path,
                        change_type=ArtifactChangeType.CREATED,
                        new_hash=hash_value
                    ))
                    
                    # Atualizar estado
                    self.project_context.update_artifact_state(
                        rel_path,
                        ArtifactState(
                            path=rel_path, 
                            hash=hash_value, 
                            summary=f"Arquivo criado por comando"
                        )
                    )
            
            if artifacts_changed:
                await self.project_context.save_context()
            
        except Exception as e:
            logger.error(f"Erro ao detectar mudanças em artefatos: {e}")
        
        return artifacts_changed

    async def _check_file_changes_async(self, artifact_path_rel: str, artifact_state_obj: ArtifactState) -> Optional[ArtifactChange]:
        """Verifica mudanças em um arquivo específico"""
        try:
            exists = await self.async_file_service.file_exists(f"artifacts/{artifact_path_rel}")
            
            if exists:
                new_hash, hash_result = await self.async_file_service.get_file_hash(f"artifacts/{artifact_path_rel}")
                
                if hash_result.success and new_hash != artifact_state_obj.hash:
                    # Arquivo foi modificado
                    self.project_context.update_artifact_state(
                        artifact_path_rel,
                        ArtifactState(
                            path=artifact_path_rel, 
                            hash=new_hash, 
                            summary=f"Modificado por comando"
                        )
                    )
                    
                    return ArtifactChange(
                        path=artifact_path_rel,
                        change_type=ArtifactChangeType.MODIFIED,
                        old_hash=artifact_state_obj.hash,
                        new_hash=new_hash
                    )
            else:
                # Arquivo foi deletado
                self.project_context.remove_artifact_state(artifact_path_rel)
                
                return ArtifactChange(
                    path=artifact_path_rel,
                    change_type=ArtifactChangeType.DELETED,
                    old_hash=artifact_state_obj.hash
                )
        except Exception as e:
            logger.error(f"Erro ao verificar mudanças no arquivo {artifact_path_rel}: {e}")
        
        return None

    async def execute_task_async(self, task: Task) -> ExecutionResult:
        """
        Executa uma tarefa de forma assíncrona com controle de concorrência
        """
        async with self.task_semaphore:
            start_time = time.time()
            self.metrics.total_executions += 1
            self.metrics.concurrent_executions += 1
            
            try:
                logger.info(f"AsyncTaskExecutor: Executando tarefa {task.task_id} - {task.type.value}")
                
                if not task.details:
                    return ExecutionResult(exit_code=1, stderr="Detalhes da tarefa ausentes.")

                # Mapeamento de tipos para executores assíncronos
                async_exec_map = {
                    TaskType.CREATE_FILE: self._execute_create_file_async,
                    TaskType.MODIFY_FILE: self._execute_modify_file_async,
                    TaskType.DELETE_FILE: self._execute_delete_file_async,
                    TaskType.EXECUTE_COMMAND: self._execute_command_async,
                }

                if task.type in async_exec_map:
                    result = await async_exec_map[task.type](task)
                else:
                    logger.error(f"Tipo de tarefa não suportado: {task.type.value}")
                    result = ExecutionResult(
                        command_executed=task.description,
                        exit_code=1,
                        stderr=f"Tipo de tarefa não suportado: {task.type.value}",
                    )
                
                # Atualizar métricas
                execution_time = (time.time() - start_time) * 1000
                self.metrics.avg_execution_time_ms = (
                    (self.metrics.avg_execution_time_ms * (self.metrics.total_executions - 1) + execution_time) /
                    self.metrics.total_executions
                )
                
                logger.info(f"Tarefa {task.task_id} executada",
                           success=result.exit_code == 0,
                           execution_time_ms=execution_time)
                
                return result
                
            except Exception as e:
                logger.error(f"Erro na execução da tarefa {task.task_id}: {str(e)}")
                self.metrics.errors += 1
                return ExecutionResult(
                    command_executed=task.description,
                    exit_code=1,
                    stderr=f"Erro na execução: {str(e)}"
                )
            finally:
                self.metrics.concurrent_executions -= 1

    async def batch_execute_tasks(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Executa múltiplas tarefas em batch com concorrência controlada"""
        
        logger.info(f"Executando batch de {len(tasks)} tarefas", 
                   max_concurrent=self.max_concurrent_tasks)
        
        # Executar todas as tarefas concorrentemente
        results = await asyncio.gather(
            *[self.execute_task_async(task) for task in tasks],
            return_exceptions=True
        )
        
        # Processar resultados
        execution_results = []
        successful = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_results.append(ExecutionResult(
                    command_executed=tasks[i].description,
                    exit_code=1,
                    stderr=f"Exceção durante execução: {str(result)}"
                ))
            else:
                execution_results.append(result)
                if result.exit_code == 0:
                    successful += 1
        
        logger.info(f"Batch execution completed",
                   total=len(tasks),
                   successful=successful,
                   success_rate=successful/len(tasks))
        
        return execution_results

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        return {
            **self.metrics.__dict__,
            'agent_id': self.agent_id,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'current_concurrent': self.metrics.concurrent_executions
        }