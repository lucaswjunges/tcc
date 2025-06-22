import argparse
import asyncio
import uuid

# --- INÍCIO DA MODIFICAÇÃO ---
# Importa a instância 'settings' que agora é criada de forma robusta dentro de settings.py
from evolux_engine.settings import settings
# Importa o logger e a função de setup
from evolux_engine.utils.logging_utils import setup_logging
from loguru import logger as log
# Importa o Agente
from evolux_engine.core.agent import Agent
# --- FIM DA MODIFICAÇÃO ---

async def main():
    # Configurar logging com as settings que já foram importadas e criadas
    setup_logging(
        level=settings.LOGGING_LEVEL,
        sink_file=settings.LOG_TO_FILE,
        file_path=str(settings.LOG_FILE_PATH),
        file_level=settings.LOG_LEVEL_FILE,
        file_rotation=settings.LOG_FILE_ROTATION,
        file_retention=settings.LOG_FILE_RETENTION,
        serialize_json=settings.LOG_SERIALIZE_JSON
    )

    parser = argparse.ArgumentParser(description="Evolux Engine - Agente de Desenvolvimento")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal do projeto.")
    parser.add_argument("--project-id", type=str, help="ID de um projeto existente ou a ser usado.")
    args = parser.parse_args()

    log.info("Evolux Engine iniciando...", component="__main__")
    log.info(f"PROVEDOR DE LLM CONFIGURADO: {settings.LLM_PROVIDER}") # Log para confirmar

    project_id_to_use = args.project_id or str(uuid.uuid4())
    
    log.info(f"Objetivo recebido: {args.goal}", component="__main__", project_id_arg=args.project_id)

    try:
        log.info(f"Inicializando Agente...", component="__main__", agent_id=project_id_to_use, goal=args.goal)
        agent = Agent(project_id=project_id_to_use, goal=args.goal)
        
        log.info("Agente instanciado. Iniciando execução...", component="__main__")
        
        success = await agent.run()

        if success:
            log.info("Execução do agente principal concluída com sucesso.", component="__main__", project_id=project_id_to_use)
        else:
            log.error("Execução do agente principal concluída com falhas.", component="__main__", project_id=project_id_to_use)

    except ValueError as ve:
        log.error(f"Erro de valor ou configuração: {str(ve)}", component="__main__", exc_info=True)
    except Exception as e:
        log.error(f"Erro inesperado durante a execução: {str(e)}", component="__main__", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())