from evolux_engine.utils.logging_utils import log
from .openai_llm import OpenAILLM  # Importa a classe concreta OpenAILLM
from .openrouter_llm import OpenRouterLLM # Importa a classe concreta OpenRouterLLM
# Removido: from .llm_client import LLMClient (vamos usar as classes concretas diretamente)

class LLMFactory:
    def __init__(self, api_key: str):
        """
        Inicializa a LLMFactory.
        A api_key deve ser fornecida aqui (ex: settings.OPENROUTER_API_KEY ou settings.OPENAI_API_KEY).
        """
        if not api_key:
            log.error("LLMFactory: API key não fornecida na inicialização.")
            raise ValueError("API key deve ser fornecida para LLMFactory.")
        
        self.api_key = api_key
        log.debug(f"LLMFactory inicializada.") # Log mais apropriado é debug aqui

    def get_llm_client(self, provider: str, model: str): # Espera 'provider' e 'model'
        """
        Retorna uma instância configurada de um cliente LLM específico (OpenAILLM ou OpenRouterLLM).

        Args:
            provider: O nome do provedor LLM (ex: "openai", "openrouter").
            model: O nome do modelo específico a ser usado.

        Returns:
            Uma instância de OpenAILLM ou OpenRouterLLM.

        Raises:
            ValueError: Se o provedor for desconhecido ou o modelo não for fornecido.
        """
        if not provider:
            log.error("LLMFactory.get_llm_client: Nome do provedor não fornecido.")
            raise ValueError("Nome do provedor é obrigatório.")
        if not model:
            log.error("LLMFactory.get_llm_client: Nome do modelo não fornecido.")
            raise ValueError("Nome do modelo é obrigatório.")
            
        log.debug(f"LLMFactory tentando criar cliente para provider: {provider}, modelo: {model}")

        if provider.lower() == "openai":
            return OpenAILLM(api_key=self.api_key, model_name=model)
        elif provider.lower() == "openrouter":
            return OpenRouterLLM(api_key=self.api_key, model_name=model)
        else:
            log.error(f"LLMFactory: Provedor LLM desconhecido: {provider}")
            raise ValueError(f"Provedor LLM desconhecido: {provider}")

