from typing import Optional, Dict, Any
import requests
import json
from src.config import settings as global_settings
from src.services.observability_service import log

class LLMClient:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-haiku"):
        """
        Inicializa o cliente LLM com a chave de API e o modelo padrão.
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        log.info("LLMClient initialized.", model=self.model)

    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Gera uma resposta para o prompt fornecido usando o modelo configurado.
        """
        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            log.error("Error generating LLM response.", error=str(e))
            raise

    def list_models(self) -> Dict[str, Any]:
        """
        Lista os modelos disponíveis no OpenRouter.
        """
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            log.error("Error listing models.", error=str(e))
            raise
