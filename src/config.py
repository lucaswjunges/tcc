from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict
import os

class SystemConfig(BaseSettings):
    """
    Configurações do sistema carregadas de variáveis de ambiente ou de um arquivo .env.
    O prefixo 'EVOLUX_' é usado para as variáveis (ex: EVOLUX_OPENROUTER_API_KEY).
    """
    openrouter_api_key: str
    project_base_dir: str = "/home/lucas-junges/Documents/evolux-engine"
    project_workspace_dir: str = "project_workspaces"
    llm_provider: str = "openrouter"

    # Mapeamento dos modelos pode ser definido via variáveis de ambiente, se necessário
    MODEL_PLANNER: str = "anthropic/claude-3-haiku"
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku"

    model_config = SettingsConfigDict(
        env_file=".env",  # Caminho relativo ao arquivo .env
        env_prefix="EVOLUX_",  # Prefixo das variáveis de ambiente
        extra="ignore"  # Ignora campos extras no .env
    )

# Verifique se as variáveis de ambiente estão sendo carregadas
print("Carregando variáveis de ambiente...")
print(f"EVOLUX_OPENROUTER_API_KEY: {os.getenv('EVOLUX_OPENROUTER_API_KEY')}")
print(f"EVOLUX_PROJECT_BASE_DIR: {os.getenv('EVOLUX_PROJECT_BASE_DIR')}")
print(f"EVOLUX_LLM_PROVIDER: {os.getenv('EVOLUX_LLM_PROVIDER')}")

# Instancie SystemConfig para carregar as configurações
settings = SystemConfig()

# Exportar os campos diretamente para o escopo global (opcional)

OPENROUTER_API_KEY = settings.openrouter_api_key
PROJECT_BASE_DIR = settings.project_base_dir
PROJECT_WORKSPACE_DIR = settings.project_workspace_dir
LLM_PROVIDER = settings.llm_provider
