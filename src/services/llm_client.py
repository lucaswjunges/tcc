# src/services/llm_client.py (VERSÃO FINAL E CORRETA)

from openai import OpenAI
from src.config import settings # Importa as configurações globais
from src.services.observability_service import log

class LLMClient:
    """Um wrapper unificado para interagir com diferentes clientes de LLM."""
    def __init__(self, provider: str):
        self._client = self._get_client(provider)

    def _get_client(self, provider: str):
        """Fábrica que retorna uma instância de cliente configurada."""
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY must be set in .env for OpenRouter provider")
            
            return OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def chat_completion(self, model: str, messages: list, max_tokens: int = 4096) -> str:
        """Método unificado para chamar o endpoint de chat completion."""
        log.info("Requesting chat completion from LLM.", model=model)
        try:
            response = self._client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            log.info("Chat completion received successfully.", model=model)
            return content
        except Exception as e:
            log.error("Error during LLM chat completion.", error=str(e), exc_info=True)
            raise

# --- A CORREÇÃO ESTÁ AQUI ---
# A função não aceita mais argumentos. Ela é autossuficiente.
def get_llm_client() -> LLMClient:
    """Retorna uma instância do nosso LLMClient usando as configurações globais."""
    return LLMClient(provider=settings.llm_provider)
