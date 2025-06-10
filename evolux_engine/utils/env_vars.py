# Conteúdo para: evolux_engine/utils/env_vars.py
import os
from typing import Optional, Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Carrega as variáveis do .env para o ambiente ANTES do Pydantic tentar lê-las.
# É importante que load_dotenv() seja chamado antes de SystemConfig()
# se você quiser que .env tenha prioridade ou preencha o que não está no ambiente.
# Pydantic-settings também pode ler .env diretamente se model_config.env_file for definido,
# tornando esta chamada explícita de load_dotenv() às vezes redundante,
# mas não prejudicial.
load_dotenv()

class SystemConfig(BaseSettings):
    """
    Configurações do sistema carregadas de variáveis de ambiente e arquivos .env.
    Utiliza um prefixo EVOLUX_ para as variáveis de ambiente.
    """
    OPENROUTER_API_KEY: Optional[str] = Field(None, validation_alias='EVOLUX_OPENROUTER_API_KEY_ALIAS_TEST') # Teste com alias se o nome direto não funcionar
    # OPENROUTER_API_KEY: Optional[str] = None # Se o prefixo funcionar, esta é a forma normal
    OPENAI_API_KEY: Optional[str] = None
    PROJECT_BASE_DIR: str = Field(default_factory=lambda: os.path.join(os.getcwd(), "project_workspaces"))
    LLM_PROVIDER: Literal["openrouter", "openai"] = "openrouter"
    MODEL_PLANNER: str = "anthropic/claude-3-haiku"
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku"
    MAX_CONCURRENT_TASKS: int = 5
    LOGGING_LEVEL: str = "INFO"

    # Pydantic V2 model_config
    model_config = SettingsConfigDict(
        env_prefix="EVOLUX_",  # Procura por EVOLUX_OPENROUTER_API_KEY, EVOLUX_PROJECT_BASE_DIR, etc.
        env_file=".env",        # Explicitamente diz para ler do .env
        env_file_encoding="utf-8",
        extra="ignore",         # Ignora variáveis de ambiente extras não definidas na classe
        case_sensitive=False    # Nomes de variáveis de ambiente não são case-sensitive
    )

    # Para depuração, mostrar de onde os valores vieram
    # @root_validator(pre=True)
    # def log_settings_sources(cls, values):
    #     print("Raw environment variables being considered by Pydantic:")
    #     for key in cls.model_fields:
    #         env_var_name_with_prefix = cls.model_config.get('env_prefix', '') + key.upper()
    #         env_var_name_direct = key.upper()
    #         print(f"  For field '{key}':")
    #         print(f"    Checking env var (with prefix): {env_var_name_with_prefix} -> {os.getenv(env_var_name_with_prefix)}")
    #         print(f"    Checking env var (direct): {env_var_name_direct} -> {os.getenv(env_var_name_direct)}")
    #     return values


# Cria uma instância única das configurações para ser importada por outros módulos
settings = SystemConfig()

# Função para carregar e opcionalmente imprimir as variáveis (pode ser usada no início do run.py)
def load_env_variables():
    print("Variáveis de ambiente carregadas (via Pydantic settings):")
    print(f"  EVOLUX_OPENROUTER_API_KEY (campo OPENROUTER_API_KEY): {'********' if settings.OPENROUTER_API_KEY else 'None'}")
    print(f"  EVOLUX_PROJECT_BASE_DIR (campo PROJECT_BASE_DIR): {settings.PROJECT_BASE_DIR}")
    print(f"  EVOLUX_LLM_PROVIDER (campo LLM_PROVIDER): {settings.LLM_PROVIDER}")
    # Adicione outras variáveis que queira depurar
    return settings

# Para compatibilidade com o import que run.py faz, se ele ainda espera estas:
# EVOLUX_PROJECT_BASE_DIR = settings.PROJECT_BASE_DIR
# EVOLUX_LLM_PROVIDER = settings.LLM_PROVIDER
# EVOLUX_OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
# OPENAI_API_KEY = settings.OPENAI_API_KEY
# ... mas o ideal é que outros módulos importem 'settings' e use 'settings.FIELD_NAME'
