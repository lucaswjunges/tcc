# evolux_engine/settings.py
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Carrega variáveis do arquivo .env para o ambiente do OS
# Isso é feito globalmente uma vez pelo python-dotenv
# O BaseSettings abaixo lerá diretamente do ambiente
# load_dotenv() # Removido, pois run.py já faz isso com log.

class EvoluxSettings(BaseSettings):
    # Configuração para Pydantic BaseSettings
    model_config = SettingsConfigDict(
        env_file='.env',            # Nome do arquivo .env
        env_file_encoding='utf-8',
        extra='ignore',             # Ignorar variáveis de ambiente extras
        case_sensitive=False,       # Nomes de variáveis de ambiente não diferenciam maiúsculas/minúsculas
        env_prefix='EVOLUX_'        # Ler variáveis que começam com EVOLUX_
    )

    # Chaves de API (usando Field para definir o nome da variável de ambiente)
    # O alias precisa ser o nome da variável no .env SEM o prefixo. Pydantic adicionará o prefixo.
    openrouter_api_key: Optional[str] = Field(None, validation_alias='OPENROUTER_API_KEY')
    openai_api_key: Optional[str] = Field(None, validation_alias='OPENAI_API_KEY')
    # Adicione outras chaves de API conforme necessário

    # Diretório base dos projetos
    project_base_dir: str = Field("./project_workspaces", validation_alias='PROJECT_BASE_DIR')

    # Provedor LLM padrão
    llm_provider: str = Field("openrouter", validation_alias='LLM_PROVIDER')

    # Modelos padrão
    model_planner: str = Field("deepseek/deepseek-coder", validation_alias='MODEL_PLANNER') # Exemplo
    model_executor: str = Field("deepseek/deepseek-coder", validation_alias='MODEL_EXECUTOR') # Exemplo
    # model_validator: str = Field("anthropic/claude-3-haiku-20240307", validation_alias='MODEL_VALIDATOR')

    # Configurações do Engine
    max_concurrent_tasks: int = Field(1, validation_alias='MAX_CONCURRENT_TASKS')
    logging_level: str = Field("INFO", validation_alias='LOGGING_LEVEL')

    # Opcional: para OpenRouter
    http_referer: Optional[str] = Field(None, validation_alias='HTTP_REFERER') # Ex: http://localhost
    app_title: Optional[str] = Field("Evolux Engine (TCC)", validation_alias='APP_TITLE')


# Instância global das configurações
settings = EvoluxSettings()

# Log para confirmar carregamento (opcional, pode ser feito no run.py)
# print("Variáveis de ambiente carregadas (via Pydantic settings) em settings.py:")
# for field_name, field_value in settings.model_fields.items():
#     alias = field_value.validation_alias
#     env_var_name_no_prefix = alias if isinstance(alias, str) else (alias.choices[0] if alias and alias.choices else field_name.upper())
#     env_var_name = f"{settings.model_config.get('env_prefix', '').upper()}{env_var_name_no_prefix}"
#     actual_value = getattr(settings, field_name)
#     print(f"  {env_var_name} (campo {field_name}): {'********' if 'KEY' in env_var_name else actual_value}")

