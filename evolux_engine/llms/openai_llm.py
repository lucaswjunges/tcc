# Conteúdo para: evolux_engine/llms/openai_llm.py
from typing import Optional
import requests

# --- INÍCIO DA CORREÇÃO ---
# Importa o logger diretamente do Loguru, assim como nos outros arquivos.
from loguru import logger as log
# --- FIM DA CORREÇÃO ---

from .base_llm import BaseLLM

# Se for usar a biblioteca oficial `openai`:
# import openai

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model_name)
        self.api_url = "https://api.openai.com/v1/chat/completions" # Endpoint padrão
        # Se usar a biblioteca openai:
        # self.client = openai.OpenAI(api_key=self.api_key)
        log.debug(f"OpenAILLM inicializado para modelo: {self.model_name}")


    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> Optional[str]:
        # Exemplo usando a biblioteca 'requests' (similar ao OpenRouterLLM)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        log.debug("Enviando requisição para OpenAI API...", model=self.model_name, prompt_start=prompt[:50]+"...")
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=180)
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                log.debug("Resposta recebida da OpenAI API.", model=self.model_name, response_length=len(content))
                return content.strip()
            else:
                log.warning("Resposta da OpenAI API não continha 'choices' ou estava vazia.",
                            response_data_keys=list(response_data.keys()) if response_data else "None", 
                            model=self.model_name)
                return None
        except requests.exceptions.HTTPError as e:
            log.error(f"Erro HTTP da API OpenAI: {e.response.status_code} - {e.response.text}",
                      model=self.model_name, exc_info=True)
        except requests.exceptions.RequestException as e:
            log.error(f"Erro de requisição para OpenAI API: {e}", model=self.model_name, exc_info=True)
        except Exception as e:
            log.error(f"Erro inesperado ao comunicar com OpenAI API: {e}", model=self.model_name, exc_info=True)
        return None