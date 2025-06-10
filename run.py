# Conteúdo para: run.py
import argparse
import os
import sys
import uuid # Para gerar IDs de projeto únicos

# Adiciona o diretório raiz do projeto ao sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---- DEBUG SYS.PATH ----
# print("--- DEBUG SYS.PATH ANTES DO IMPORT ---")
# ... (pode comentar ou remover esses prints de debug do sys.path se quiser)
# print("--- FIM DO BLOCO DE DEPURAÇÃO SYS.PATH ---")
# ---- FIM DEBUG ----

from evolux_engine.utils.env_vars import load_env_variables, settings
from evolux_engine.core.agent import Agent
from evolux_engine.utils.logging_utils import log
from evolux_engine.core.context_manager import ContextManager # <--- IMPORTAR ContextManager
from evolux_engine.models.project_context import ProjectContext # <--- IMPORTAR ProjectContext

def main():
    load_env_variables()

    log.info("Configurações carregadas.",
             provider=settings.LLM_PROVIDER,
             base_dir=settings.PROJECT_BASE_DIR)

    if not settings.OPENROUTER_API_KEY and settings.LLM_PROVIDER == "openrouter":
        log.error("Chave da API OpenRouter não configurada. Verifique seu arquivo .env ou variáveis de ambiente.")
        sys.exit(1)
    if not settings.OPENAI_API_KEY and settings.LLM_PROVIDER == "openai":
        log.error("Chave da API OpenAI não configurada.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Evolux Engine: Agente de IA para desenvolvimento de software.")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal para o agente.")
    parser.add_argument("--project_id", type=str, default=None, help="ID do projeto existente para continuar ou um novo será criado.")
    args = parser.parse_args()

    log.info(f"Objetivo recebido: {args.goal}")

    # Configurar o ContextManager
    project_id = args.project_id or str(uuid.uuid4()) # Usa ID fornecido ou gera um novo
    project_base_path = settings.PROJECT_BASE_DIR     # Definido em env_vars.py
    
    # Certifique-se de que o diretório base para todos os projetos exista
    if not os.path.exists(project_base_path):
        try:
            os.makedirs(project_base_path)
            log.info(f"Diretório base de projetos criado em: {project_base_path}")
        except OSError as e:
            log.error(f"Não foi possível criar o diretório base de projetos {project_base_path}: {e}")
            sys.exit(1)
            
    project_path = os.path.join(project_base_path, project_id)
    
    # Criar ProjectContext (se ContextManager não o fizer internamente ao ser inicializado)
    # Supondo que ProjectContext também precisa do project_path
    # Verifique a definição de ProjectContext e ContextManager
    # Por simplicidade, vamos assumir que ContextManager lida com a criação/carregamento do contexto.
    
    try:
        context_manager = ContextManager(project_id=project_id, project_dir=project_path)
        log.info(f"ContextManager inicializado para o projeto: {project_id} em {project_path}")
    except Exception as e:
        log.error(f"Falha ao inicializar ContextManager: {e}", exc_info=True)
        sys.exit(1)

    # Agora instancie o Agente com o context_manager
    try:
        agent = Agent(goal=args.goal, context_manager=context_manager) # <--- PASSAR context_manager
        log.info("Agente instanciado com sucesso.")
        
        # Executar o agente
        agent.run() # <--- Linha para realmente executar a lógica do agente
        
        log.info("Execução do agente (simulada ou real) concluída.")
    except ValueError as ve: # Capturar ValueErrors específicos (ex: API key, provider)
        log.error(f"Erro de configuração ou valor inválido ao inicializar ou executar o agente: {ve}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        log.error(f"Erro durante a inicialização ou execução do agente: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
