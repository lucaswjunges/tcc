import os
from typing import Optional, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Garante que load_dotenv() seja chamado para carregar o arquivo .env
# O Pydantic também tentará carregar, mas chamar explicitamente é uma boa prática.
# verbose=True pode ajudar a depurar se o .env não está sendo encontrado.
# override=True fará com que as variáveis do .env sobrescrevam as do sistema.
if load_dotenv(verbose=True, override=True):
    print("Arquivo .env carregado por python-dotenv.")
else:
    print("Arquivo .env não encontrado ou não carregado por python-dotenv. Pydantic tentará carregar.")


class SystemConfig(BaseSettings):
    """
    Configurações do sistema carregadas de variáveis de ambiente ou arquivo .env.
    O prefixo EVOLUX_ é esperado nas variáveis de ambiente.
    Ex: EVOLUX_OPENROUTER_API_KEY será mapeado para settings.OPENROUTER_API_KEY
    """
    OPENROUTER_API_KEY: Optional[str] = Field(None)
    OPENAI_API_KEY: Optional[str] = Field(None)

    PROJECT_BASE_DIR: str = Field(
        default_factory=lambda: os.path.join(os.getcwd(), "project_workspaces")
    )
    LLM_PROVIDER: Literal["openrouter", "openai"] = "openrouter"
    MODEL_PLANNER: str = "anthropic/claude-3-haiku-20240307" # Usar nomes de modelo completos
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku-20240307"

    MAX_CONCURRENT_TASKS: int = 5
    LOGGING_LEVEL: str = "INFO"

    # Configuração do Pydantic para carregar variáveis
    model_config = SettingsConfigDict(
        env_prefix="EVOLUX_",      # Ex: EVOLUX_LOGGING_LEVEL
        env_file=".env",           # Nome do arquivo .env a ser procurado
        env_file_encoding="utf-8", # Encoding do arquivo .env
        extra="ignore",            # Ignorar variáveis extras no .env que não estão no modelo
        case_sensitive=False       # Nomes de env vars geralmente são case-insensitive na prática
    )

# Instância única das configurações
settings = SystemConfig()

# Função para carregar e opcionalmente imprimir as variáveis
# (pode ser chamada no início do run.py)
def load_env_variables(print_vars: bool = False) -> SystemConfig:
    """
    Retorna a instância das configurações.
    Opcionalmente, imprime as variáveis carregadas (com chaves API mascaradas).
    """
    if print_vars:
        print("Variáveis de ambiente carregadas (via Pydantic settings):")
        for key, value in settings.model_dump().items():
            env_var_name = f"{settings.model_config.get('env_prefix', '').upper()}{key.upper()}"
            display_value = value
            if "API_KEY" in key.upper() and value is not None:
                display_value = f"{value[:5]}********{value[-4:]}" if len(value) > 9 else "********"
            
            print(f"  {env_var_name} (campo {key}): {display_value}")
    return settings

if __name__ == "__main__":
    # Para testar o carregamento das configurações diretamente
    print("Executando env_vars.py diretamente para teste:")
    current_settings = load_env_variables(print_vars=True)
    # Você pode acessar as configurações assim:
    # print(f"Project base dir: {current_settings.PROJECT_BASE_DIR}")
    # print(f"OpenRouter Key: {'Present' if current_settings.OPENROUTER_API_KEY else 'Not Present'}")
