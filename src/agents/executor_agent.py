# src/agents/executor_agent.py

from src.schemas.contracts import SystemConfig, ProjectContext, Task
from src.services.llm_client import LLMClient
from src.services.toolbelt import Toolbelt
from src.services.observability_service import log

class ExecutorAgent:
    def __init__(self, llm_client: LLMClient, toolbelt: Toolbelt, config: SystemConfig):
        self.llm_client = llm_client
        self.toolbelt = toolbelt
        self.model = config.model_mapping.executor # Vamos usar um modelo para o executor também

    def find_next_task(self, context: ProjectContext) -> Task | None:
        """
        Encontra a primeira tarefa na lista que ainda não foi concluída
        e cujas dependências já foram satisfeitas.
        """
        completed_task_ids = {task.id for task in context.completed_tasks}
        
        for task in context.tasks:
            # Se a tarefa já foi concluída, pule.
            if task.id in completed_task_ids:
                continue
            
            # Se a tarefa não tem dependências, ela está pronta.
            if not task.dependencies:
                log.info(f"ExecutorAgent: Found next task with no dependencies.", task_id=task.id)
                return task
            
            # Verifique se todas as dependências foram concluídas.
            if all(dep_id in completed_task_ids for dep_id in task.dependencies):
                log.info(f"ExecutorAgent: Found next task with resolved dependencies.", task_id=task.id)
                return task
        
        # Se o loop terminar, não há mais tarefas executáveis.
        log.info(f"ExecutorAgent: No more executable tasks found.")
        return None

    def execute_task(self, context: ProjectContext, task: Task):
        """
        Executa uma tarefa específica. (Ainda não implementado)
        """
        # Placeholder - aqui é onde a mágica acontecerá
        log.info(f"ExecutorAgent: Pretending to execute task.", task_description=task.description)
        
        # Por enquanto, vamos apenas movê-la para a lista de concluídas
        context.completed_tasks.append(task)
        log.info(f"ExecutorAgent: Task marked as complete.", task_id=task.id)
