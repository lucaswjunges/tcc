import sys # Necessário para o handler de log de debug
from typing import Optional, List
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
# from pydantic_settings import PydanticSettingsSource # Descomente se usar settings_customise_sources

# --- Configuração de Logger para Debug Interno do Settings ---
# Usamos um logger separado aqui para garantir que as mensagens de debug de carregamento
# apareçam mesmo que o logging principal ainda não esteja totalmente configurado
# ou se settings.py for importado antes do setup_logging.
try:
    from loguru import logger as settings_logger
    IS_LOGURU_AVAILABLE = True
    settings_logger.remove() # Remove handlers padrão para evitar duplicação se loguru já estiver configurado
    # Adiciona um handler simples para imprimir no stderr, fácil de ver no início
    settings_logger.add(lambda msg_record: print(msg_record, file=sys.stderr, flush=True), 
                        level="DEBUG", 
                        format="<level>[Settings Debug]</level> {time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}")
except ImportError:
    IS_LOGURU_AVAILABLE = False
    # Fallback para print simples se loguru não estiver disponível neste ponto
    def simple_debug_print(message):
        print(f"[Settings Debug Fallback] | DEBUG    | {message}", file=sys.stderr, flush=True)
    class MockLogger:
        def debug(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def info(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def warning(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
        def error(self, msg, **kwargs): simple_debug_print(f"{msg} {kwargs if kwargs else ''}")
    settings_logger = MockLogger()
# --- Fim da Configuração de Logger para Debug Interno ---


# Define o diretório base do projeto para facilitar a construção de caminhos
# __file__ é o caminho para este arquivo (settings.py)
# .resolve() torna o caminho absoluto
# .parent é o diretório 'evolux_engine'
# .parent.parent é o diretório raiz do projeto (onde .env e run.py devem estar)
BASE_PROJECT_DIR_PATH = Path(__file__).resolve().parent.parent
EXPECTED_ENV_FILE_PATH = BASE_PROJECT_DIR_PATH / '.env'

settings_logger.debug(f"Calculado BASE_PROJECT_DIR_PATH: {BASE_PROJECT_DIR_PATH}")
settings_logger.debug(f"Caminho esperado para o arquivo .env: {EXPECTED_ENV_FILE_PATH}")

if EXPECTED_ENV_FILE_PATH.exists():
    settings_logger.info(f"Verificação de existência: Arquivo .env ENCONTRADO em '{EXPECTED_ENV_FILE_PATH}'.")
    try:
        with open(EXPECTED_ENV_FILE_PATH, "r", encoding="utf-8") as f_env:
            env_content_preview = f_env.read(200) # Lê os primeiros 200 chars
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
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        env="EVOLUX_OPENROUTER_API_KEY", # Nome da variável no ambiente ou .env
        description="API Key for OpenRouter.ai."
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        env="EVOLUX_OPENAI_API_KEY",
        description="API Key for OpenAI (if used directly)."
    )

    # --- Configurações do Projeto ---
    PROJECT_BASE_DIR: str = Field(
        default=str(BASE_PROJECT_DIR_PATH / "project_workspaces"),
        env="EVOLUX_PROJECT_BASE_DIR",
        description="Diretório base onde os workspaces dos projetos serão criados."
    )

    # --- Configurações de LLM ---
    LLM_PROVIDER: str = Field(
        default="openrouter",
        env="EVOLUX_LLM_PROVIDER",
        description="Provedor LLM padrão (ex: 'openrouter', 'openai')."
    )
    MODEL_PLANNER: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free",
        env="EVOLUX_MODEL_PLANNER",
        description="Modelo LLM padrão para o agente de planejamento."
    )
    MODEL_EXECUTOR: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free",
        env="EVOLUX_MODEL_EXECUTOR",
        description="Modelo LLM padrão para o agente executor de tarefas."
    )
    MODEL_VALIDATOR: Optional[str] = Field(
        default=None,
        env="EVOLUX_MODEL_VALIDATOR",
        description="Modelo LLM padrão para o agente validador semântico (opcional)."
    )
    HTTP_REFERER: Optional[HttpUrl] = Field(
        default="http://localhost:3000",
        env="EVOLUX_HTTP_REFERER",
        description="HTTP Referer a ser enviado para APIs como OpenRouter."
    )
    APP_TITLE: Optional[str] = Field(
        default="Evolux Engine (TCC)",
        env="EVOLUX_APP_TITLE",
        description="X-Title a ser enviado para APIs como OpenRouter (nome do seu app)."
    )

    # --- Configurações de Execução ---
    MAX_CONCURRENT_TASKS: int = Field(
        default=3,
        env="EVOLUX_MAX_CONCURRENT_TASKS",
        description="Número máximo de tarefas que o executor pode processar em paralelo."
    )
    MAX_ITERATIONS: int = Field(
        default=10,
        env="EVOLUX_MAX_ITERATIONS",
        description="Número máximo de iterações para um objetivo."
    )
    MAX_REPLAN_ATTEMPTS: int = Field(
        default=3,
        env="EVOLUX_MAX_REPLAN_ATTEMPTS",
        description="Número máximo de tentativas de replanejamento para uma tarefa falha."
    )

    # --- Configurações de Logging ---
    LOGGING_LEVEL: str = Field(default="INFO", env="EVOLUX_LOGGING_LEVEL")
    LOG_TO_FILE: bool = Field(default=False, env="EVOLUX_LOG_TO_FILE")
    LOG_FILE_PATH: str = Field(default=str(BASE_PROJECT_DIR_PATH / "logs" / "evolux_engine.log"), env="EVOLUX_LOG_FILE_PATH")
    LOG_LEVEL_FILE: str = Field(default="DEBUG", env="EVOLUX_LOG_LEVEL_FILE")
    LOG_FILE_ROTATION: str = Field(default="10 MB", env="EVOLUX_LOG_FILE_ROTATION")
    LOG_FILE_RETENTION: str = Field(default="7 days", env="EVOLUX_LOG_FILE_RETENTION")
    LOG_SERIALIZE_JSON: bool = Field(default=False, env="EVOLUX_LOG_SERIALIZE_JSON")
    
    model_config = SettingsConfigDict(
        env_file=str(EXPECTED_ENV_FILE_PATH), # Pydantic tentará carregar deste arquivo
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False # Nomes de variáveis de ambiente não são case_sensitive por padrão
    )

    # --- Debug Avançado Pydantic (descomente se necessário) ---
    # @classmethod
    # def settings_customise_sources(
    #     cls,
    #     settings_cls: type[BaseSettings],
    #     init_settings: PydanticSettingsSource,
    #     env_settings: PydanticSettingsSource,
    #     dotenv_settings: PydanticSettingsSource, # Este é o que carrega do env_file
    #     file_secret_settings: PydanticSettingsSource,
    # ) -> tuple[PydanticSettingsSource, ...]:
    #     
    #     # Loga o que cada fonte de configuração encontrou (ou não)
    #     # Isso é bem verboso, mas pode mostrar exatamente de onde Pydantic está pegando cada valor
    #     settings_logger.debug(f"Pydantic - init_settings (argumentos do construtor): {init_settings.load_config()}")
    #     settings_logger.debug(f"Pydantic - env_settings (variáveis de ambiente do sistema): {env_settings.load_config().get('EVOLUX_OPENROUTER_API_KEY', 'NÃO PRESENTE NAS VARS DE AMBIENTE')}")
    #     
    #     dotenv_config = dotenv_settings.load_config()
    #     settings_logger.debug(f"Pydantic - dotenv_settings (do arquivo .env): {dotenv_config.get('EVOLUX_OPENROUTER_API_KEY', 'NÃO ENCONTRADO NO .ENV PELO PYDANTIC')}")
    #     settings_logger.debug(f"Pydantic - Todos os valores do dotenv_settings: {dotenv_config}")
    #     
    #     settings_logger.debug(f"Pydantic - file_secret_settings (Docker secrets, etc.): {file_secret_settings.load_config()}")
    #     
    #     return (
    #         init_settings,
    #         env_settings,
    #         dotenv_settings,
    #         file_secret_settings,
    #     )

# --- Instanciação das Configurações ---
settings_logger.info("Preparando para instanciar EvoluxSettings...")
try:
    settings = EvoluxSettings()
    settings_logger.info("EvoluxSettings instanciado com sucesso.")
    SETTINGS_LOADED_SUCCESSFULLY = True
except Exception as e:
    settings_logger.error(f"Falha ao instanciar EvoluxSettings: {e}", exc_info=True)
    SETTINGS_LOADED_SUCCESSFULLY = False
    # Se falhar aqui, o programa provavelmente não pode continuar.
    # Você pode querer levantar a exceção ou sair.
    # Para este debug, vamos permitir que continue para ver os logs.
    class FallbackSettings: # Cria um objeto settings com defaults para o resto do código não quebrar imediatamente
        OPENROUTER_API_KEY = None
        # Adicione outros campos com seus valores default se necessário para o programa não quebrar na importação
        PROJECT_BASE_DIR = str(BASE_PROJECT_DIR_PATH / "project_workspaces_fallback")
        LLM_PROVIDER = "openrouter"
        MODEL_PLANNER = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        MODEL_EXECUTOR = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        HTTP_REFERER = None
        APP_TITLE = "Evolux Engine (Fallback)"
        LOGGING_LEVEL = "INFO"
        # ... etc
    settings = FallbackSettings()


# --- Logar Valores Carregados (após Pydantic ter feito seu trabalho) ---
if SETTINGS_LOADED_SUCCESSFULLY:
    settings_logger.info("--- Valores Finais Carregados em 'settings' (Pydantic) ---")
    
    # Acessar model_fields da classe para Pydantic v2.11+
    if hasattr(EvoluxSettings, 'model_fields'):
        for field_name in EvoluxSettings.model_fields:
            value = getattr(settings, field_name, "CAMPO_NAO_ENCONTRADO_NA_INSTANCIA")
            env_var_name = EvoluxSettings.model_fields[field_name].validation_alias or field_name.upper()
            
            if "API_KEY" in env_var_name and value and isinstance(value, str) and len(value) > 4:
                value_display = f"'{value[:4]}...{value[-4:]}'" if len(value) > 8 else "'****'"
            else:
                value_display = f"'{value}'" if isinstance(value, str) else value

            default_value = EvoluxSettings.model_fields[field_name].default
            source_info = "(do default)" if value == default_value and default_value is not None else ""
            if value is None and default_value is None:
                source_info = "(None, default também é None)"


            if field_name == "OPENROUTER_API_KEY":
                if value:
                    settings_logger.info(f"  >>>> {field_name} ({env_var_name}): {value_display} {source_info} <<<<")
                else:
                    settings_logger.warning(f"  >>>> {field_name} ({env_var_name}): {value_display} {source_info} - AINDA ESTÁ NONE! <<<<")
            else:
                settings_logger.debug(f"  {field_name} ({env_var_name}): {value_display} {source_info}")
    else:
        settings_logger.warning("Não foi possível iterar por EvoluxSettings.model_fields para logar valores carregados.")

    settings_logger.debug(f"Pydantic usou o arquivo .env: '{settings.model_config.get('env_file')}'")
    settings_logger.info("--- Fim dos Valores Finais Carregados ---")
else:
    settings_logger.error("Settings não foram carregadas corretamente. Verifique os logs anteriores.")

