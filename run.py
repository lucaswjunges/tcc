# Conteúdo para: run.py
import argparse
import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
# Isso permite que 'evolux_engine' seja importado como um pacote de nível superior
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---- DEBUG SYS.PATH ----
print("--- DEBUG SYS.PATH ANTES DO IMPORT ---")
print(f"Arquivo sendo executado (__file__): {__file__}")
print(f"Diretório do arquivo: {os.path.dirname(__file__)}")
print(f"Diretório absoluto do arquivo: {project_root}")
print(f"Current Working Directory (os.getcwd()): {os.getcwd()}")
print("Conteúdo de sys.path:")
for i, path_entry in enumerate(sys.path):
    print(f"  sys.path[{i}]: {path_entry}")
print("--- FIM DO BLOCO DE DEPURAÇÃO SYS.PATH ---")
# ---- FIM DEBUG ----

# Agora importe de evolux_engine
# A função load_env_variables agora retorna a instância settings
from evolux_engine.utils.env_vars import load_env_variables, settings
from evolux_engine.core.agent import Agent
from evolux_engine.utils.logging_utils import log # Importa o logger configurado

def main():
    # Carrega as variáveis de ambiente usando a função de env_vars.py
    # Esta chamada também imprime as variáveis para depuração.
    load_env_variables()

    # Agora você pode acessar as configurações via 'settings'
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
    # Adicione outros argumentos conforme necessário

    args = parser.parse_args()

    log.info(f"Objetivo recebido: {args.goal}")

    agent = Agent(goal=args.goal)
    # agent.plan_and_execute() # Ou o método principal do seu agente
    log.info("Planejamento iniciado (simulação).") # Simulação
    # Simular alguma ação do agente
    try:
        llm_client_instance = agent.llm_factory.get_llm_client()
        # response = llm_client_instance.generate_response(prompt="Olá, mundo!")
        # log.info(f"Resposta simulada do LLM: {response}")
        log.info("Agente obteve cliente LLM.")
        log.info("Execução do agente (simulada) concluída.")
    except Exception as e:
        log.error(f"Erro durante a execução do agente: {e}", exc_info=True)


if __name__ == "__main__":
    main()
