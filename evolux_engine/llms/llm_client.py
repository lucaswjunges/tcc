import json
import asyncio
from typing import Optional, Dict, Any, List, Union

import httpx
import google.generativeai as genai
from loguru import logger

from evolux_engine.schemas.contracts import LLMProvider

class LLMClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        provider: Union[str, LLMProvider],
        api_base_url: Optional[str] = None,
        timeout: int = 180,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ):
        if not api_key: raise ValueError("API key é obrigatória")
        if not model_name: raise ValueError("Nome do modelo é obrigatório")

        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.provider = LLMProvider(provider.lower()) if isinstance(provider, str) else provider
        
        self._async_client: Optional[httpx.AsyncClient] = None
        self._gemini_model: Optional[genai.GenerativeModel] = None

        if self.provider == LLMProvider.GOOGLE:
            genai.configure(api_key=self.api_key)
            self._gemini_model = genai.GenerativeModel(self.model_name)
            logger.info(f"LLMClient (Google GenAI) inicializado para '{self.model_name}'.")
        else:
            self.base_url = api_base_url or self._get_default_base_url()
            self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            if self.provider == LLMProvider.OPENROUTER:
                if http_referer: self.headers["HTTP-Referer"] = str(http_referer)
                if x_title: self.headers["X-Title"] = str(x_title)
            logger.info(f"LLMClient (HTTPX) inicializado para '{self.provider.value}' com '{self.model_name}'.")

    def _get_default_base_url(self) -> str:
        if self.provider == LLMProvider.OPENAI: return "https://api.openai.com/v1"
        return "https://openrouter.ai/api/v1"

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            # Configurar cliente com logs menos verbosos
            self._async_client = httpx.AsyncClient(
                headers=self.headers, 
                timeout=self.timeout,
                # Reduzir logs HTTP verbosos
                event_hooks={
                    'request': [],
                    'response': []
                }
            )
        return self._async_client

    async def close(self):
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()

    async def _generate_gemini_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        gemini_messages = [{'role': "model" if msg["role"] == "assistant" else msg["role"], 'parts': [msg['content']]} for msg in messages]
        try:
            logger.debug(f"Enviando requisição para Gemini: Modelo='{self.model_name}'")
            response = await self._gemini_model.generate_content_async(gemini_messages)
            return response.text
        except Exception:
            logger.opt(exception=True).error(f"Erro inesperado ao gerar resposta do Gemini: {self.model_name}")
            return None

    async def _generate_httpx_response(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Optional[str]:
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model_name, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        logger.debug(f"Enviando requisição para LLM via HTTPX: Modelo='{self.model_name}'")
        
        # Retry automático com backoff
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                client = await self._get_async_client()
                response = await client.post(endpoint_url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 502, 503, 504] and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Erro HTTP {e.response.status_code}, tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Erro HTTP {e.response.status_code}: {e.response.text}")
                    return None
                    
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Erro de conexão, tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Erro de conexão após {max_retries} tentativas: {str(e)}")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro inesperado na requisição HTTPX para '{self.model_name}': {str(e)}")
                return None
        
        return None

    async def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 8000, temperature: float = 0.5) -> Optional[str]:
        if self.provider == LLMProvider.GOOGLE:
            return await self._generate_gemini_response(messages)
        else:
            return await self._generate_httpx_response(messages, max_tokens, temperature)