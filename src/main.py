# src/main.py

import argparse
from pathlib import Path
from .config import settings
from src.agents.orchestrator import Orchestrator
from src.services.llm_client import LLMClient
from src.services.file_service import FileService
# Adicione esta importação
from src.services.shell_service import ShellService 
from src.models import ProjectContext
from src.services.observability_service import log
import structlog

# A classe ContextManager permanece a mesma

class ContextManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        structlog.get_logger().info("ContextManager initialized.", base_dir=str(self.base_dir))

    def create_project_context(self, goal: str) -> ProjectContext:
        structlog.get_logger().info("Creating a new project context.", goal=goal)
        context = ProjectContext(goal=goal)
        project_path = self.base_dir / context.project_id
        context.workspace_path = str(project_path / "workspace")
        context.logs_path = str(project_path / "logs")

        context_file_path = project_path / "context.json"
        context.save(context_file_path)
        structlog.get_logger().info(f"Project context for '{context.project_id}' saved.", path=str(context_file_path))
        return context

def main():
    parser = argparse.ArgumentParser(description="Evolux Engine - An autonomous AI agent.")
    parser.add_argument('--goal', type=str, required=True, help='The high-level goal for the agent.')
    parser.add_argument('--model', type=str, default='anthropic/claude-3-haiku-20240307', help='The model to use for the LLM.')
    args = parser.parse_args()

    try:
 #       context_manager = ContextManager(settings.project_base_dir)
        context_manager = ContextManager(global_settings.project_base_dir)

        context = context_manager.create_project_context(args.goal)
        log.info(f"New project '{context.project_id}' created successfully.")

        log_file_path = Path(context.logs_path) / "execution.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        structlog.configure(
            processors=[
                # ... (resto da configuração igual) ...
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(min_level=structlog.INFO),
            logger_factory=structlog.PrintLoggerFactory(file=log_file_path.open('w')),
            cache_logger_on_first_use=True
        )
        log.info("Logging initialized.", log_file=str(log_file_path.absolute()))

        llm_client = LLMClient(provider=settings.llm_provider)
        file_service = FileService(workspace_path=context.workspace_path)
        # Crie uma instância do novo serviço
        shell_service = ShellService(workspace_path=context.workspace_path)
        # Passe-o para o Orchestrator
        orchestrator = Orchestrator(llm_client, file_service, shell_service)

        orchestrator.run(context, args.model)
        
        context.save(Path(settings.project_base_dir) / context.project_id / "context.json")

    except Exception as e:
        structlog.get_logger().critical("A critical error occurred.", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}\nVerifique os logs para detalhes.")

if __name__ == "__main__":
    main()
