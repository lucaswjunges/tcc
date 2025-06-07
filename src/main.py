# src/main.py (VERSÃO CORRIGIDA)

import uuid
import click
from dotenv import load_dotenv

# AQUI ESTÁ A MUDANÇA: Importamos a classe ConfigManager
from src.services.config_manager import ConfigManager
from src.services.observability_service import log, setup_logging
from src.services.context_manager import ContextManager
from src.agents.orchestrator import Orchestrator

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@click.group()
def main():
    """Evolux Engine CLI"""
    pass

@main.command()
@click.option('--goal', required=True, help='The main goal for the project.')
@click.option('--project-type', default='code_project', help='The type of project.')
@click.option('--project-id', 'project_id_str', default=None, help='Existing project ID to resume.')
def start(goal: str, project_type: str, project_id_str: str):
    """Starts a new project or resumes an existing one."""
    
    project_id = uuid.UUID(project_id_str) if project_id_str else uuid.uuid4()
    
    setup_logging(project_id)
    log.info("====================================")
    log.info("       STARTING EVOLUX ENGINE       ")
    log.info("====================================")

    try:
        # E AQUI ESTÁ A MUDANÇA: Usamos a classe diretamente
        config = ConfigManager.get_config()
        
        context_manager = ContextManager(project_id)
        context = context_manager.get_context()
        
        # Se for um novo projeto, inicializa o contexto com o objetivo
        if not project_id_str:
            context.project_goal = goal
            context.project_type = project_type
            context_manager.save_context()
        
        orchestrator = Orchestrator(project_id, config, context_manager)
        orchestrator.run()

    except Exception as e:
        log.critical("A critical error occurred during execution.", error=str(e), exc_info=True)
        print(f"\nErro Crítico: {e}")
        print(f"Verifique o arquivo de log em 'project_workspaces/{project_id}/logs' para mais detalhes.")

if __name__ == '__main__':
    main()

