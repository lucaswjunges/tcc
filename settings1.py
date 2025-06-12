from typing import Optional, List # Importação corrigida e List adicionada para o futuro
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define o diretório base do projeto para facilitar a construção de caminhos
BASE_PROJECT_DIR_PATH = Path(__file__).resolve().parent.parent # Aponta para a raiz do projeto (onde está run.py)

class EvoluxSettings(BaseSettings):
    """
    Configurações do Evolux Engine, carregadas de variáveis de ambiente e/ou arquivo .env.
    """

    # --- Chaves de API ---
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        env="EVOLUX_OPENROUTER_API_KEY",
        description="API Key for OpenRouter.ai."
    )
    OPENAI_API_KEY: Optional[str] = Field( # Se for usar OpenAI diretamente algum dia
        default=None,
        env="EVOLUX_OPENAI_API_KEY",
        description="API Key for OpenAI (if used directly)."
    )

    # --- Configurações do Projeto ---
    PROJECT_BASE_DIR: str = Field(
        default=str(BASE_PROJECT_DIR_PATH / "project_workspaces"), # Default para '{raiz_do_projeto}/project_workspaces'
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
        default="deepseek/deepseek-r1-0528-qwen3-8b:free", # Exemplo de modelo gratuito
        env="EVOLUX_MODEL_PLANNER",
        description="Modelo LLM padrão para o agente de planejamento."
    )
    MODEL_EXECUTOR: str = Field(
        default="deepseek/deepseek-r1-0528-qwen3-8b:free", # Exemplo de modelo gratuito
        env="EVOLUX_MODEL_EXECUTOR",
        description="Modelo LLM padrão para o agente executor de tarefas."
    )
    MODEL_VALIDATOR: Optional[str] = Field( # Se tiver um agente validador com modelo diferente
        default=None, # Pode usar o mesmo que o executor ou um específico
        env="EVOLUX_MODEL_VALIDATOR",
        description="Modelo LLM padrão para o agente validador semântico (opcional)."
    )
    # Para OpenRouter, estes headers são recomendados para identificação
    HTTP_REFERER: Optional[HttpUrl] = Field( # Usar HttpUrl para validação básica
        default="http://localhost:3000", # Exemplo, ajuste para seu app se tiver um front-end
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
        description="Número máximo de iterações (ciclos de replanejamento/execução) para um objetivo."
    )
    MAX_REPLAN_ATTEMPTS: int = Field(
        default=3,
        env="EVOLUX_MAX_REPLAN_ATTEMPTS",
        description="Número máximo de tentativas de replanejamento para uma tarefa falha."
    )

    # --- Configurações de Logging (para o novo logging_utils.py) ---
    LOGGING_LEVEL: str = Field(
        default="INFO",
        env="EVOLUX_LOGGING_LEVEL",
        description="Nível de log para o console (DEBUG, INFO, WARNING, ERROR, CRITICAL)."
    )
    LOG_TO_FILE: bool = Field(
        default=False,
        env="EVOLUX_LOG_TO_FILE",
        description="Se True, habilita o logging em arquivo."
    )
    LOG_FILE_PATH: str = Field(
        default=str(BASE_PROJECT_DIR_PATH / "logs" / "evolux_engine.log"),
        env="EVOLUX_LOG_FILE_PATH",
        description="Caminho completo para o arquivo de log."
    )
    LOG_LEVEL_FILE: str = Field(
        default="DEBUG",
        env="EVOLUX_LOG_LEVEL_FILE",
        description="Nível de log para o arquivo."
    )
    LOG_FILE_ROTATION: str = Field( # Adicionado para Loguru
        default="10 MB",
        env="EVOLUX_LOG_FILE_ROTATION",
        description="Tamanho para rotação do arquivo de log (ex: '10 MB', '1 week')."
    )
    LOG_FILE_RETENTION: str = Field( # Adicionado para Loguru
        default="7 days",
        env="EVOLUX_LOG_FILE_RETENTION",
        description="Período de retenção para arquivos de log rotacionados."
    )
    LOG_SERIALIZE_JSON: bool = Field(
        default=False,
        env="EVOLUX_LOG_SERIALIZE_JSON",
        description="Se True, os logs no arquivo serão serializados como JSON."
    )
    
    # Configuração do Pydantic para carregar de .env, etc.
    model_config = SettingsConfigDict(
        env_file=str(BASE_PROJECT_DIR_PATH / '.env'), # Garante que .env na raiz do projeto é lido
        env_file_encoding='utf-8',
        extra='ignore',  # Ignora variáveis de ambiente extras que não estão definidas aqui
        case_sensitive=False # Nomes de variáveis de ambiente não são case_sensitive por padrão
    )

# Instância global das configurações, para ser importada em outros módulos
settings = EvoluxSettings()

# Você pode adicionar uma função para imprimir as configurações carregadas ao iniciar, para debug
# if __name__ == "__main__":
#     print("Configurações Carregadas:")
#     for field_name in EvoluxSettings.model_fields:
#         value = getattr(settings, field_name)
#         if "API_KEY" in field_name.upper() and value and isinstance(value, str) and len(value) > 8:
#             value_display = f"{value[:6]}********{value[-4:]}"
#         else:
#             value_display = value
#         print(f"  {field_name}: {value_display}")
#     print(f"  Caminho do .env usado: {settings.model_config.get('env_file')}")
