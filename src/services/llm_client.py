# src/services/llm_client.py (VERSÃO CORRIGIDA)

import os
import requests
from dotenv import load_dotenv

# AQUI ESTÁ A CORREÇÃO: Importamos a classe ConfigManager
from src.services.config_manager import ConfigManager
from src.services.observability_service import log

load_dotenv()

class LLMClient:
    def __init__(self):
        # E AQUI ESTÁ A CORREÇÃO: Usamos a classe para obter a config
        self.config = ConfigManager.get_config()
        self.api_settings = self.config.api_settings
        self.default_provider = self.api_settings.default_provider
        self.provider_settings = self.api_settings.provider[self.default_provider]
        
        self.api_key_env_var = self.provider_settings.api_key_env
        self.api_key = os.getenv(self.api_key_env_var)
        
        if not self.api_key:
            log.critical(f"API key environment variable '{self.api_key_env_var}' not set.", env_var=self.api_key_env_var)
            raise ValueError(f"API key environment variable '{self.api_key_env_var}' not set. Please create a .env file and set this variable.")

        self.base_url = self.provider_settings.base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        log.info("LLMClient initialized successfully.", provider=self.default_provider)

    def invoke(self, model: str, messages: list[dict], max_tokens: int = 4096) -> dict:
        """Envia uma requisição para a API da LLM."""
        
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        log.info("Invoking LLM.", model=model, num_messages=len(messages))

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=120)
            response.raise_for_status() # Lança um erro para status HTTP 4xx/5xx
            
            response_data = response.json()
            log.info("LLM invocation successful.", model=model)
            return response_data

        except requests.exceptions.HTTPError as http_err:
            log.error("HTTP error occurred during LLM invocation.", 
                      status_code=http_err.response.status_code, 
                      response=http_err.response.text,
                      error=str(http_err))
            raise
        except Exception as e:
            log.error("An unexpected error occurred during LLM invocation.", error=str(e), exc_info=True)
            raise

