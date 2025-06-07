# src/main.py (VERSÃO FINAL E LIMPA)

import typer
import uuid

# Note: Não há mais hacks de sys.path aqui. Não precisamos mais deles.

from src.services.config_manager import ConfigManager
from src.services.context_manager import ContextManager
from src.services.observability_service import ObservabilityService, log
from src.agents.orchestrator import Orchestrator
from src.services.llm_client import LLMClient
from src.services.toolbelt import Toolbelt

# O app é criado aqui para ser importado pelo evolux.py
app = typer.Typer(
    name="Evolux Engine",
    help="An AI-powered software development automation engine."
)

@app.command()
def start(
    goal: str = typer.Option(..., "--goal", "-g", help="The main goal for the project."),
    project_id: uuid.UUID = typer.Option(None, "--project-id", "-p", help="An existing project ID to resume.")
):
    """
    Start a new project or resume an existing one.
    """
    project_id = project_id or uuid.uuid4()
    
    try:
        log_dir = f"project_workspaces/{project_id}/logs"
        ObservabilityService.initialize(log_dir=log_dir, project_id=project_id)
        
        log.info("====================================")
        log.info("       STARTING EVOLUX ENGINE       ")
        log.info("====================================")

        config = ConfigManager.get_config()
        log.info("Configuration loaded and validated successfully.")

        context_manager = ContextManager(project_id)
        context = context_manager.get_context()
        context.project_goal = goal
        context_manager.save_context(context)
        
        llm_client = LLMClient(config.llm_provider, config.openrouter_api_key)
        toolbelt = Toolbelt(context.workspace_path)
        
        orchestrator = Orchestrator(
            project_id=project_id,
            config=config,
            context_manager=context_manager,
            llm_client=llm_client,
            toolbelt=toolbelt
        )
        orchestrator.run()

    except Exception as e:
        log.critical("A critical error occurred during execution.", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}")
        print(f"Verifique o arquivo de log em 'project_workspaces/{project_id}/logs' para mais detalhes.")

# Note: A cláusula `if __name__ == "__main__"` foi removida.
# O ponto de entrada agora é o `evolux.py`.
