from typing import Optional, List, Dict
import requests
import json # Para formatar o corpo do erro JSON

from loguru import logger # <--- MUDANÇA AQUI
from .base_llm import BaseLLM # Assumindo que você tem base_llm.py

class OpenRouterLLM(BaseLLM):
    def __init__(
        self, 
        api_key: str, 
        model_name: str, # Ex: "mistralai/mistral-7b-instruct:free"
        http_referer: Optional[str] = None, # Ex: "http://localhost:3000"
        x_title: Optional[str] = None # Ex: "Evolux Engine TCC"
    ):
        super().__init__(api_key, model_name)
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.http_referer = http_referer
        self.x_title = x_title
        logger.debug(
            f"OpenRouterLLM inicializado para modelo: {self.model_name}", 
            referer=self.http_referer, 
            title=self.x_title
        )

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7, 
        max_tokens: int = 1500
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
            # OpenRouter pode aceitar outros parâmetros como "transforms", "route"
            # "site_url": self.http_referer, # Algumas APIs OpenRouter podem usar isso
            # "your_app_name": self.x_title, # Outra forma de passar o nome do app
        }

        last_user_message = "N/A"
        if messages and isinstance(messages, list) and len(messages) > 0:
            last_user_message = messages[-1].get("content", "Formato de mensagem inválido")

        logger.debug(
            "Enviando requisição para OpenRouter API...", 
            model=self.model_name, 
            last_message_preview=last_user_message[:70]+"...",
            url=self.api_url
        )
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=180) # Timeout mais longo
            response.raise_for_status()  # Levanta HTTPError para status ruins (4xx ou 5xx)
            
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if choice.get("message") and choice["message"].get("content"):
                    content = choice["message"]["content"]
                    usage = response_data.get("usage", {})
                    logger.debug(
                        "Resposta recebida da OpenRouter API.", 
                        model=self.model_name, 
                        prompt_tokens=usage.get('prompt_tokens', 'N/A'),
                        completion_tokens=usage.get('completion_tokens', 'N/A'),
                        response_length=len(content)
                    )
                    return content.strip()
            
            logger.warning(
                "Resposta da OpenRouter API em formato inesperado ou sem conteúdo.",
                response_data_preview=str(response_data)[:200]+"...", 
                model=self.model_name
            )
            return None

        except requests.exceptions.HTTPError as e:
            error_body = e.response.text
            try: # Tenta formatar o corpo do erro se for JSON
                error_json = e.response.json()
                error_body = json.dumps(error_json, indent=2)
            except json.JSONDecodeError:
                pass # Mantém o texto bruto se não for JSON

            logger.error(
                f"Erro HTTP da API OpenRouter: {e.response.status_code}",
                response_body=error_body,
                model=self.model_name
            )
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao conectar com OpenRouter API.", model=self.model_name)
        except requests.exceptions.RequestException as e:
            logger.opt(exception=True).error(f"Erro de requisição para OpenRouter API.", model=self.model_name)
        except Exception as e:
            logger.opt(exception=True).error(f"Erro inesperado ao comunicar com OpenRouter API.", model=self.model_name)
        return None

