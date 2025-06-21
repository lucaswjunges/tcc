# --- INÍCIO DA CORREÇÃO ---
# 1. Importa o logger da forma correta (padrão do projeto)
from loguru import logger as log
# 2. Importa as settings para obter os valores de referer e title
from evolux_engine.settings import settings
# --- FIM DA CORREÇÃO ---

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
            # A classe OpenAILLM não precisa dos headers extras
            return OpenAILLM(api_key=self.api_key, model_name=model)
        
        elif provider.lower() == "openrouter":
            # --- INÍCIO DA CORREÇÃO ---
            # 3. Passa os argumentos que faltavam para o OpenRouterLLM, pegando-os das settings.
            return OpenRouterLLM(
                api_key=self.api_key, 
                model_name=model,
                http_referer=settings.HTTP_REFERER,
                x_title=settings.APP_TITLE
            )
            # --- FIM DA CORREÇÃO ---
        else:
            log.error(f"LLMFactory: Provedor LLM desconhecido: {provider}")
            raise ValueError(f"Provedor LLM desconhecido: {provider}")