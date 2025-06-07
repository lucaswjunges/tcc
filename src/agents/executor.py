# src/agents/executor.py

from ..models import ProjectContext
from ..services.llm_client import LLMClient
from ..services.file_service import FileService
from ..services.observability_service import log
from ..schemas.contracts import Task

class Executor:
    """
    O Agente Executor é responsável por executar as tarefas definidas no plano,
    uma a uma, utilizando as ferramentas disponíveis.
    """
    def __init__(self, llm_client: LLMClient, file_service: FileService):
        self.llm_client = llm_client
        self.file_service = file_service
        self.toolbelt = {
            "write_file": self.file_service.write_file,
            "read_file": self.file_service.read_file,
            "list_files": self.file_service.list_files,
        }

    def _execute_task(self, task: Task, context: ProjectContext):
        log.info(f"Executing task: {task.description}", task_id=task.id)
        
        tool_name = task.tool
        if tool_name not in self.toolbelt:
            log.error("Tool not found.", tool_name=tool_name)
            raise ValueError(f"Tool '{tool_name}' is not available.")
            
        tool_func = self.toolbelt[tool_name]
        
        try:
            # Transforma o dicionário de parâmetros em argumentos para a função
            result = tool_func(**task.parameters)
            log.info("Task executed successfully.", task_id=task.id, result=str(result))
            context.add_action_result(task.id, "success", str(result))

        except Exception as e:
            log.error("Error executing task.", task_id=task.id, error=str(e), exc_info=True)
            context.add_action_result(task.id, "error", str(e))
            # Você pode decidir se quer parar a execução ou continuar
            raise e

    def execute_plan(self, context: ProjectContext, model: str):
        log.info("Executor agent starting plan execution.", project_id=context.project_id)
        
        if not context.plan or not context.plan.tasks:
            log.warn("No plan or tasks to execute.")
            return

        for task in context.plan.tasks:
            self._execute_task(task, context)
            
        log.info("All tasks in the plan have been executed.")

