# evolux-engine/run.py
import argparse
import logging
import os
import sys

# --- INÍCIO DO BLOCO DE DEPURAÇÃO SYS.PATH ---
print("--- DEBUG SYS.PATH ANTES DO IMPORT ---")
print(f"Arquivo sendo executado (__file__): {__file__}")
print(f"Diretório do arquivo: {os.path.dirname(__file__)}")
print(f"Diretório absoluto do arquivo: {os.path.abspath(os.path.dirname(__file__))}")
print(f"Current Working Directory (os.getcwd()): {os.getcwd()}")
print("Conteúdo de sys.path:")
for i, p in enumerate(sys.path):
    print(f"  sys.path[{i}]: {p}")
print("--- FIM DO BLOCO DE DEPURAÇÃO SYS.PATH ---")
# ----

try:
    from evolux_engine.core.agent import Agent
    from evolux_engine.core.context_manager import ContextManager
    from evolux_engine.utils.env_vars import load_env_variables, EVOLUX_PROJECT_BASE_DIR
    from evolux_engine.utils.logging_utils import setup_logging
except ModuleNotFoundError as e:
    print(f"\n!!!!!! ERRO AO IMPORTAR MODULO !!!!!!")
    print(f"Erro específico: {e}")
    print(f"Python tentou encontrar o pacote '{e.name}' nos caminhos listados acima.")
    print(f"Verifique se o diretório '{os.path.join(os.getcwd(), e.name)}' existe e é um pacote Python (contém __init__.py).")
    sys.exit(1)
except ImportError as e:
    print(f"\n!!!!!! ERRO GERAL DE IMPORTAÇÃO !!!!!!")
    print(f"Erro específico: {e}")
    sys.exit(1)


# Configurar o logging o mais cedo possível
setup_logging()

# Criar um logger para este arquivo específico (run.py)
log = logging.getLogger(__name__) # Usar __name__ é o padrão (será '__main__' aqui)

def main():
    log.info("--- Iniciando a execução a partir de run.py ---")
    # Removi o log do Python Path, pois o debug de sys.path acima é mais completo.

    log.info("Carregando variáveis de ambiente...")
    load_env_variables()

    log.info(f"EVOLUX_OPENROUTER_API_KEY: {'********' if os.getenv('EVOLUX_OPENROUTER_API_KEY') else 'None'}")
    log.info(f"EVOLUX_PROJECT_BASE_DIR: {EVOLUX_PROJECT_BASE_DIR}")
    log.info(f"EVOLUX_LLM_PROVIDER: {os.getenv('EVOLUX_LLM_PROVIDER')}")

    parser = argparse.ArgumentParser(description="Evolux Engine - Agente Autônomo de Desenvolvimento")
    parser.add_argument("--goal", type=str, required=True, help="O objetivo principal para o agente.")
    parser.add_argument("--project-id", type=str, help="ID de um projeto existente para continuar.")

    args = parser.parse_args()

    try:
        project_base_dir = EVOLUX_PROJECT_BASE_DIR
        context_manager = ContextManager(base_dir=project_base_dir)

        if args.project_id:
            log.info(f"Carregando projeto existente: {args.project_id}")
            # context_manager.load_project_context(args.project_id) # Certifique-se que este método existe e funciona
        else:
            log.info(f"Criando novo projeto para o objetivo: {args.goal}")
            context_manager.create_project_context(args.goal) # Método chamado no seu log original

        agent = Agent(goal=args.goal, context_manager=context_manager)
        agent.run()

        log.info("--- Execução de run.py Concluída ---")

    except Exception as e:
        log.error(f"Erro Crítico na função main: {e}", exc_info=True)
        print(f"Erro Crítico: {e}")
        print("Verifique os logs (console e/ou arquivo logs/evolux_engine.log) para detalhes.")
        sys.exit(1)

if __name__ == "__main__":
    main()
