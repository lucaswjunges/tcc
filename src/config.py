# src/config.py (VERSÃO SIMPLIFICADA E FINAL)

from pydantic_settings import BaseSettings, SettingsConfigDict
# CORREÇÃO: Importa o modelo de dados do nosso arquivo de contratos unificado.
from .schemas.contracts import SystemConfig, ModelMapping

class Settings(BaseSettings):
    """
    Carrega as configurações a partir de variáveis de ambiente ou de um arquivo .env.
    O prefixo 'EVOLUX_' é usado para as variáveis (ex: EVOLUX_OPENROUTER_API_KEY).
    """
    OPENROUTER_API_KEY: str
    
    # Mapeamento dos modelos pode ser definido via variáveis de ambiente, se necessário
    MODEL_PLANNER: str = "anthropic/claude-3-haiku"
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku"

    model_config = SettingsConfigDict(env_prefix='EVOLUX_', env_file='.env', env_file_encoding='utf-8', extra='ignore')

# Cria uma instância única das configurações para ser usada em todo o aplicativo
_settings_instance = Settings()

# Monta o objeto SystemConfig a partir das configurações carregadas
settings = SystemConfig(
    openrouter_api_key=_settings_instance.OPENROUTER_API_KEY,
    model_mapping=ModelMapping(
        planner=_settings_instance.MODEL_PLANNER,
        executor=_settings_instance.MODEL_EXECUTOR
    )
)
