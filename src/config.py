from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict, Optional
import os

class SystemConfig(BaseSettings):
    """
    Configurações do sistema carregadas de variáveis de ambiente ou de um arquivo .env.
    O prefixo 'EVOLUX_' é usado para das variáveis (ex: EVOLUX_OPENROUTER_API_KEY).
    """
    # Configurações de API
    openrouter_api_key: str = Field(..., description="Chave de API para acesso ao OpenRouter")
    
    # Configurações de diretórios
    project_base_dir: str = Field(
        default=os.path.join(os.getcwd(), "project_workspaces"),
        description="Diretório base onde os projetos serão armazenados"
    )
    project_workspace_dir: str = Field(
        default="workspaces",
        description="Subdiretório para armazenar os workspaces dos projetos"
    )
    
    # Configurações de LLM
    llm_provider: str = Field(
        default="openrouter",
        description="Provedor de LLM a ser utilizado"
    )
    model_planner: str = Field(
        default="anthropic/claude-3-haiku",
        description="Modelo a ser usado para tarefas de planejamento"
    )
    model_executor: str = Field(
        default="anthropic/claude-3-haiku",
        description="Modelo a ser usado para tarefas de execução"
    )
    
    # Configurações avançadas
    max_concurrent_tasks: int = Field(
        default=5,
        description="Número máximo de tarefas que podem ser executadas simultaneamente"
    )
    logging_level: str = Field(
        default="INFO",
        description="Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Configuração do Pydantic para carregar variáveis de ambiente
    model_config = SettingsConfigDict(
        env_file=".env",  # Caminho relativo ao arquivo .env
        env_prefix="EVOLUX_",  # Prefixo das variáveis de ambiente
        extra="ignore"  # Ignora campos extras no .env
    )

# Verificação de carregamento das variáveis de ambiente
print("Carregando variáveis de ambiente...")
print(f"EVOLUX_OPENROUTER_API_KEY: {'*' * 8}")  # Evita expor a chave de API
print(f"EVOLUX_PROJECT_BASE_DIR: {os.getenv('EVOLUX_PROJECT_BASE_DIR')}")
print(f"EVOLUX_LLM_PROVIDER: {os.getenv('EVOLUX_LLM_PROVIDER')}")

# Instanciar as configurações (carrega automaticamente do .env e/ou variáveis de ambiente)
settings: SystemConfig = SystemConfig()

# Exportar os campos diretamente para o escopo global (opcional)
OPENROUTER_API_KEY: str = settings.openrouter_api_key
PROJECT_BASE_DIR: str = settings.project_base_dir
PROJECT_WORKSPACE_DIR: str = settings.project_workspace_dir
LLM_PROVIDER: str = settings.llm_provider
MODEL_PLANNER: str = settings.model_planner
MODEL_EXECUTOR: str = settings.model_executor
MAX_CONCURRENT_TASKS: int = settings.max_concurrent_tasks
LOGGING_LEVEL: str = settings.logging_level
