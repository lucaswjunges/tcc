from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Carrega as configurações a partir de variáveis de ambiente ou de um arquivo .env.
    O prefixo 'EVOLUX_' é usado para as variáveis (ex: EVOLUX_OPENROUTER_API_KEY).
    """
    OPENROUTER_API_KEY: str
    project_base_dir: str = "/home/lucas-junges/Documents/evolux-engine"
    project_workspace_dir: str = "project_workspaces"
    
    # Mapeamento dos modelos pode ser definido via variáveis de ambiente, se necessário
    MODEL_PLANNER: str = "anthropic/claude-3-haiku"
    MODEL_EXECUTOR: str = "anthropic/claude-3-haiku"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EVOLUX_",
        extra="ignore"
    )

# Exportar os campos direta   para o escopo global
SETTINGS = Settings()
global_settings = BaseSettings(
    llm_provider=SETTINGS.llm_provider,
    openrouter_api_key=SETTINGS.OPENROUTER_API_KEY,
    model_mapping=ModelMapping(
        planner=SETTINGS.MODEL_PLANNER,
        executor=SETTINGS.MODEL_EXECUTOR
    ),
    project_base_dir=SETTINGS.project_base_dir,
    project_workspace_dir=SETTINGS.project_workspace_dir
)
