# src/agents/executor.py (VERSÃO FINAL DE VERDADE)

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
        
        # CORREÇÃO DEFINITIVA: Simplesmente armazena o file_service recebido.
        # Não tenta recriá-lo a partir de um atributo inexistente.
        self.file_service = file_service
        
        self.toolbelt = {
            "write_file": self.file_service.write_file,
            "read_file": self.file_service.read_file,
            "list_files": self.file_service.list_files,
            "finish": self._handle_finish,
        }

    def _handle_finish(self, **kwargs):
        """Ação especial para a ferramenta 'finish'. Apenas loga a conclusão."""
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
            log.info("Task executed successfully.", task_id=task.id, result=str(result))
            context.add_action_result(task.id, "success", str(result))

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

