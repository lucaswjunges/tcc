import sys
from pathlib import Path
from typing import Optional, List

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define o diretório base do projeto
# __file__ é o settings.py -> .parent é evolux_engine/ -> .parent.parent é a raiz do projeto
BASE_PROJECT_DIR_PATH = Path(__file__).resolve().parent.parent
# Caminho absoluto para o arquivo .env
ENV_FILE_PATH = BASE_PROJECT_DIR_PATH / ".env"

# Debug inicial para verificar o caminho do .env
sys.stderr.write(f"[settings.py DEBUG] Inicializando evolux_engine.settings.\n")
sys.stderr.write(f"[settings.py DEBUG] BASE_PROJECT_DIR_PATH: {BASE_PROJECT_DIR_PATH}\n")
sys.stderr.write(f"[settings.py DEBUG] Tentando carregar .env de: {ENV_FILE_PATH}\n")
if ENV_FILE_PATH.exists():
    sys.stderr.write(f"[settings.py DEBUG] Arquivo .env ENCONTRADO em: {ENV_FILE_PATH}\n")
else:
    sys.stderr.write(f"[settings.py DEBUG] ATENÇÃO: Arquivo .env NÃO ENCONTRADO em: {ENV_FILE_PATH}\n")


class EvoluxSettings(BaseSettings):
    # --- Chaves de API ---
    # Campo Python: OPENROUTER_API_KEY | .env var: EVOLUX_OPENROUTER_API_KEY
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias="EVOLUX_OPENROUTER_API_KEY"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias="EVOLUX_OPENAI_API_KEY"
    )

    # --- Configurações do Projeto ---
    PROJECT_BASE_DIR: str = Field(
        # O default será usado se EVOLUX_PROJECT_BASE_DIR não estiver no .env ou ambiente
        default=str(BASE_PROJECT_DIR_PATH / "project_workspaces"),
        validation_alias="EVOLUX_PROJECT_BASE_DIR"
    )

    # --- Configurações de LLM ---
    LLM_PROVIDER: str = Field(default="openrouter", validation_alias="EVOLUX_LLM_PROVIDER")
    MODEL_PLANNER: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", validation_alias="EVOLUX_MODEL_PLANNER")
    MODEL_EXECUTOR: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", validation_alias="EVOLUX_MODEL_EXECUTOR")
    MODEL_VALIDATOR: Optional[str] = Field(default=None, validation_alias="EVOLUX_MODEL_VALIDATOR")
    HTTP_REFERER: Optional[HttpUrl] = Field(default="http://localhost:3000", validation_alias="EVOLUX_HTTP_REFERER") # type: ignore
    APP_TITLE: Optional[str] = Field(default="Evolux Engine (TCC)", validation_alias="EVOLUX_APP_TITLE")

    # --- Configurações de Execução ---
    MAX_CONCURRENT_TASKS: int = Field(default=3, validation_alias="EVOLUX_MAX_CONCURRENT_TASKS")
    MAX_ITERATIONS: int = Field(default=10, validation_alias="EVOLUX_MAX_ITERATIONS")
    MAX_REPLAN_ATTEMPTS: int = Field(default=3, validation_alias="EVOLUX_MAX_REPLAN_ATTEMPTS")

    # --- Configurações de Logging ---
    LOGGING_LEVEL: str = Field(default="INFO", validation_alias="EVOLUX_LOGGING_LEVEL")
    LOG_TO_FILE: bool = Field(default=False, validation_alias="EVOLUX_LOG_TO_FILE")
    LOG_FILE_PATH: str = Field(
        default=str(BASE_PROJECT_DIR_PATH / "logs" / "evolux_engine.log"),
        validation_alias="EVOLUX_LOG_FILE_PATH"
    )
    LOG_LEVEL_FILE: str = Field(default="DEBUG", validation_alias="EVOLUX_LOG_LEVEL_FILE")
    LOG_FILE_ROTATION: str = Field(default="10 MB", validation_alias="EVOLUX_LOG_FILE_ROTATION")
    LOG_FILE_RETENTION: str = Field(default="7 days", validation_alias="EVOLUX_LOG_FILE_RETENTION")
    LOG_SERIALIZE_JSON: bool = Field(default=False, validation_alias="EVOLUX_LOG_SERIALIZE_JSON")
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),       # Pydantic usará este arquivo
        env_file_encoding='utf-8',
        extra='ignore',                   # Ignora variáveis extras no .env ou ambiente
        case_sensitive=False              # Nomes de variáveis de ambiente não são case-sensitive
                                            # para correspondência com validation_alias. Pydantic normaliza
                                            # os nomes das env vars para minúsculas antes de comparar.
    )

# Instancia as configurações. Esta é a instância singleton que será importada.
try:
    settings = EvoluxSettings()
    sys.stderr.write(f"[settings.py DEBUG] Instância 'settings' criada.\n")
    # Logar o valor da chave API imediatamente após a criação
    key_value = settings.OPENROUTER_API_KEY
    key_display = f"'{key_value[:6]}...{key_value[-4:]}'" if key_value and len(key_value) > 10 else str(key_value)
    sys.stderr.write(f"[settings.py DEBUG] settings.OPENROUTER_API_KEY (após init): {key_display}\n")
    if not key_value:
        sys.stderr.write(f"[settings.py DEBUG] ALERTA: OPENROUTER_API_KEY é None após instanciação!\n")

except Exception as e:
    sys.stderr.write(f"[settings.py DEBUG] ERRO FATAL ao instanciar EvoluxSettings: {e}\n")
    # Para o programa não quebrar totalmente na importação se algo der muito errado
    # Em um cenário real, você poderia querer levantar a exceção aqui.
    class FallbackSettings:
        def __getattr__(self, name): return None # Retorna None para qualquer atributo
    settings = FallbackSettings()
    sys.stderr.write(f"[settings.py DEBUG] Usando FallbackSettings devido a erro.\n")

sys.stderr.write(f"[settings.py DEBUG] Fim de evolux_engine.settings.py.\n")

