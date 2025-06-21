import requests # Certifique-se que 'requests' está no requirements.txt

# --- INÍCIO DA CORREÇÃO ---
# Importa o logger diretamente do Loguru, o padrão do nosso projeto.
from loguru import logger as log
# --- FIM DA CORREÇÃO ---

from .base_llm import BaseLLM # Importa o BaseLLM do mesmo pacote

class OpenRouterLLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str, http_referer: str, x_title: str): # Adicionados referer e title
        super().__init__(api_key, model_name) # Passa model_name para o super
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.http_referer = http_referer
        self.x_title = x_title
        log.debug(f"OpenRouterLLM inicializado para modelo: {self.model_name}")

    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str | None:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.x_title,
        }
        data = {
            "model": self.model_name, # Usa o model_name da instância
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        log.debug("Enviando requisição para OpenRouter...", model=self.model_name, prompt_start=prompt[:50]+"...")
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=180) # Timeout de 3 minutos
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                log.debug("Resposta recebida da OpenRouter.", model=self.model_name, response_length=len(content))
                return content.strip()
            else:
                log.warning("Resposta da OpenRouter não continha 'choices' ou estava vazia.",
                            response_data_keys=list(response_data.keys()) if response_data else "None", 
                            model=self.model_name)
                return None
        except requests.exceptions.HTTPError as e:
            log.error(f"Erro HTTP da API OpenRouter: {e.response.status_code} - {e.response.text}",
                      model=self.model_name, exc_info=True)
        except requests.exceptions.RequestException as e:
            log.error(f"Erro de requisição para OpenRouter: {e}", model=self.model_name, exc_info=True)
        except Exception as e: # Captura genérica para outros erros (ex: JSONDecodeError)
            log.error(f"Erro inesperado ao comunicar com OpenRouter: {e}", model=self.model_name, exc_info=True)
        return None