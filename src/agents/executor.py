# src/agents/executor.py

from src.models import ProjectContext
from src.services.llm_client import LLMClient
from src.services.file_service import FileService
# Adicione esta importação
from src.services.shell_service import ShellService 
from src.services.observability_service import log
from src.schemas.contracts import Task

class Executor:
    # Atualize a assinatura do __init__
    def __init__(self, llm_client: LLMClient, file_service: FileService, shell_service: ShellService):
        self.llm_client = llm_client
        self.file_service = file_service
        # Adicione esta linha
        self.shell_service = shell_service
        
        self.toolbelt = {
            "write_file": self.file_service.write_file,
            "read_file": self.file_service.read_file,
            "list_files": self.file_service.list_files,
            # Adicione a nova ferramenta ao dicionário
            "run_shell_command": self.shell_service.run_shell_command,
            "finish": self._handle_finish,
        }

    # O resto do arquivo permanece o mesmo...

    def _handle_finish(self, **kwargs):
        log.info("Project goal considered complete by the plan.")
        return "Project finished successfully."

    def _execute_task(self, task: Task, context: ProjectContext):
        log.info(f"Executing task: {task.description}", task_id=task.id)
        
        tool_name = task.tool
        if tool_name not in self.toolbelt:
            log.error("Tool not found.", tool_name=tool_name)
            raise ValueError(f"Tool '{tool_name}' is not available.")
            
        tool_func = self.toolbelt[tool_name]
        
        try:
            result = tool_func(**task.parameters)
            result_str = str(result) if result is not None else "None"
            log.info("Task executed successfully.", task_id=task.id, result=result_str)
            context.add_action_result(task.id, "success", result_str)
        except Exception as e:
            log.error("Error executing task.", task_id=task.id, error=str(e), exc_info=True)
            context.add_action_result(task.id, "error", str(e))
            raise e

    def execute_plan(self, context: ProjectContext, model: str):
        log.info("Executor agent starting plan execution.", project_id=context.project_id)
        
        if not context.plan or not context.plan.tasks:
            log.warn("No plan or tasks to execute.")
            return

        for task in context.plan.tasks:
            self._execute_task(task, context)
            if task.tool == 'finish':
                break
            
        log.info("All tasks in the plan have been executed.")
