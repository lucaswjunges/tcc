# Conteúdo para: evolux_engine/llms/llm_client.py

from typing import Optional, Dict, Any
import requests
import json

# Imports problemáticos referenciando 'src' - vamos comentá-los ou ajustá-los depois
# from src.config import settings as global_settings
# from src.services.observability_service import log

# Se for precisar do log, e o observability_service já foi movido para evolux_engine/core:
# (Assumindo que observability_service.py está em evolux_engine/core/)
# from evolux_engine.core.observability_service import log

class LLMClient:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-haiku"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # if 'log' in globals(): log.info("LLMClient initialized.", model=self.model)
        print(f"DEBUG: LLMClient initialized for model {self.model}")


    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
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
            response.raise_for_status() # Levanta um erro para respostas HTTP 4xx/5xx
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as http_err:
            print(f"DEBUG: HTTP error in LLMClient: {http_err} - {response.text if 'response' in locals() else 'No response object'}")
            # if 'log' in globals(): log.error(f"HTTP error generating LLM response: {http_err} - {response.text}", error=str(http_err))
            raise
        except Exception as e:
            print(f"DEBUG: Generic error in LLMClient: {e}")
            # if 'log' in globals(): log.error("Error generating LLM response.", error=str(e))
            raise

    def list_models(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"DEBUG: HTTP error listing models: {http_err} - {response.text if 'response' in locals() else 'No response object'}")
            # if 'log' in globals(): log.error(f"HTTP error listing models: {http_err} - {response.text}", error=str(http_err))
            raise
        except Exception as e:
            print(f"DEBUG: Generic error listing models: {e}")
            # if 'log' in globals(): log.error("Error listing models.", error=str(e))
            raise
