import argparse
import os
import sys
import uuid

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importações devem vir depois do ajuste de sys.path
from evolux_engine.utils.env_vars import load_env_variables, settings
from evolux_engine.utils.logging_utils import setup_logging, log # log global
from evolux_engine.core.agent import Agent
from evolux_engine.core.context_manager import ContextManager


def main():
    # Carrega as configurações de ambiente ANTES de configurar o logging,
    # pois o nível de log pode vir das settings.
    load_env_variables(print_vars=True) # Imprime as vars para debug inicial

    # Configura o logging usando o nível das settings
    try:
        setup_logging(level=settings.LOGGING_LEVEL)
    except ValueError as e:
        # Se o nível de log for inválido, usa INFO e avisa.
        print(f"AVISO: Nível de log inválido '{settings.LOGGING_LEVEL}' nas configurações. Usando INFO. Erro: {e}")
        setup_logging(level="INFO")

    log.info("Evolux Engine iniciando...") # Agora log global está disponível
    log.debug("Configurações carregadas e logging inicializado.",
             provider=settings.LLM_PROVIDER,
             base_dir_projects=settings.PROJECT_BASE_DIR)

    # Validação de Chaves API
    if settings.LLM_PROVIDER == "openrouter" and not settings.OPENROUTER_API_KEY:
        log.error("Provedor é OpenRouter, mas EVOLUX_OPENROUTER_API_KEY não está configurada.")
        sys.exit(1)
    if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        log.error("Provedor é OpenAI, mas EVOLUX_OPENAI_API_KEY não está configurada.")
        sys.exit(1)
    if not settings.OPENROUTER_API_KEY and not settings.OPENAI_API_KEY:
         log.warning("Nenhuma chave de API (OpenRouter ou OpenAI) foi configurada. Funcionalidade LLM será limitada.")
         # Não sair, pode haver tarefas que não usam LLM ou o usuário pode querer apenas testar a estrutura.

    parser = argparse.ArgumentParser(description="Evolux Engine: Agente de IA para desenvolvimento de software.")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal para o agente.")
    parser.add_argument("--project_id", type=str, default=None, help="ID de um projeto existente para continuar. Se omitido, um novo ID será gerado.")
    # Adicionar mais argumentos conforme necessário (ex: --provider, --model)
    args = parser.parse_args()

    log.info(f"Objetivo recebido: {args.goal}", project_id_arg=args.project_id)

    # Configurar ContextManager
    project_id = args.project_id or str(uuid.uuid4())
    project_base_dir_for_projects = settings.PROJECT_BASE_DIR # Diretório onde todos os projetos são armazenados

    # Garantir que o diretório base onde TODOS os projetos ficam exista
    if not os.path.exists(project_base_dir_for_projects):
        try:
            os.makedirs(project_base_dir_for_projects)
            log.info(f"Diretório base de projetos criado: {project_base_dir_for_projects}")
        except OSError as e:
            log.critical(f"Não foi possível criar o diretório base de projetos {project_base_dir_for_projects}: {e}")
            sys.exit(1)
            
    # Caminho para o diretório específico deste projeto
    current_project_dir = os.path.join(project_base_dir_for_projects, project_id)

    try:
        context_manager = ContextManager(project_id=project_id, project_dir=current_project_dir)
        log.info(f"ContextManager inicializado para projeto.", project_id=project_id, path=current_project_dir)
    except Exception as e:
        log.critical(f"Falha ao inicializar ContextManager: {e}", project_id=project_id, exc_info=True)
        sys.exit(1)

    # Instanciar e executar o Agente
    try:
        agent = Agent(goal=args.goal, context_manager=context_manager)
        log.info("Agente instanciado. Iniciando execução...")
        
        agent.run() # Executa a lógica principal do agente
        
        log.info("Execução do agente concluída com sucesso.", project_id=project_id)
    except ValueError as ve:
        log.error(f"Erro de configuração ou valor inválido durante a operação do agente: {ve}", project_id=project_id, exc_info=True)
        sys.exit(1)
    except Exception as e:
        log.critical(f"Erro crítico durante a execução do agente: {e}", project_id=project_id, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
