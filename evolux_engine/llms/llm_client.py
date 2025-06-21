import json
from typing import Optional, Dict, Any, List, Union

import httpx
# --- INÍCIO DA MODIFICAÇÃO ---
import google.generativeai as genai
from loguru import logger
# --- FIM DA MODIFICAÇÃO ---

try:
    from evolux_engine.schemas.contracts import LLMProvider
except ImportError:
    from enum import Enum
    class LLMProvider(Enum):
        OPENAI = "openai"
        OPENROUTER = "openrouter"
        GOOGLE = "google"

class LLMClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        provider: Union[str, LLMProvider],
        api_base_url: Optional[str] = None,
        timeout: int = 180, # Aumentado timeout padrão
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ):
        if not api_key:
            raise ValueError("API key é obrigatória para LLMClient.")
        if not model_name:
            raise ValueError("Nome do modelo é obrigatório para LLMClient.")

        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

        if isinstance(provider, str):
            self.provider = LLMProvider(provider.lower())
        else:
            self.provider = provider
        
        # --- LÓGICA DE INICIALIZAÇÃO SEPARADA POR PROVEDOR ---
        self._async_client: Optional[httpx.AsyncClient] = None
        self._gemini_model: Optional[genai.GenerativeModel] = None

        if self.provider == LLMProvider.GOOGLE:
            genai.configure(api_key=self.api_key)
            self._gemini_model = genai.GenerativeModel(self.model_name)
            logger.info(f"LLMClient (Google GenAI) inicializado para modelo '{self.model_name}'.")
        else: # Lógica para OpenRouter, OpenAI, etc.
            self.base_url = api_base_url or self._get_default_base_url()
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            if self.provider == LLMProvider.OPENROUTER:
                if http_referer: self.headers["HTTP-Referer"] = str(http_referer)
                if x_title: self.headers["X-Title"] = str(x_title)
            
            logger.info(f"LLMClient (HTTPX) inicializado para '{self.provider.value}' com modelo '{self.model_name}'.")

    def _get_default_base_url(self) -> str:
        if self.provider == LLMProvider.OPENAI:
            return "https://api.openai.com/v1"
        return "https://openrouter.ai/api/v1"

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self._async_client

    async def close(self):
        # A API do Gemini não requer fechamento de cliente
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None
            logger.info(f"LLMClient HTTPX client para '{self.model_name}' fechado.")

    async def _generate_gemini_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        # Converte o formato de mensagem OpenAI para o formato Gemini
        gemini_messages = []
        for msg in messages:
            # Gemini usa 'model' para respostas do assistente
            role = "model" if msg["role"] == "assistant" else msg["role"]
            gemini_messages.append({'role': role, 'parts': [msg['content']]})

        try:
            logger.debug(f"Enviando requisição para Gemini: Modelo='{self.model_name}'")
            response = await self._gemini_model.generate_content_async(gemini_messages)
            content = response.text
            logger.debug(f"Resposta recebida do Gemini. Conteúdo (início): {(content[:150] + '...') if len(content) > 150 else content}")
            return content
        except Exception as e:
            logger.opt(exception=True).error(f"Erro inesperado ao gerar resposta do Gemini. Modelo: {self.model_name}")
            return None

    async def _generate_httpx_response(self, messages: List[Dict[str, str]], model_override: Optional[str], max_tokens: int, temperature: float) -> Optional[str]:
        model_to_use = model_override or self.model_name
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = {"model": model_to_use, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        log_message_preview = (messages[-1]['content'][:150] + '...') if messages else ""
        logger.debug(f"Enviando requisição para LLM via HTTPX: Modelo='{model_to_use}', URL='{endpoint_url}', Última Msg='{log_message_preview}'")
        try:
            client = await self._get_async_client()
            response = await client.post(endpoint_url, json=payload)
            response.raise_for_status()
            result_json = response.json()
            if result_json.get('choices') and result_json['choices'][0].get('message'):
                content = result_json['choices'][0]['message'].get('content', '')
                logger.debug(f"Resposta recebida de '{model_to_use}'.")
                return str(content)
            else:
                logger.error(f"Resposta do LLM ('{model_to_use}') em formato inesperado. Resposta: {json.dumps(result_json, indent=2)}")
                return None
        except httpx.HTTPStatusError as http_err:
            logger.error(f"Erro HTTP {http_err.response.status_code} ao chamar API. Corpo da Resposta:\n{http_err.response.text}")
            return None
        except Exception as e:
            logger.opt(exception=True).error(f"Erro inesperado na requisição HTTPX para '{model_to_use}'.")
            return None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_override: Optional[str] = None,
        max_tokens: int = 8000,
        temperature: float = 0.7,
    ) -> Optional[str]:
        if self.provider == LLMProvider.GOOGLE:
            return await self._generate_gemini_response(messages)
        else:
            return await self._generate_httpx_response(messages, model_override, max_tokens, temperature)