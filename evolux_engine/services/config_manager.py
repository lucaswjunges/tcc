import os
from typing import Any, Optional, Dict, Union

import yaml 
from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings

# Ajuste no import para refletir a nova estrutura de pastas
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


    def _load_configuration(self, config_file_path: Optional[str]):
        """
        Carrega as configurações.
        1. Carrega .env para variáveis de ambiente.
        2. Usa Pydantic BaseSettings para parsear essas variáveis no schema GlobalConfig.
        3. (Opcional) Poderia carregar um arquivo YAML e fazer merge.
        """
        # Carrega explicitamente o .env do diretório atual
        import os
        env_path = os.path.join(os.getcwd(), '.env')
        load_dotenv(env_path) # Carrega variáveis do arquivo .env para o ambiente
        
        # Debug: mostra se as variáveis foram carregadas
        logger.debug(f"EVOLUX_OPENROUTER_API_KEY loaded: {os.getenv('EVOLUX_OPENROUTER_API_KEY') is not None}")
        logger.debug(f"EVOLUX_OPENAI_API_KEY loaded: {os.getenv('EVOLUX_OPENAI_API_KEY') is not None}")
        logger.debug(f"EVOLUX_GOOGLE_API_KEY loaded: {os.getenv('EVOLUX_GOOGLE_API_KEY') is not None}")

        try:
            # Força a criação do GlobalConfig com valores manuais se o Pydantic falhar
            self.global_config = GlobalConfig()
            
            # Se as chaves ainda estão None, force manualmente
            if not self.global_config.evolux_openrouter_api_key:
                self.global_config.evolux_openrouter_api_key = os.getenv('EVOLUX_OPENROUTER_API_KEY')
            if not self.global_config.evolux_openai_api_key:
                self.global_config.evolux_openai_api_key = os.getenv('EVOLUX_OPENAI_API_KEY')
            if not self.global_config.evolux_google_api_key:
                self.global_config.evolux_google_api_key = os.getenv('EVOLUX_GOOGLE_API_KEY')
                
            # Log mascarado para segurança - nunca expor chaves reais
            logger.debug(f"OpenRouter API key configured: {'Yes' if self.global_config.evolux_openrouter_api_key else 'No'}")
            logger.debug(f"OpenAI API key configured: {'Yes' if self.global_config.evolux_openai_api_key else 'No'}")
            logger.debug(f"Google API key configured: {'Yes' if self.global_config.evolux_google_api_key else 'No'}")
            
            # Validar chaves API
            self._validate_api_keys()

            if config_file_path and os.path.exists(config_file_path):
                try:
                    with open(config_file_path, 'r') as f:
                        yaml_config_data = yaml.safe_load(f)
                    if yaml_config_data:
                        logger.info(f"Configurações do arquivo YAML '{config_file_path}' foram consideradas (lógica de merge a ser implementada).")
                except Exception as e:
                    logger.error(f"Erro ao carregar arquivo de configuração YAML '{config_file_path}': {e}")

        except Exception as e:
            logger.opt(exception=True).critical(f"Falha crítica ao carregar configurações globais: {e}")
            raise

    def _validate_api_keys(self):
        """Valida formato e segurança das chaves API"""
        import re
        
        # Padrões básicos para validar formato das chaves
        key_patterns = {
            'evolux_openrouter_api_key': r'^sk-or-v1-[a-zA-Z0-9]{40,}$',
            'evolux_openai_api_key': r'^sk-[a-zA-Z0-9]{20,}$',
            'evolux_google_api_key': r'^[a-zA-Z0-9_-]{20,}$'
        }
        
        for key_attr, pattern in key_patterns.items():
            key_value = getattr(self.global_config, key_attr, None)
            
            if key_value:
                # Verificar formato básico
                if not re.match(pattern, key_value):
                    logger.warning(f"API key format may be invalid for {key_attr}")
                
                # Verificar comprimento mínimo de segurança
                if len(key_value) < 20:
                    logger.error(f"API key too short for {key_attr} - security risk")
                    raise ValueError(f"Invalid API key length for {key_attr}")
                
                # Verificar se não é chave de exemplo/teste comum
                test_keys = ['test', 'example', 'demo', 'placeholder', 'your-key-here']
                if any(test in key_value.lower() for test in test_keys):
                    logger.error(f"Test/placeholder API key detected for {key_attr}")
                    raise ValueError(f"Cannot use test API key for {key_attr}")

    def get_global_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Obtém uma configuração global pelo nome do campo no schema GlobalConfig.
        """
        return getattr(self.global_config, key, default)

    def get_api_key(self, provider_name: Union[str, LLMProvider]) -> Optional[str]:
        """
        Obtém a chave de API para um provedor LLM específico.
        """
        provider_enum: Optional[LLMProvider] = None
        if isinstance(provider_name, LLMProvider):
            provider_enum = provider_name
        else:
            try:
                # Corrigido para usar .value se for um enum, e lower() se for string
                provider_enum = LLMProvider(provider_name.lower())
            except ValueError:
                logger.error(f"Provedor LLM desconhecido: {provider_name}")
                return None
        
        if provider_enum == LLMProvider.OPENROUTER:
            api_key = self.global_config.evolux_openrouter_api_key
            logger.debug(f"OpenRouter API key: {api_key[:10] if api_key else None}...")
            return api_key
        elif provider_enum == LLMProvider.OPENAI:
            return self.global_config.evolux_openai_api_key
        # --- INÍCIO DA MODIFICAÇÃO (A única mudança necessária) ---
        elif provider_enum == LLMProvider.GOOGLE:
            return self.global_config.evolux_google_api_key
        # --- FIM DA MODIFICAÇÃO ---
        else:
            logger.warning(f"Nenhuma chave de API configurada em GlobalConfig para o provedor: {provider_name}")
            return None

    def get_default_model_for(self, purpose: str) -> Optional[str]:
        """
        Obtém o nome do modelo padrão para um propósito específico (planner, executor, validator).
        Esta é a sua lógica original, que está correta.
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