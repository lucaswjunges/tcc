# src/services/llm_client.py (VERSÃO FINALÍSSIMA, COMPLETA E CORRETA)

import httpx
from pydantic import SecretStr
from .observability_service import log
from ..config import settings  # Importa as configurações para usar a chave

class LLMClient:
    """Um cliente HTTP para interagir com a API do LLM (OpenRouter)."""

    def __init__(self, api_key: SecretStr, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key.get_secret_value()
        self.base_url = base_url
        
        # CORREÇÃO 1: Adiciona o prefixo "Bearer " exigido pela API.
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Define um timeout mais longo para dar tempo ao LLM de "pensar"
        self.http_client = httpx.Client(
            base_url=self.base_url, 
            headers=self.headers,
            timeout=120.0 
        )

    def chat_completion(self, model: str, messages: list) -> str:
        """Envia uma requisição de chat completion para o LLM."""
        log.info("Requesting chat completion from LLM.", model=model)
        
        try:
            response = self.http_client.post(
                url="/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                }
            )
            response.raise_for_status()  # Lança exceção para erros HTTP 4xx/5xx
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            log.info("LLM response received successfully.")
            return content

        except httpx.HTTPStatusError as e:
            error_msg = f"Error code: {e.response.status_code} - {e.response.text}"
            log.error("Error during LLM chat completion.", error=error_msg, exc_info=True)
            raise Exception(error_msg)
        except Exception as e:
            log.error("An unexpected error occurred during LLM communication.", error=str(e), exc_info=True)
            raise

# --- Ponto de acesso Singleton ---
# CORREÇÃO 2: Esta função foi omitida por engano e está sendo restaurada.
_llm_client_instance = None

def get_llm_client() -> LLMClient:
    """Retorna uma instância única do LLMClient (padrão Singleton)."""
    global _llm_client_instance
    if _llm_client_instance is None:
        log.info("Creating a new LLMClient instance.")
        _llm_client_instance = LLMClient(api_key=settings.openrouter_api_key)
    return _llm_client_instance
