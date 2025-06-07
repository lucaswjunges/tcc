# src/services/context_manager.py

import uuid
import json
from pathlib import Path
from datetime import datetime

# AQUI ESTÁ A CHAVE: Nós IMPORTAMOS as classes, não as definimos aqui.
from src.schemas.contracts import ProjectContext, Task
from src.services.observability_service import log

class ContextManager:
    """Gerencia o estado e o workspace de um projeto."""
    
    BASE_WORKSPACE_PATH = Path("project_workspaces")

    def __init__(self, project_id: uuid.UUID):
        self.project_id = project_id
        self.workspace_path = self.BASE_WORKSPACE_PATH / str(self.project_id)
        self.context_file_path = self.workspace_path / "context.json"
        
        self.context = self._load_or_create_context()
        log.info("ContextManager initialized.", project_id=str(self.project_id))
    
    def _create_workspace(self):
        """Cria o diretório do workspace, incluindo logs."""
        log.info("Creating project workspace.", path=str(self.workspace_path))
        (self.workspace_path / "logs").mkdir(parents=True, exist_ok=True)
        (self.workspace_path / "artifacts").mkdir(exist_ok=True)

    def _load_or_create_context(self) -> ProjectContext:
        """Carrega o context.json ou cria um novo se não existir."""
        if self.context_file_path.exists():
            log.info("Loading existing project context.", path=str(self.context_file_path))
            with open(self.context_file_path, 'r') as f:
                data = json.load(f)
                return ProjectContext(**data)
        else:
            log.warning("Creating a new context without a goal/type. This should be set later.")
            self._create_workspace()
            context = ProjectContext(project_id=self.project_id)
            self.save_context(context, initial_creation=True)
            return context

    def save_context(self, context: ProjectContext = None, initial_creation: bool = False):
        """Salva o objeto de contexto atual no arquivo context.json."""
        if context is None:
            context = self.context
        
        context.last_updated = datetime.utcnow().isoformat()
        json_str = context.model_dump_json(indent=2)
        
        with open(self.context_file_path, 'w') as f:
            f.write(json_str)

        if not initial_creation:
            log.info("Project context saved.", path=str(self.context_file_path))
        else:
            log.info("New project context created.", project_id=str(self.project_id))
    
    def get_context(self) -> ProjectContext:
        """Retorna o objeto de contexto atual."""
        return self.context

    def complete_task(self, task: Task, output: str):
        """Marca uma tarefa como concluída e a move da fila para a lista de concluídas."""
        task_in_queue = next((t for t in self.context.task_queue if t.task_id == task.task_id), None)
        if not task_in_queue:
            log.warning("Attempted to complete a task not in the queue.", task_id=str(task.task_id))
            return

        self.context.task_queue.remove(task_in_queue)
        
        task.status = 'completed'
        task.output = output
        self.context.completed_tasks.append(task)
        
        log.info("Task marked as completed.", task_id=str(task.task_id))
        self.save_context()

    def update_status(self, status: str):
        """Atualiza o status geral do projeto."""
        log.info(f"Updating project status to '{status}'.")
        self.context.status = status
        self.save_context()
