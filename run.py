import argparse
import asyncio
import logging
from dotenv import load_dotenv

# Carrega o .env no início para garantir que todas as variáveis de ambiente
# estejam disponíveis para os módulos que serão importados em seguida.
load_dotenv()

# Reduzir logs verbosos do httpcore/httpx
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Agora, importa os componentes da nova arquitetura
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.services.advanced_context_manager import AdvancedContextManager
from evolux_engine.config.advanced_config import AdvancedSystemConfig
from evolux_engine.core.orchestrator import Orchestrator
from evolux_engine.services.observability_service import init_logging, get_logger

# Define um logger para este script de inicialização
log = get_logger("evolux_engine_main")

async def main():
    """
    Função principal que inicializa e executa o agente.
    """
    # 1. Carrega as configurações globais usando o ConfigManager
    try:
        config = ConfigManager()
        # 2. Inicializa o sistema de logging com as configurações carregadas
        log_dir = config.get_global_setting("log_dir", "./logs")
        init_logging(log_dir=log_dir, console_level=config.get_global_setting("logging_level", "INFO"))
    except Exception as e:
        # Se a configuração falhar, é um erro crítico.
        log.error("Falha crítica na inicialização das configurações. Encerrando.", error=str(e), exc_info=True)
        return

    log.info("ConfigManager e Logging inicializados com sucesso.")
    log.info(f"PROVEDOR DE LLM CONFIGURADO: {config.get_global_setting('default_llm_provider')}")

    # 3. Processa os argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Evolux Engine - Orquestrador de Agentes de IA")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal do projeto.")
    parser.add_argument("--project-id", type=str, help="ID de um projeto existente para continuar trabalhando nele.")
    parser.add_argument("--modoexecucao", type=str, default="producao", choices=["producao", "teste"], help="Modo de execução do sistema.")
    args = parser.parse_args()

    # Passa o modo de execução para a configuração global
    config.set_global_setting("execution_mode", args.modoexecucao)
    log.info(f"Modo de execução definido como: {args.modoexecucao}")

    # 4. Cria ou carrega o contexto do projeto usando AdvancedContextManager
    advanced_config = AdvancedSystemConfig(
        project_base_directory=config.get_global_setting("project_base_directory", "./project_workspaces")
    )
    context_manager = AdvancedContextManager(config=advanced_config)
    project_context = None

    if args.project_id:
        try:
            log.info(f"Tentando carregar projeto existente com ID: {args.project_id}")
            project_context = context_manager.load_project_context(args.project_id)
        except FileNotFoundError:
            log.error(f"Projeto com ID '{args.project_id}' não encontrado. Criando um novo projeto.")
            # Se não encontrar, segue para criar um novo
    
    if not project_context:
        log.info("Nenhum projeto existente fornecido ou encontrado. Criando um novo projeto.")
        project_context = context_manager.create_new_project_context(goal=args.goal)

    log.info(f"Trabalhando com o Projeto ID: {project_context.project_id}")
    log.info(f"Objetivo: {project_context.project_goal}")

    # 5. Inicializa e executa o Orquestrador
    try:
        orchestrator = Orchestrator(
            project_context=project_context,
            config_manager=config,
        )
        await orchestrator.run_project_cycle()
        log.info("Ciclo do Orquestrador concluído.")
        
    except Exception as e:
        log.error("Erro fatal no ciclo principal do Orquestrador.", error=str(e), exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
