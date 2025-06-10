# Conteúdo para: evolux_engine/llms/llm_factory.py

from typing import Optional
import os # Para pegar variáveis de ambiente

# Importa LLMClient do arquivo llm_client.py no mesmo diretório (evolux_engine/llms/)
from .llm_client import LLMClient

# Imports problemáticos que trataremos depois:
# from src.config import settings as global_settings
# Se a factory precisar de log, e o observability_service já foi movido para evolux_engine/core:
# (Assumindo que observability_service.py está em evolux_engine/core/)
# from evolux_engine.core.observability_service import log

class LLMFactory: # <--- ESTA É A CLASSE QUE SEU CÓDIGO ESTÁ PROCURANDO
    def __init__(self, api_key: Optional[str] = None):
        effective_api_key = api_key or os.getenv("EVOLUX_OPENROUTER_API_KEY")
        
        if not effective_api_key:
            raise ValueError("API key must be provided to LLMFactory or set as EVOLUX_OPENROUTER_API_KEY environment variable.")
        
        self.api_key = effective_api_key
        # if 'log' in globals(): log.info("LLMFactory initialized.")
        print(f"DEBUG: LLMFactory initialized with API key (first 5 chars): {self.api_key[:5] if self.api_key else 'None'}")


    def get_llm_client(self, model: str = "anthropic/claude-3-haiku") -> LLMClient:
        # if 'log' in globals(): log.info(f"LLMFactory creating LLMClient for model: {model}")
        print(f"DEBUG: LLMFactory.get_llm_client called for model: {model}")
        return LLMClient(api_key=self.api_key, model=model)
