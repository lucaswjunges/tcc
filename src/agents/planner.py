import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
import os
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define os tipos de task com descrição
class TaskType(Enum):
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    EXECUTE_COMMAND = "execute_command"
    VALIDATE_ARTIFACT = "validate_artifact"
    PLAN_SUB_TASKS = "plan_sub_tasks"

@dataclass
class TaskDetails:
    """Base class for task details"""
    pass

@dataclass
class CreateFileDetails(TaskDetails):
    file_path: str
    content_guideline: str
    overwrite: bool = False

@dataclass
class ModifyFileDetails(TaskDetails):
    file_path: str
    modification_guideline: str
    section_to_modify: Optional[str] = None
    existing_content_context: Optional[str] = None

@dataclass
class ExecuteCommandDetails(TaskDetails):
    command_description: str
    target_path: Optional[str] = None
    environment: Optional[Dict] = field(default_factory=dict)

@dataclass
class ValidateArtifactDetails(TaskDetails):
    artifact_id: str
    validation_criteria: str
    expected_constraints: Optional[Dict] = field(default_factory=dict)

@dataclass
class PlanSubTasksDetails(TaskDetails):
    main_task_description: str
    context_summary: str
    expected_subtask_count: Optional[int] = 2

@dataclass
class Dependency:
    task_id: str
    depends_on: str  # 'after' ou 'before'

class Task:
    def __init__(self, task_id: str, description: str, task_type: TaskType, details: TaskDetails):
        self.task_id = task_id
        self.description = description
        self.type = task_type
        self.details = details
        self.dependencies = []
        self.status = "pending"
        self.acceptance_criteria = self._generate_default_criteria()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    @property
    def default_path(self) -> str:
        raise NotImplementedError("Subclasses must implement this")

    def _generate_default_criteria(self) -> str:
        return f"Tarefa '{self.description}' realizada com sucesso e documentação atualizada"

    def add_dependency(self, dependency_id: str):
        self.dependencies.append(Dependency(task_id=self.task_id, depends_on=dependency_id))

    def mark_complete(self):
        self.status = "completed"
        self.end_time = datetime.now()

class PlannerAgent:
    """Classe responsável por gerenciar a criação e o fluxo de tarefas"""
    def __init__(self, context_manager, task_db, artifact_store):
        self.context_manager = context_manager
        self.task_db = task_db
        self.artifact_store = artifact_store
        self.active_tasks = {}
        self.next_task_id = self._generate_next_id()
        logger.info("PlannerAgent inicializado com componentes necessários")

    def _generate_next_id(self) -> str:
        """Gera um ID sequencial único"""
        return str(uuid.uuid4())

    async def generate_tasks_from_blueprint(self, blueprint_name: str) -> List[Task]:
        """Baseado em um blueprint, gera um conjunto de tarefas"""
        blueprint = await self.context_manager.get_blueprint(blueprint_name)
        if not blueprint:
            raise ValueError(f"Blueprint '{blueprint_name}' não encontrado")

        tasks = []
        # Implementação para mapear blueprint para tasks...
        
        # Exemplo simplificado
        tasks.append(Task(
            task_id=self.next_task_id(),
            description=f"Criar estrutura inicial para {blueprint_name}",
            type=TaskType.CREATE_FILE,
            details=CreateFileDetails(
                file_path="src/project_structure.json",
                content_guideline="Definir estrutura base conforme blueprint solicitado"
            )
        ))
        
        self.next_task_id += 1
        return tasks

    def get_pending_tasks(self) -> List[Task]:
        """Retorna todas as tarefas pendentes"""
        pending = [task for task_id, task in self.active_tasks.items() if task.status == "pending"]
        return sorted(pending, key=lambda t: t.description)

    def get_completed_tasks(self) -> List[Task]:
        """Retorna todas as tarefas concluídas"""
        return [task for task_id, task in self.active_tasks.items() if task.status in ["completed", "failed"]]

    def _resolve_dependency_chain(self, task_id: str) -> bool:
        """Verifica se todas as dependências de uma task estão concluídas"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        for dep in task.dependencies:
            if dep.depends_on not in self.active_tasks:
                continue
            if self.active_tasks[dep.depends_on].status != "completed":
                return False
        return True

    async def execute_task(self, task_id: str) -> Union[bool, Exception]:
        """Executa uma tarefa específica e atualiza seu status"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False, ValueError("Tarefa não encontrada")

        logger.info(f"Executando tarefa {task_id}: {task.description}")
        task.start_time = datetime.now()

        try:
            if task.type == TaskType.CREATE_FILE:
                await self._execute_create_file_task(task)
            elif task.type == TaskType.MODIFY_FILE:
                await self._execute_modify_file_task(task)
            # ... outros tipos similarmente

            task.mark_complete()
            return True, None
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task_id}: {str(e)}")
            task.status = "failed"
            return False, e

    async def manage_workflow(self) -> Tuple[bool, str]:
        """Gera e gerencia o fluxo de trabalho através das tarefas"""
        active_context = self.context_manager.get_active_context()
        if not active_context:
            logger.error("Nenhum contexto ativo encontrado para planejamento")
            return False, "Contexto não configurado"

        tasks_to_run = self.get_pending_tasks()
        if not tasks_to_run:
            logger.info("Nenhuma tarefa pendente disponível")
            return False, "Nenhuma tarefa para executar"

        # Executa todas as tarefas pendentes
        success_count = 0
        for task in tasks_to_run:
            task_id = task.task_id
            success, error = await self.execute_task(task_id)
            if not success:
                logger.error(f"Falha na execução de {task_id}: {str(error)}")
                # Gera tarefa de fallback
                await self.recover_problematic_task(task, str(error))
            else:
                success_count += 1

        return True, f"{success_count}/{len(tasks_to_run)} tarefas concluídas"

    async def recover_problematic_task(self, original_task: Task, error_details: str) -> bool:
        """Recupera problemas identificados durante a execução de uma tarefa"""
        recovery_prompt = f"""
        Contexto: Tarefa falhou com o seguinte erro:
        {error_details}

        Por favor, sugira as ações necessárias para corrigir este problema.
        Você pode:
        - Propor uma nova tarefa específica para correção
        - Identificar dependência faltante
        - Sugerir modificação em tarefa existente
        """

        response = await self.get_ai_suggestion(recovery_prompt)
        if "nova_tarefa" in response.lower():
            # Processar sugestão de nova tarefa
            return self.create_recovery_task(response, error_details)
        elif "dependência" in response.lower():
            # Processar dependência faltante
            return self.fix_dependency_error(original_task.task_id)
        # ... outros casos...

    async def get_ai_suggestion(self, context: str) -> str:
        """Utiliza IA para obter sugestões de recuperação baseadas no contexto"""
        # Implementação para chamar API de IA ou service externo
        return "Sugestão de recuperação baseada na análise do erro"

    async def create_recovery_task(self, suggestion: str, error: str) -> bool:
        """Cria uma tarefa específica para rejuvenescer o contexto atual"""
        task_id = self.next_task_id()
        
        # Analisa a sugestão para determinar o tipo de tarefa
        task_type = self._identify_task_type_from_suggestion(suggestion)
        
        # Cria estrutura de details com base no tipo
        details = self._create_task_details_from_suggestion(task_type, error, suggestion)
        
        # Cria uma nova tarefa de recuperação
        recovery_task = Task(
            task_id=task_id,
            description=f"Recuperação automática de erro: {error[:50]}...",
            type=task_type,
            details=details
        )
        
        self.active_tasks[task_id] = recovery_task
        logger.info(f"Tarefa de recuperação criada: {recovery_task.task_id}")
        return True

    def _identify_task_type_from_suggestion(self, suggestion: str) -> TaskType:
        """Determina o tipo de task baseado na sugestão de recuperação"""
        # Lógica para mapear palavras-chave na sugestão para tipos específicos
        if any(word in suggestion.lower() for word in ["corrigir", "reparar", "corrigir"]):
            return TaskType.MODIFY_FILE
        elif "criar" in suggestion.lower() or "novo" in suggestion.lower():
            return TaskType.CREATE_FILE
        else:
            return TaskType.EXECUTE_COMMAND

    def _create_task_details_from_suggestion(self, task_type: TaskType, error: str, suggestion: str) -> TaskDetails:
        """Cria um objeto de detalhes de task baseado na sugestão e erro"""
        # Baseado no tipo de task identificado, cria os detalhes específicos
        if task_type == TaskType.CREATE_FILE:
            return CreateFileDetails(
                file_path=self._define_recovery_path(error),
                content_guideline=f" Corrigir o erro: {error[:80]}"
            )
        # ... outros tipos similarmente

    def _define_recovery_path(self, error: str) -> str:
        """Determina o caminho do arquivo para ação de recuperação"""
        # Lógica para identificar o arquivo relevante para recuperação
        return "src/recovery.patch"
