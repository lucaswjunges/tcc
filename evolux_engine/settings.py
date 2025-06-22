import sys
from typing import Optional, List
from pathlib import Path

# --- INÍCIO DA MODIFICAÇÃO ---
# Importa a função para ler o .env diretamente
from dotenv import dotenv_values
# --- FIM DA MODIFICAÇÃO ---

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from loguru import logger as settings_logger
    IS_LOGURU_AVAILABLE = True
    settings_logger.remove()
    settings_logger.add(lambda msg_record: print(msg_record, file=sys.stderr, flush=True), 
                        level="DEBUG", 
                        format="<level>[Settings Debug]</level> {time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}")
except ImportError:
    IS_LOGURU_AVAILABLE = False
    def simple_debug_print(message):
        print(f"[Settings Debug Fallback] | DEBUG    | {message}", file=sys.stderr, flush=True)
    class MockLogger:
        def debug(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def info(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def warning(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def error(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
    settings_logger = MockLogger()

BASE_PROJECT_DIR_PATH = Path(__file__).resolve().parent.parent
EXPECTED_ENV_FILE_PATH = BASE_PROJECT_DIR_PATH / '.env'

settings_logger.debug(f"Calculado BASE_PROJECT_DIR_PATH: {BASE_PROJECT_DIR_PATH}")
settings_logger.debug(f"Caminho esperado para o arquivo .env: {EXPECTED_ENV_FILE_PATH}")

if EXPECTED_ENV_FILE_PATH.exists():
    settings_logger.info(f"Verificação de existência: Arquivo .env ENCONTRADO em '{EXPECTED_ENV_FILE_PATH}'.")
    try:
        with open(EXPECTED_ENV_FILE_PATH, "r", encoding="utf-8") as f_env:
            env_content_preview = f_env.read(200)
        settings_logger.debug(f"Conteúdo inicial do .env (primeiros 200 chars): \n---\n{env_content_preview}\n---")
    except Exception as e:
        settings_logger.warning(f"Não foi possível ler o conteúdo do .env para preview: {e}")
else:
    settings_logger.warning(f"Verificação de existência: Arquivo .env NÃO ENCONTRADO em '{EXPECTED_ENV_FILE_PATH}'.")
    settings_logger.warning("Verifique se o arquivo .env está na raiz do projeto e com o nome correto.")


class EvoluxSettings(BaseSettings):
    """
    Configurações do Evolux Engine, carregadas de variáveis de ambiente e/ou arquivo .env.
    """

    # --- Chaves de API ---
    OPENROUTER_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)

    # --- Configurações do Projeto ---
    PROJECT_BASE_DIR: str = Field(default=str(BASE_PROJECT_DIR_PATH / "project_workspaces"))

    # --- Configurações de LLM ---
    LLM_PROVIDER: str = Field(default="openrouter")
    MODEL_PLANNER: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free")
    MODEL_EXECUTOR: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free")
    MODEL_VALIDATOR: Optional[str] = Field(default=None)
    HTTP_REFERER: Optional[HttpUrl] = Field(default="http://localhost:3000")
    APP_TITLE: Optional[str] = Field(default="Evolux Engine (TCC)")

    # --- Configurações de Execução ---
    MAX_CONCURRENT_TASKS: int = Field(default=3)
    MAX_ITERATIONS: int = Field(default=10)
    MAX_REPLAN_ATTEMPTS: int = Field(default=3)

    # --- Configurações de Logging ---
    LOGGING_LEVEL: str = Field(default="INFO")
    LOG_TO_FILE: bool = Field(default=False)
    LOG_FILE_PATH: str = Field(default=str(BASE_PROJECT_DIR_PATH / "logs" / "evolux_engine.log"))
    LOG_LEVEL_FILE: str = Field(default="DEBUG")
    LOG_FILE_ROTATION: str = Field(default="10 MB")
    LOG_FILE_RETENTION: str = Field(default="7 days")
    LOG_SERIALIZE_JSON: bool = Field(default=False)
    
    # Removido model_config daqui para forçar o carregamento manual abaixo
    # model_config = SettingsConfigDict(...)

# --- Instanciação das Configurações ---
settings_logger.info("Preparando para instanciar EvoluxSettings...")
try:
    # --- INÍCIO DA MODIFICAÇÃO ---
    # 1. Carrega os valores do .env para um dicionário, ignorando o cache do sistema.
    #    Os nomes das chaves aqui devem ser SEM o prefixo "EVOLUX_".
    config_from_env_file = {
        key.replace("EVOLUX_", ""): value 
        for key, value in dotenv_values(EXPECTED_ENV_FILE_PATH).items()
    }
    
    # 2. Instancia as settings, passando os valores do arquivo .env diretamente.
    #    Isso força o Pydantic a usar esses valores.
    settings = EvoluxSettings(**config_from_env_file)
    # --- FIM DA MODIFICAÇÃO ---
    
    settings_logger.info("EvoluxSettings instanciado com sucesso.")
    SETTINGS_LOADED_SUCCESSFULLY = True
except Exception as e:
    settings_logger.error(f"Falha ao instanciar EvoluxSettings: {e}", exc_info=True)
    SETTINGS_LOADED_SUCCESSFULLY = False
    # ... (código de fallback permanece o mesmo)
    class FallbackSettings:
        OPENROUTER_API_KEY = None
        GOOGLE_API_KEY = None
        PROJECT_BASE_DIR = str(BASE_PROJECT_DIR_PATH / "project_workspaces_fallback")
        LLM_PROVIDER = "openrouter"
        MODEL_PLANNER = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        MODEL_EXECUTOR = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        HTTP_REFERER = None
        APP_TITLE = "Evolux Engine (Fallback)"
        LOGGING_LEVEL = "INFO"
    settings = FallbackSettings()


# --- Logar Valores Carregados (após Pydantic ter feito seu trabalho) ---
if SETTINGS_LOADED_SUCCESSFULLY:
    # Este bloco de log agora é mais simples e direto
    settings_logger.info("--- Valores Finais Carregados em 'settings' ---")
    for field_name, value in settings.model_dump().items():
        display_value = value
        if "API_KEY" in field_name.upper() and value and isinstance(value, str):
            display_value = f"'{value[:4]}...{value[-4:]}'" if len(value) > 8 else "'****'"
        
        if "API_KEY" in field_name.upper() and not value:
            settings_logger.warning(f"  >>>> {field_name}: {display_value} - ATENÇÃO: CHAVE NÃO CARREGADA! <<<<")
        else:
            settings_logger.info(f"  > {field_name}: {display_value}")
    settings_logger.info("--- Fim dos Valores Finais Carregados ---")
else:
    settings_logger.error("Settings não foram carregadas corretamente. Verifique os logs anteriores.")