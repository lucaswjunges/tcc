import os
from typing import Any, Optional, Dict

import yaml # Para carregar de um arquivo config.yaml se necessário
from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings # Usaremos pydantic-settings para carregar do .env

from evolux_engine.schemas.contracts import LLMProvider, GlobalConfig


class ConfigManager:
    """
    Gerencia o carregamento e o acesso às configurações globais do Evolux Engine.
    Prioriza variáveis de ambiente, mas pode ter um fallback para um arquivo de configuração.
    """

    def __init__(self, config_file_path: Optional[str] = None):
        self.global_config: GlobalConfig
        self._load_configuration(config_file_path)
        logger.info("ConfigManager inicializado.")
        # logger.debug(f"Configurações carregadas: {self.global_config.model_dump(exclude_none=True)}")


    def _load_configuration(self, config_file_path: Optional[str]):
        """
        Carrega as configurações.
        1. Carrega .env para variáveis de ambiente.
        2. Usa Pydantic BaseSettings para parsear essas variáveis no schema GlobalConfig.
        3. (Opcional) Poderia carregar um arquivo YAML e fazer merge.
        """
        load_dotenv() # Carrega variáveis do arquivo .env para o ambiente

        try:
            # Pydantic-settings automaticamente lê variáveis de ambiente
            # que correspondem aos campos de GlobalConfig (e seus aliases).
            # Ex: OPENROUTER_API_KEY no .env será mapeado para evolux_openrouter_api_key
            self.global_config = GlobalConfig()

            # Se um config_file_path YAML for fornecido, poderíamos carregar e sobrescrever/complementar.
            # Por enquanto, vamos manter simples e focar no .env e nos defaults do GlobalConfig._
            if config_file_path and os.path.exists(config_file_path):
                try:
                    with open(config_file_path, 'r') as f:
                        yaml_config_data = yaml.safe_load(f)
                    if yaml_config_data:
                        # Aqui você precisaria de uma lógica de merge cuidadosa
                        # Por exemplo, sobrescrever os valores do GlobalConfig com os do YAML
                        # self.global_config = GlobalConfig(**{**self.global_config.model_dump(), **yaml_config_data})
                        logger.info(f"Configurações do arquivo YAML '{config_file_path}' foram consideradas (lógica de merge a ser implementada).")
                except Exception as e:
                    logger.error(f"Erro ao carregar arquivo de configuração YAML '{config_file_path}': {e}")

        except Exception as e: # Ex: ValidationError do Pydantic se algo estiver errado
            logger.opt(exception=True).critical(f"Falha crítica ao carregar configurações globais: {e}")
            raise  # Re-lança a exceção para parar a aplicação se configs cruciais faltarem


    def get_global_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Obtém uma configuração global pelo nome do campo no schema GlobalConfig.
        """
        if hasattr(self.global_config, key):
            value = getattr(self.global_config, key)
            return value if value is not None else default
        else:
            logger.warning(f"Tentativa de acessar configuração global desconhecida: {key}")
            return default

    def get_api_key(self, provider_name: Union[str, LLMProvider]) -> Optional[str]:
        """
        Obtém a chave de API para um provedor LLM específico.
        """
        provider_enum: Optional[LLMProvider] = None
        if isinstance(provider_name, LLMProvider):
            provider_enum = provider_name
        else:
            try:
                provider_enum = LLMProvider[provider_name.upper()]
            except KeyError:
                logger.error(f"Provedor LLM desconhecido: {provider_name}")
                return None
        
        if provider_enum == LLMProvider.OPENROUTER:
            return self.global_config.evolux_openrouter_api_key
        elif provider_enum == LLMProvider.OPENAI:
            return self.global_config.evolux_openai_api_key
        # Adicionar outros provedores aqui
        # elif provider_enum == LLMProvider.GOOGLE:
        #     return self.global_config.evolux_google_api_key
        # elif provider_enum == LLMProvider.ANTHROPIC:
        #     return self.global_config.evolux_anthropic_api_key
        else:
            logger.warning(f"Nenhuma chave de API configurada em GlobalConfig para o provedor: {provider_name}")
            return None

    def get_default_model_for(self, purpose: str) -> Optional[str]:
        """
        Obtém o nome do modelo padrão para um propósito específico (planner, executor, validator).
        """
        if purpose == "planner":
            return self.global_config.default_model_planner
        elif purpose == "executor_content_gen":
            return self.global_config.default_model_executor_content_gen
        elif purpose == "executor_command_gen":
            return self.global_config.default_model_executor_command_gen
        elif purpose == "validator":
            return self.global_config.default_model_validator
        else:
            logger.warning(f"Propósito de modelo desconhecido: {purpose}")
            return None
            
    @property
    def project_base_directory(self) -> str:
        """Retorna o diretório base para todos os workspaces de projetos."""
        return self.global_config.project_base_dir

# Exemplo de uso (seria em main.py ou similar):
# if __name__ == "__main__":
#     # Criar um arquivo .env de exemplo na raiz do projeto:
#     # OPENROUTER_API_KEY="sk-or-v1-sua-chave-aqui"
#     # EVOLUX_MODEL_PLANNER="anthropic/claude-3-opus-20240229"
#     # EVOLUX_PROJECT_BASE_DIR="./my_evolux_projects"
#
#     config_manager = ConfigManager()
#     print(f"OpenRouter Key: {config_manager.get_api_key('openrouter')}")
#     print(f"Default Planner Model: {config_manager.get_default_model_for('planner')}")
#     print(f"Project Base Dir: {config_manager.project_base_directory}")
#     print(f"Logging Level: {config_manager.get_global_setting('logging_level')}")

