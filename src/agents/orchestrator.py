# src/agents/orchestrator.py (VERSÃO FINAL E CORRIGIDA)

from src.services.llm_client import LLMClient
from src.services.context_manager import ContextManager
from src.services.toolbelt import Toolbelt
from src.services.observability_service import log
from src.models.project_context import ProjectContext, ProjectState, Task
from src.schemas.contracts import SystemConfig
from src.agents.planner_agent import PlannerAgent

class Orchestrator:
    def __init__(
        self,
        project_id: str,
        config: SystemConfig,
        context_manager: ContextManager,
        llm_client: LLMClient,
        toolbelt: Toolbelt,
    ):
        self.project_id = project_id
        self.config = config
        self.context_manager = context_manager
        self.llm_client = llm_client
        self.toolbelt = toolbelt
        self.planner_agent = PlannerAgent(llm_client=self.llm_client)
        log.info("Orchestrator initialized.", project_id=self.project_id)

    def run(self):
        log.info("Orchestrator run loop started.", project_id=self.project_id)
        try:
            context = self.context_manager.get_context()
            
            # --- A CORREÇÃO CRÍTICA ESTÁ AQUI ---
            # Injetamos a configuração geral no estado do projeto.
            # Agora, qualquer agente que receber o 'context' terá acesso ao 'config'.
            context.config = self.config
            # ------------------------------------
            
            if context.current_state == ProjectState.PLANNING:
                self._execute_planning_phase(context)

        except Exception as e:
            log.critical("Orchestrator run failed. Halting execution.", error_message=str(e), exc_info=True)
            context = self.context_manager.get_context()
            context.current_state = ProjectState.FAILED
            log.info("Updating project status to 'failed'.")
            # Salvar o contexto após a falha precisa ser cuidadoso
            if hasattr(context, 'config'):
                del context.config # Remova antes de salvar para evitar problemas de serialização
            self.context_manager.save_context(context)


    def _execute_planning_phase(self, context: ProjectContext):
        log.info("Project is in 'planning' state. Invoking PlannerAgent.")
        tasks_data = self.planner_agent.create_initial_plan(context)
        context.tasks = [Task(**task_data) for task_data in tasks_data]
        context.current_state = ProjectState.EXECUTING
        
        # Remover config antes de salvar para evitar problemas de serialização
        del context.config 
        self.context_manager.save_context(context)
        log.info("Planning phase completed. Tasks created and state updated to EXECUTING.", num_tasks=len(context.tasks))

