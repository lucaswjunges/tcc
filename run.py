import asyncio
import argparse
import uuid
import os # Ainda pode ser útil para outras coisas, mas não para carregar .env aqui

# REMOVA COMPLETAMENTE AS LINHAS DE python-dotenv:
# from dotenv import load_dotenv
# load_dotenv()
# print("Arquivo .env carregado por python-dotenv.") # Ou qualquer print sobre isso

from evolux_engine.core.agent import Agent
from evolux_engine.utils.logging_utils import setup_logging, APP_LOGGER_NAME
from evolux_engine.settings import settings, EvoluxSettings # Importar a classe para o type hint
from loguru import logger # logger global (será configurado por setup_logging)

# Função para imprimir variáveis carregadas (corrigido para Pydantic v2)
def print_loaded_env_vars(current_settings: EvoluxSettings): # Recebe a instância
    """Imprime as variáveis de ambiente relevantes carregadas pelo Pydantic (settings)."""
    logger.info("Variáveis de ambiente carregadas (via Pydantic settings):")
    # Acessar model_fields a partir da CLASSE, não da instância
    for field_name, field_info in EvoluxSettings.model_fields.items():
        # O nome da variável de ambiente é o validation_alias se existir, senão o nome do campo em maiúsculas
        env_var_name = field_info.validation_alias if field_info.validation_alias else None
        if not env_var_name and hasattr(field_info, 'json_schema_extra') and isinstance(field_info.json_schema_extra, dict):
            env_var_name = field_info.json_schema_extra.get('env') # Fallback para 'env' se usado
        if not env_var_name: # Se ainda não definido, use o nome do campo
             env_var_name = field_name.upper()


        value = getattr(current_settings, field_name)
        
        value_display = value
        # Mascarar chaves de API
        if isinstance(value, str) and ("API_KEY" in field_name.upper() or "TOKEN" in field_name.upper()):
            if len(value) > 10:
                value_display = f"{value[:6]}...{value[-4:]}"
            elif value: # Se for uma string curta mas não vazia
                value_display = "****" 
        
        logger.info(f"  {env_var_name} (campo {field_name}): {value_display}")

async def main():
    parser = argparse.ArgumentParser(description="Evolux Engine - Agente Autônomo de Desenvolvimento")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal para o agente.")
    parser.add_argument("--project_id", type=str, default=None, help="ID de um projeto existente para continuar.")
    args = parser.parse_args()

    # Configura o logging usando as configurações carregadas pelo Pydantic
    # setup_logging() usa o objeto `settings` importado globalmente
    setup_logging() 
    main_logger = logger.bind(module="run_main") # Logger específico para esta função main

    main_logger.info("Evolux Engine iniciando...")
    
    # Imprime as variáveis de ambiente carregadas usando a instância `settings` importada
    print_loaded_env_vars(settings)

    project_id_to_use = args.project_id if args.project_id else str(uuid.uuid4())
    main_logger.info(f"Usando Project ID: {project_id_to_use}")
    main_logger.info(f"Objetivo recebido: {args.goal}")

    try:
        main_logger.info("Inicializando Agente...")
        agent = Agent(project_id=project_id_to_use, goal=args.goal)
        main_logger.info("Agente inicializado. Executando ciclo de planejamento/execução...")
        await agent.run()
        main_logger.info("Ciclo do agente concluído.")
    except ValueError as ve:
        main_logger.error(f"Erro de valor ou configuração: {ve}")
        # Adicionar mais detalhes se a exceção for sobre a chave API
        if "OPENROUTER_API_KEY" in str(ve).upper() or "TOKEN" in str(ve).upper() :
            main_logger.error("Verifique se EVOLUX_OPENROUTER_API_KEY está definida corretamente no seu arquivo .env e se o arquivo .env está na raiz do projeto.")
            main_logger.error(f"Valor atual de settings.OPENROUTER_API_KEY no run.py: {'MASKED' if settings.OPENROUTER_API_KEY else 'None'}")
    except Exception as e:
        main_logger.exception(f"Erro inesperado durante a execução do agente: {e}")

if __name__ == "__main__":
    asyncio.run(main())
