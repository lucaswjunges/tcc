# src/main.py
import argparse
from .config import settings
from .services.observability_service import init_logging, log
from .services.context_manager import ContextManager
from .orchestrator.orchestrator import Orchestrator  # Corrigido de 'src.orchestrator' para '.orchestrator'

def app(goal: str, project_id: str | None = None):
    try:
        context_manager = ContextManager(settings.project_workspace_dir)
        if project_id:
            context = context_manager.load_project_context(project_id)
        else:
            context = context_manager.create_new_project_context(goal)
        
        init_logging(context.get_logs_path())
        log.info("Configuration and context loaded.", config=settings.model_dump_json())
        
        orchestrator = Orchestrator(config=settings, context=context)
        orchestrator.run()
    except Exception as e:
        log.critical("A critical error occurred during execution.", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}\nVerifique os logs para detalhes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evolux Engine")
    parser.add_argument("--goal", type=str, required=True, help="The main goal.")
    parser.add_argument("--project_id", type=str, help="Optional project ID to continue.")
    args = parser.parse_args()
    
    log.info("="*36); log.info("       STARTING EVOLUX ENGINE       "); log.info("="*36)
    app(goal=args.goal, project_id=args.project_id)
