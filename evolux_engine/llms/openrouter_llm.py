import requests
from evolux_engine.utils.logging_utils import log
from .base_llm import BaseLLM

class OpenRouterLLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str = "anthropic/claude-3-haiku-20240307"):
        super().__init__(api_key, model_name)
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        log.info(f"OpenRouterLLM inicializado com modelo: {self.model_name}")

    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # OpenRouter espera uma lista de mensagens, mesmo que seja apenas uma mensagem do usuário
        data = {
            "model": self.model_name, # O modelo é especificado por instância
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        log.debug("Enviando requisição para OpenRouter...", model=self.model_name, prompt_length=len(prompt))
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=180) # Timeout aumentado
            response.raise_for_status()  # Levanta HTTPError para respostas 4XX/5XX
            
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                log.debug("Resposta recebida da OpenRouter.", model=self.model_name, response_length=len(content))
                return content.strip()
            else:
                log.warning("Resposta da OpenRouter não continha 'choices' ou 'choices' estava vazio.",
                            response_data=response_data, model=self.model_name)
                return None
        except requests.exceptions.HTTPError as e:
            log.error(f"Erro HTTP da API OpenRouter: {e.response.status_code} - {e.response.text}",
                      model=self.model_name, exc_info=True)
        except requests.exceptions.RequestException as e:
            log.error(f"Erro de requisição para OpenRouter: {e}", model=self.model_name, exc_info=True)
        except Exception as e:
            log.error(f"Erro inesperado ao comunicar com OpenRouter: {e}", model=self.model_name, exc_info=True)
        return None
