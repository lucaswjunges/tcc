# src/main.py (VERSÃO FINAL E CORRIGIDA)

import typer
from typing_extensions import Annotated
from typing import Optional
import uuid

from src.config import settings
from src.services.observability_service import init_logging, log
from src.services.context_manager import ContextManager
from src.services.llm_client import LLMClient
from src.services.toolbelt import Toolbelt
from src.agents.orchestrator import Orchestrator

app = typer.Typer()

@app.command()
def start(
    goal: Annotated[
        Optional[str],
        typer.Option(
            "--goal",
            "-g",
            help="The main goal of the AI project.",
        ),
    ] = None,
    project_id: Annotated[
        Optional[str],
        typer.Option(
            "--project-id",
            "-p",
            help="The ID of an existing project to resume.",
        ),
    ] = None,
):
    """Starts the Evolux Engine to work on a project goal."""
    if not goal and not project_id:
        log.error("Either --goal or --project-id must be provided.")
        raise typer.Exit(code=1)

    project_uuid = uuid.UUID(project_id) if project_id else uuid.uuid4()
    
    log_dir = f"project_workspaces/{project_uuid}/logs"
    init_logging(log_dir)

    log.info("====================================")
    log.info("       STARTING EVOLUX ENGINE       ")
    log.info("====================================")

    config = settings
    log.info("Configuration loaded and validated successfully.")

    try:
        context_manager = ContextManager(str(project_uuid))
        
        # --- A CORREÇÃO LÓGICA ESTÁ AQUI ---
        if goal:
            log.info("Starting a new project...")
            context = context_manager.create_context(goal)
        else:
            log.info(f"Resuming project {project_uuid}...")
            context = context_manager.get_context()
        # ------------------------------------

        llm_client = LLMClient(config)
        toolbelt = Toolbelt(context.workspace_path)
        
        orchestrator = Orchestrator(
            project_id=str(project_uuid),
            config=config,
            context_manager=context_manager,
            llm_client=llm_client,
            toolbelt=toolbelt,
        )
        orchestrator.run()

    except Exception as e:
        log.critical("A critical error occurred during execution.", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}")
        print(f"Verifique o arquivo de log em '{log_dir}' para mais detalhes.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
