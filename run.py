import argparse
import asyncio
import os
import uuid # Para gerar project_id se não fornecido

# Carregar .env antes de importar outros módulos que possam usar settings
from dotenv import load_dotenv
load_dotenv()
print("Arquivo .env carregado por python-dotenv.") # Confirmação de carregamento

# --- INÍCIO DA CORREÇÃO ---
# 1. Importe a função de CONFIGURAÇÃO do logging_utils
from evolux_engine.utils.logging_utils import setup_logging
# 2. Importe o logger do LOGURU para USAR, e o apelide de 'log'
from loguru import logger as log
# 3. Importe o Agent e as settings normalmente
from evolux_engine.core.agent import Agent
from evolux_engine.settings import settings
# --- FIM DA CORREÇÃO ---

def print_loaded_env_vars():
    """Imprime as variáveis de ambiente relevantes carregadas pelo Pydantic (settings)."""
    print("\n--- Variáveis de Ambiente Carregadas (via Pydantic settings) ---")
    for field_name, field in settings.model_fields.items():
        alias = field.alias if field.alias else field_name
        env_var_name = field.validation_alias if field.validation_alias else alias.upper()
        value = getattr(settings, field_name)

        # Ocultar chaves de API parcialmente
        if "API_KEY" in env_var_name and value and isinstance(value, str) and len(value) > 8:
            value_display = f"{value[:6]}...{value[-4:]}"
        else:
            value_display = value

        # Adiciona um aviso se a chave ainda for None após carregar
        warning = ""
        if "API_KEY" in env_var_name and not value:
            warning = "  <-- ATENÇÃO: Chave não carregada!"

        print(f"  > {env_var_name}: {value_display}{warning}")
    print("----------------------------------------------------------------\n")


async def main():
    # --- INÍCIO DA CORREÇÃO ---
    # Configurar logging ANTES de qualquer outra coisa.
    # Usa os valores das settings que já foram carregadas.
    setup_logging(
        level=settings.LOGGING_LEVEL,
        sink_file=settings.LOG_TO_FILE,
        file_path=str(settings.LOG_FILE_PATH), # Garante que seja string
        file_level=settings.LOG_LEVEL_FILE,
        file_rotation=settings.LOG_FILE_ROTATION,
        file_retention=settings.LOG_FILE_RETENTION,
        serialize_json=settings.LOG_SERIALIZE_JSON
    )
    # --- FIM DA CORREÇÃO ---

    # Argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Evolux Engine - Agente de Desenvolvimento")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal do projeto.")
    parser.add_argument("--project-id", type=str, help="ID de um projeto existente ou a ser usado.")
    args = parser.parse_args()

    # Imprimir variáveis carregadas para depuração
    print_loaded_env_vars()

    log.info("Evolux Engine iniciando...", component="__main__")

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