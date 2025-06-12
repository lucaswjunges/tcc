from typing import Optional, List, Dict # Adicionado List e Dict para messages
import requests

from loguru import logger # <--- MUDANÇA AQUI
from .base_llm import BaseLLM # Assumindo que você tem base_llm.py

# Se for usar a biblioteca oficial `openai`:
# import openai # Descomente se for usar a biblioteca oficial
# from openai import OpenAIError # Para capturar exceções específicas


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model_name)
        self.api_url = "https://api.openai.com/v1/chat/completions"
        # # Para a biblioteca oficial openai:
        # try:
        #     self.client = openai.OpenAI(api_key=self.api_key)
        # except Exception as e:
        #     logger.opt(exception=True).error(f"Falha ao inicializar cliente OpenAI: {e}")
        #     raise
        logger.debug(f"OpenAILLM inicializado para modelo: {self.model_name}")

    def generate_response(
        self, 
        messages: List[Dict[str, str]], # Alterado de 'prompt: str' para 'messages'
        temperature: float = 0.7, 
        max_tokens: int = 1500
    ) -> Optional[str]:
        # Implementação usando a biblioteca 'requests'
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_name,
            "messages": messages, # Usar a lista de mensagens
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Para log, pegar o conteúdo da última mensagem do usuário
        last_user_message = "N/A"
        if messages and isinstance(messages, list) and len(messages) > 0:
            last_user_message = messages[-1].get("content", "Formato de mensagem inválido")
        
        logger.debug(
            "Enviando requisição para OpenAI API...", 
            model=self.model_name, 
            last_message_preview=last_user_message[:70]+"..."
        )
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=180) # Timeout mais longo
            response.raise_for_status()  # Levanta HTTPError para status ruins (4xx ou 5xx)
            
            response_data = response.json()
            
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if choice.get("message") and choice["message"].get("content"):
                    content = choice["message"]["content"]
                    logger.debug(
                        "Resposta recebida da OpenAI API.", 
                        model=self.model_name, 
                        response_length=len(content)
                    )
                    return content.strip()
            
            logger.warning(
                "Resposta da OpenAI API em formato inesperado ou sem conteúdo.",
                response_data_preview=str(response_data)[:200]+"...", 
                model=self.model_name
            )
            return None

        except requests.exceptions.HTTPError as e:
            error_body = e.response.text
            try:
                error_json = e.response.json()
                error_body = json.dumps(error_json, indent=2)
            except: pass
            logger.error(
                f"Erro HTTP da API OpenAI: {e.response.status_code}",
                response_body=error_body,
                model=self.model_name
            ) # Não precisa de exc_info=True se opt(exception=True não for usado
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao conectar com OpenAI API.", model=self.model_name)
        except requests.exceptions.RequestException as e:
            logger.opt(exception=True).error(f"Erro de requisição para OpenAI API.", model=self.model_name)
        except Exception as e:
            # Use opt(exception=True) para ter o traceback completo
            logger.opt(exception=True).error(f"Erro inesperado ao comunicar com OpenAI API.", model=self.model_name)
        return None

        # --- ALTERNATIVA USANDO A BIBLIOTECA 'openai' --- Async version
        # (Se optar por esta, comente ou remova a implementação com 'requests' acima)
        # (Esta seria uma implementação síncrona. Para assíncrona, use AsyncOpenAI)
        # async def generate_response_async_openai(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 1500) -> Optional[str]:
        #     try:
        #         from openai import AsyncOpenAI # Importar AsyncOpenAI
        #         async_client = AsyncOpenAI(api_key=self.api_key)
        #
        #         logger.debug(f"Enviando requisição para OpenAI via biblioteca (async), modelo: {self.model_name}")
        #         chat_completion = await async_client.chat.completions.create(
        #             messages=messages,
        #             model=self.model_name,
        #             temperature=temperature,
        #             max_tokens=max_tokens,
        #         )
        #         await async_client.close() # Fechar o cliente assíncrono
        #
        #         if chat_completion.choices and len(chat_completion.choices) > 0:
        #             content = chat_completion.choices[0].message.content
        #             logger.debug("Resposta recebida da OpenAI (biblioteca async).", model=self.model_name, response_length=len(content) if content else 0)
        #             return content.strip() if content else None
        #         else:
        #             logger.warning("Resposta da OpenAI (biblioteca async) não continha 'choices' ou estava vazia.",
        #                         response_object_str=str(chat_completion)[:200]+"...", model=self.model_name) # Logar parte do objeto
        #             return None
        #     except OpenAIError as e: # Captura erros específicos da API da OpenAI
        #         logger.opt(exception=True).error(f"Erro da API OpenAI (biblioteca async): {e.http_status} - {e.error}", model=self.model_name)
        #     except Exception as e:
        #         logger.opt(exception=True).error(f"Erro inesperado ao comunicar com OpenAI (biblioteca async): {e}", model=self.model_name)
        #     return None

