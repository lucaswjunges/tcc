# src/agents/orchestrator.py (VERSÃO CORRIGIDA)

import uuid
from pathlib import Path

from src.schemas.contracts import SystemConfig, Task, ProjectContext, ProjectStatus
from src.services.context_manager import ContextManager
from src.services.llm_client import LLMClient
from src.agents.planner_agent import PlannerAgent
from src.services.observability_service import log
from src.tools.toolbelt import Toolbelt

class Orchestrator:
    def __init__(self, project_id: uuid.UUID, config: SystemConfig, context_manager: ContextManager):
        self.project_id = project_id
        self.config = config
        self.context_manager = context_manager
        
        self.llm_client = LLMClient()
        # =========================================================================
        # AQUI ESTÁ A CORREÇÃO:
        # Acessamos o atributo 'workspace_path' diretamente, sem os "()",
        # porque ele é uma variável do ContextManager, não um método/função.
        self.toolbelt = Toolbelt(self.context_manager.workspace_path)
        # =========================================================================
        
        log.info("Orchestrator initialized.", project_id=str(project_id))

    def run(self):
        log.info("Orchestrator run loop started.", project_id=str(self.project_id))
        context = self.context_manager.get_context()

        try:
            if context.current_status == ProjectStatus.PLANNING:
                self._execute_planning_phase()

            # (Outras fases como EXECUTION virão aqui no futuro)

            # Se chegamos aqui e tudo correu bem
            if context.current_status != ProjectStatus.FAILED:
                context.current_status = ProjectStatus.COMPLETED
                log.info("Project has been completed successfully.")
            
            self.context_manager.save_context()

        except Exception as e:
            log.critical("Orchestrator run failed. Halting execution.", error=str(e), exc_info=True)
            context = self.context_manager.get_context() # Recarrega o contexto
            context.current_status = ProjectStatus.FAILED
            log.info("Updating project status to 'failed'.")
            self.context_manager.save_context()


    def _execute_planning_phase(self):
        context = self.context_manager.get_context()
        log.info("Project is in 'planning' state. Invoking PlannerAgent.")

        planner = PlannerAgent(llm_client=self.llm_client, config=self.config)
        
        task_list : list[Task] = planner.create_initial_plan(context)

        if not task_list:
            log.error("PlannerAgent returned an empty task list. Halting.")
            raise ValueError("Planner failed to generate a task list.")
        
        context.tasks = task_list
        context.current_status = ProjectStatus.PENDING_EXECUTION # Próximo estado
        self.context_manager.save_context()
        log.info(f"Successfully planned {len(task_list)} tasks. Moving to next state.")

