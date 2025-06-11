import argparse
import asyncio
import os
import uuid # Para gerar project_id se não fornecido

# Carregar .env antes de importar outros módulos que possam usar settings
from dotenv import load_dotenv
load_dotenv() 
print("Arquivo .env carregado por python-dotenv.") # Confirmação de carregamento

# Agora importe seus módulos. É crucial que settings seja carregado após dotenv.
from evolux_engine.core.agent import Agent
from evolux_engine.utils.logging_utils import setup_logging, log_entry as log # Seu logger
from evolux_engine.settings import settings # Seu settings

def print_loaded_env_vars():
    """Imprime as variáveis de ambiente relevantes carregadas pelo Pydantic (settings)."""
    print("Variáveis de ambiente carregadas (via Pydantic settings):")
    for field_name, field in settings.model_fields.items():
        alias = field.alias if field.alias else field_name
        env_var_name = field.validation_alias if field.validation_alias else alias.upper()
        value = getattr(settings, field_name)
        # Ocultar chaves de API parcialmente
        if "API_KEY" in env_var_name and value and isinstance(value, str) and len(value) > 8:
            value_display = f"{value[:6]}********{value[-4:]}"
        else:
            value_display = value
        print(f"  {env_var_name} (campo {field_name}): {value_display}")


async def main():
    # Argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Evolux Engine - Agente de Desenvolvimento")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal do projeto.")
    parser.add_argument("--project-id", type=str, help="ID de um projeto existente ou a ser usado.")
    # Adicione mais argumentos conforme necessário (ex: --model-planner, --model-executor)
    args = parser.parse_args()

    # Imprimir variáveis carregadas
    print_loaded_env_vars()

    # Configurar logging (usando sua função de setup)
    # O nível de logging pode vir de settings ou ser um default.
    log_level = getattr(settings, 'LOGGING_LEVEL', "INFO").upper()
    setup_logging(level=log_level) # Ajuste conforme a assinatura da sua setup_logging
    log.info("Logging configurado para o nível: " + log_level, component="evolux_engine") # Log inicial
    log.info("Evolux Engine iniciando...", component="__main__")

    project_id_to_use = args.project_id or str(uuid.uuid4())
    
    log.info(f"Objetivo recebido: {args.goal}", component="__main__", project_id_arg=args.project_id)

    try:
        # A inicialização do agente agora ocorre dentro do __init__ do Agent
        # incluindo a criação do diretório do projeto via ContextManager
        log.info(f"Inicializando Agente...", component="__main__", agent_id=project_id_to_use, goal=args.goal)
        agent = Agent(project_id=project_id_to_use, goal=args.goal)
        
        # O __init__ do Agent já loga seu sucesso/status
        log.info("Agente instanciado. Iniciando execução...", component="__main__")
        
        success = await agent.run() # Executa o agente

        if success:
            log.info("Execução do agente principal concluída com sucesso.", component="__main__", project_id=project_id_to_use)
        else:
            log.error("Execução do agente principal concluída com falhas.", component="__main__", project_id=project_id_to_use)

    except ValueError as ve: # Erros de configuração, API keys, etc.
        log.error(f"Erro de valor ou configuração: {str(ve)}", component="__main__", exc_info=True)
    except Exception as e:
        log.error(f"Erro inesperado durante a execução: {str(e)}", component="__main__", exc_info=True)

if __name__ == "__main__":
    # O carregamento do .env já foi feito no topo do arquivo
    asyncio.run(main())

