# src/orchestrator.py

from src.models.project_context import ProjectContext
from src.services.llm_client import LLMClient
from src.services.file_service import FileService
# Adicione esta importação
from src.services.shell_service import ShellService
from src.agents.planner import Planner
from src.agents.executor import Executor
from src.services.observability_service import log

class Orchestrator:
    # Atualize a assinatura do __init__
    def __init__(self, llm_client: LLMClient, file_service: FileService, shell_service: ShellService):
        self.planner = Planner(llm_client)
        # Passe o shell_service para o Executor
        self.executor = Executor(llm_client, file_service, shell_service)

    # O resto do arquivo permanece o mesmo...
    def run(self, context: ProjectContext, model: str):
        log.info("Orchestrator starting run.", goal=context.goal)
        
        if not context.plan:
            plan = self.planner.create_plan(context, model)
            context.plan = plan
            log.info("Plan created successfully.", plan=plan.model_dump())
        else:
            log.info("Using existing plan from context.")

        self.executor.execute_plan(context, model)
        
        log.info("Orchestrator run finished.")
