from typing import Optional
from loguru import logger # <--- MUDANÇA AQUI

from .openai_llm import OpenAILLM
from .openrouter_llm import OpenRouterLLM
# Importar LLMClient assíncrono se a factory também precisar lidar com ele
# from .llm_client import LLMClient 

# Adicionar a importação dos settings para http_referer e x_title, se necessário para OpenRouterLLM
from evolux_engine.settings import settings as app_settings # Renomeado para evitar conflito se 'settings' for usado como var


class LLMFactory:
    def __init__(self, api_key: Optional[str] = None): # Tornar api_key opcional se for pego de settings
        # A API Key pode vir dos settings globais ou ser passada explicitamente
        self.api_key = api_key # Pode ser None se a fábrica for usada para clientes que pegam a key de outro lugar
        # self.openrouter_api_key = app_settings.OPENROUTER_API_KEY 
        # self.openai_api_key = app_settings.OPENAI_API_KEY
        # logger.debug(f"LLMFactory inicializada.") # Log será mais útil no get_llm_client

    def get_llm_client(
        self, 
        provider: str, 
        model_name: str,
        api_key_override: Optional[str] = None # Permitir override da API key
    ):
        if not provider:
            logger.error("LLMFactory.get_llm_client: Nome do provedor não fornecido.")
            raise ValueError("Nome do provedor é obrigatório.")
        if not model_name:
            logger.error("LLMFactory.get_llm_client: Nome do modelo não fornecido.")
            raise ValueError("Nome do modelo é obrigatório.")
            
        active_api_key = api_key_override or self.api_key # Prioriza override, depois o da factory

        # Decidir qual chave de API usar com base no provedor, se não houver override
        # e se a factory não foi inicializada com uma chave específica.
        if not active_api_key:
            if provider.lower() == "openai":
                active_api_key = app_settings.OPENAI_API_KEY
            elif provider.lower() == "openrouter":
                active_api_key = app_settings.OPENROUTER_API_KEY
            
        if not active_api_key:
            logger.error(
                f"LLMFactory: API key não encontrada para o provedor '{provider}'. "
                "Forneça via inicialização da Factory, override, ou settings (ex: EVOLUX_OPENROUTER_API_KEY)."
            )
            raise ValueError(f"API Key não configurada para o provedor {provider}.")

        logger.debug(f"LLMFactory tentando criar cliente para provider: {provider}, modelo: {model_name}")

        provider_lower = provider.lower()

        if provider_lower == "openai":
            return OpenAILLM(api_key=active_api_key, model_name=model_name)
        
        elif provider_lower == "openrouter":
            # OpenRouterLLM precisa de http_referer e x_title, que podem vir de settings
            return OpenRouterLLM(
                api_key=active_api_key, 
                model_name=model_name,
                http_referer=str(app_settings.HTTP_REFERER) if app_settings.HTTP_REFERER else None, # Converte HttpUrl para str
                x_title=app_settings.APP_TITLE
            )
        
        # Se você quiser que a factory também possa retornar o LLMClient assíncrono:
        # elif provider_lower == "async_openrouter": # Exemplo de nome para o cliente assíncrono
        #     return LLMClient( # O LLMClient assíncrono
        #         api_key=active_api_key,
        #         model_name=model_name,
        #         provider="openrouter", # Ou pegue de uma configuração
        #         http_referer=str(app_settings.HTTP_REFERER) if app_settings.HTTP_REFERER else None,
        #         x_title=app_settings.APP_TITLE
        #     )
        # elif provider_lower == "async_openai": # Exemplo de nome para o cliente assíncrono
        #     return LLMClient( # O LLMClient assíncrono
        #         api_key=active_api_key,
        #         model_name=model_name,
        #         provider="openai", # Ou pegue de uma configuração
        #     )
            
        else:
            logger.error(f"LLMFactory: Provedor LLM desconhecido ou não suportado: {provider}")
            raise ValueError(f"Provedor LLM desconhecido ou não suportado: {provider}")

