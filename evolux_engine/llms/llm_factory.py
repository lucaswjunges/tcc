from evolux_engine.utils.logging_utils import log
from .openai_llm import OpenAILLM
from .openrouter_llm import OpenRouterLLM

class LLMFactory:
    def __init__(self, api_key: str):
        if not api_key:
            log.error("LLMFactory: API key não fornecida na inicialização.")
            raise ValueError("API key deve ser fornecida para LLMFactory.")
        self.api_key = api_key
        log.debug(f"LLMFactory inicializada.")

    def get_llm_client(self, provider: str, model: str):
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
