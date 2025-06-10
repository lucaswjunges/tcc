# Conteúdo para: evolux_engine/llms/llm_client.py
from typing import Optional, Dict, Any
import requests
import json

from evolux_engine.utils.logging_utils import log
# Não precisamos de 'settings' aqui se a API key e modelo são passados no __init__

class LLMClient:
    def __init__(self, api_key: str, model: str): # Removido default do modelo, deve ser explícito
        if not api_key:
            log.error("LLMClient: API key não fornecida na inicialização.")
            raise ValueError("API key é obrigatória para LLMClient.")
        if not model:
            log.error("LLMClient: Modelo não fornecido na inicialização.")
            raise ValueError("Modelo é obrigatório para LLMClient.")

        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1" # Assume OpenRouter por enquanto
        # TODO: Tornar base_url e headers configuráveis com base no provedor (se não for sempre OpenRouter)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter pode requerer HTTP-Referer e X-Title para identificar seu app
            # "HTTP-Referer": "http://localhost:3000", # Substitua pelo seu site
            # "X-Title": "Evolux Engine TCC", # Substitua pelo nome do seu app
        }
        log.info("LLMClient initialized.", model=self.model)

    def generate_response(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        log.debug(f"Gerando resposta para o modelo {self.model} com prompt: {prompt[:100]}...")
        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                # Adicionar "stream": False se não estiver usando streaming
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=60 # Adicionar timeout para evitar bloqueio indefinido
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('choices') and result['choices'][0].get('message') and result['choices'][0]['message'].get('content'):
                content = result['choices'][0]['message']['content']
                log.debug(f"Resposta recebida do LLM: {content[:100]}...")
                return content
            else:
                log.error("Resposta do LLM em formato inesperado.", response_data=result)
                raise ValueError("Formato de resposta inesperado do LLM.")
                
        except requests.exceptions.Timeout:
            log.error(f"Timeout ao chamar LLM API para o modelo {self.model}.", error="Timeout")
            raise
        except requests.exceptions.HTTPError as http_err:
            log.error(f"Erro HTTP gerando resposta do LLM ({self.model}): {http_err.response.status_code}",
                      error_body=http_err.response.text,
                      error=str(http_err))
            raise
        except Exception as e:
            log.error(f"Erro inesperado gerando resposta do LLM ({self.model}).", error=str(e), exc_info=True)
            raise

    def list_models(self) -> Dict[str, Any]: # Este método pode não ser usado pela factory
        log.info("Listando modelos disponíveis...")
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=30)
            response.raise_for_status()
            models_data = response.json()
            log.info(f"Modelos listados com sucesso. Total: {len(models_data.get('data', []))}")
            return models_data
        except requests.exceptions.Timeout:
            log.error("Timeout ao listar modelos da LLM API.", error="Timeout")
            raise
        except requests.exceptions.HTTPError as http_err:
            log.error(f"Erro HTTP listando modelos: {http_err.response.status_code}",
                      error_body=http_err.response.text,
                      error=str(http_err))
            raise
        except Exception as e:
            log.error("Erro inesperado listando modelos.", error=str(e), exc_info=True)
            raise
