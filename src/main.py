import argparse
from pathlib import Path
from datetime import datetime
import hashlib
from src.agents.orchestrator import Orchestrator
from src.services.llm_client import LLMClient
from src.services.file_service import FileService
from src.services.shell_service import ShellService 
from src.models import ProjectContext
import structlog
from structlog.processors import JSONRenderer, TimeStamper, add_log_level
from structlog.contextvars import merge_contextvars
from src.config import settings as global_settings
from src.services.observability_service import log  # Importando o logger corretamente

class ContextManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        log.info("ContextManager initialized.", base_dir=str(self.base_dir))

    def create_project_context(self, goal: str) -> ProjectContext:
        log.info("Creating a new project context.", goal=goal)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        goal_hash = hashlib.sha1(goal.encode()).hexdigest()[:6]
        project_id = f"proj_{timestamp}_{goal_hash}"
        
        context = ProjectContext(
            project_id=project_id,
            goal=goal,
            workspace_dir=str(self.base_dir)
        )
        
        project_path = self.base_dir / project_id
        context.workspace_path = str(project_path / "workspace")
        context.logs_path = str(project_path / "logs")

        project_path.mkdir(parents=True, exist_ok=True)
        Path(context.workspace_path).mkdir(parents=True, exist_ok=True)
        Path(context.logs_path).mkdir(parents=True, exist_ok=True)

        context_file_path = project_path / "context.json"
        context.save(context_file_path)
        log.info("Project context saved", 
                 project_id=context.project_id,
                 path=str(context_file_path))
        return context

def main():
    parser = argparse.ArgumentParser(description="Evolux Engine - An autonomous AI agent.")
    parser.add_argument('--goal', type=str, required=True, help='The high-level goal for the agent.')
    parser.add_argument('--model', type=str, default='anthropic/claude-3-haiku-20240307', help='The model to use for the LLM.')
    args = parser.parse_args()

    try:
        # Verificar configurações essenciais
        if not global_settings.openrouter_api_key:
            raise ValueError("EVOLUX_OPENROUTER_API_KEY não está configurada no arquivo .env")

        context_manager = ContextManager(global_settings.project_base_dir)
        context = context_manager.create_project_context(args.goal)
        
        # Configurar logging para este projeto específico
        log_file_path = Path(context.logs_path) / "execution.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        structlog.configure(
            processors=[
                merge_contextvars,
                add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                TimeStamper(fmt="iso"),
                JSONRenderer()
            ],
            wrapper_class=structlog.BoundLogger,
            logger_factory=structlog.PrintLoggerFactory(file=log_file_path.open('w')),
            cache_logger_on_first_use=True,
        )
        
        log.info("Logging initialized", log_file=str(log_file_path))

        # Inicializar serviços
        llm_client = LLMClient(api_key=global_settings.openrouter_api_key, model=args.model)
        file_service = FileService(workspace_path=context.workspace_path)
        shell_service = ShellService(workspace_path=context.workspace_path)
        orchestrator = Orchestrator(llm_client, file_service, shell_service)

        orchestrator.run(context, args.model)
        
        context.save(Path(global_settings.project_base_dir) / context.project_id / "context.json")

    except Exception as e:
        log.error("A critical error occurred", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}\nVerifique os logs para detalhes.")

if __name__ == "__main__":
    main()
