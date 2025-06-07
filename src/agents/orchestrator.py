# src/agents/orchestrator.py (VERSÃO FINAL, SIMPLES E CORRETA)

# Um ponto (.) significa "na mesma pasta".
# Agora que os arquivos têm os nomes corretos, estas importações funcionarão.
from ..models import ProjectContext, SystemConfig
from ..services.file_service import FileService
from ..services.llm_client import get_llm_client
from ..services.observability_service import log
from .planner import Planner
from .executor import Executor

class Orchestrator:
    def __init__(self, config: SystemConfig, context: ProjectContext):
        self.config = config
        self.context = context
        self.llm_client = get_llm_client()
        self.file_service = FileService(self.context.get_workspace_path())
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client, self.file_service)

    def run(self):
        log.info("Orchestrator starting run.", goal=self.context.goal)
        plan = self.planner.create_plan(
            goal=self.context.goal,
            model=self.config.model_mapping.planner
        )
        log.info("Plan created successfully.", plan=plan.model_dump())
        self.context.add_plan(plan)
        self.executor.execute_plan(
            context=self.context,
            model=self.config.model_mapping.executor
        )
        log.info("Orchestrator run finished.")
