import os
# from typing import Optional, Literal # Verifique se Literal está aqui se usá-lo
from typing import Optional, Literal # ADICIONADO Literal
# ... resto do arquivo como antes ...

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# ... (o resto do seu arquivo env_vars.py, que já estava bom)
# Certifique-se que SystemConfig tem LLM_PROVIDER: Literal["openrouter", "openai"] = "openrouter"
# e que `from typing import Optional, Literal` esteja no topo.
# O seu arquivo no GitHub parece OK neste ponto.

if load_dotenv(verbose=True, override=True):
    print("Arquivo .env carregado por python-dotenv.")
else:
    print("Arquivo .env não encontrado ou não carregado por python-dotenv. Pydantic tentará carregar.")


class SystemConfig(BaseSettings):
    OPENROUTER_API_KEY: Optional[str] = Field(None)
    OPENAI_API_KEY: Optional[str] = Field(None)

    PROJECT_BASE_DIR: str = Field(
        default_factory=lambda: os.path.join(os.path.expanduser("~"), "evolux_engine_project_workspaces") # Melhor usar expanduser
    )
    LLM_PROVIDER: Literal["openrouter", "openai"] = "openrouter"
    MODEL_PLANNER: str = "anthropic/claude-3-haiku-20240307"
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku-20240307"

    MAX_CONCURRENT_TASKS: int = 5
    LOGGING_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="EVOLUX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

settings = SystemConfig()

def load_env_variables(print_vars: bool = False) -> SystemConfig:
    if print_vars:
        print("Variáveis de ambiente carregadas (via Pydantic settings):")
        for key, value in settings.model_dump().items():
            env_var_name = f"{settings.model_config.get('env_prefix', '').upper()}{key.upper()}"
            display_value = value
            if "API_KEY" in key.upper() and value is not None and isinstance(value, str) and len(value) > 9 : # Adicionado isinstance e len check
                display_value = f"{value[:5]}********{value[-4:]}"
            elif "API_KEY" in key.upper() and value is not None:
                 display_value = "********"

            print(f"  {env_var_name} (campo {key}): {display_value}")
    return settings
