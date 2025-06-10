# Conteúdo para: evolux_engine/llms/openai_llm.py
from typing import Optional
import requests # Ou use a biblioteca 'openai' que já está no requirements.txt

from evolux_engine.utils.logging_utils import log
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

        # --- ALTERNATIVA USANDO A BIBLIOTECA 'openai' ---
        # (Se optar por esta, comente ou remova a implementação com 'requests' acima)
        # try:
        #     log.debug(f"Enviando requisição para OpenAI via biblioteca, modelo: {self.model_name}")
        #     chat_completion = self.client.chat.completions.create(
        #         messages=[{"role": "user", "content": prompt}],
        #         model=self.model_name,
        #         temperature=temperature,
        #         max_tokens=max_tokens,
        #     )
        #     if chat_completion.choices and len(chat_completion.choices) > 0:
        #         content = chat_completion.choices[0].message.content
        #         log.debug("Resposta recebida da OpenAI (biblioteca).", model=self.model_name, response_length=len(content) if content else 0)
        #         return content.strip() if content else None
        #     else:
        #         log.warning("Resposta da OpenAI (biblioteca) não continha 'choices' ou estava vazia.",
        #                     response_object=chat_completion, model=self.model_name)
        #         return None
        # except openai.APIError as e: # Captura erros específicos da API da OpenAI
        #     log.error(f"Erro da API OpenAI: {e}", model=self.model_name, exc_info=True)
        # except Exception as e:
        #     log.error(f"Erro inesperado ao comunicar com OpenAI (biblioteca): {e}", model=self.model_name, exc_info=True)
        # return None
