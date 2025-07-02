import json
import asyncio
import os
from typing import Optional, Dict, Any, List, Union

import httpx
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from loguru import logger

from evolux_engine.schemas.contracts import LLMProvider
from evolux_engine.llms.model_router import ModelRouter, TaskCategory, ModelInfo
from evolux_engine.utils.resilience import CircuitBreaker, RateLimiter

class LLMClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        provider: Union[str, LLMProvider],
        model_router: ModelRouter,
        api_base_url: Optional[str] = None,
        timeout: int = 120,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ):
        if not api_key: raise ValueError("API key é obrigatória")
        if not model_name: raise ValueError("Nome do modelo é obrigatório")
        if not model_router: raise ValueError("ModelRouter é obrigatório")

        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.provider = LLMProvider(provider.lower()) if isinstance(provider, str) else provider
        self.model_router = model_router
        
        self._rate_limiter = RateLimiter(requests_per_minute=15, name=f"{self.provider.value}_{self.model_name}_limiter")
        self._circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60, name=f"{self.provider.value}_{self.model_name}_breaker")

        self._async_client: Optional[httpx.AsyncClient] = None
        self._gemini_model: Optional[genai.GenerativeModel] = None
        
        self._configure_client()

    def _configure_client(self):
        """Configura o cliente (Gemini ou HTTPX) com base no provedor e modelo atuais."""
        if self.provider == LLMProvider.GOOGLE:
            # A chave de API é configurada globalmente para o Gemini
            genai.configure(api_key=self.api_key)
            self._gemini_model = genai.GenerativeModel(self.model_name)
            logger.info(f"LLMClient reconfigurado para Google GenAI: '{self.model_name}'.")
        else:
            self.base_url = self._get_default_base_url()
            self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            if self.provider == LLMProvider.OPENROUTER:
                # As credenciais do OpenRouter podem vir de variáveis de ambiente
                http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:3000")
                x_title = os.getenv("OPENROUTER_X_TITLE", "Evolux Engine")
                if http_referer: self.headers["HTTP-Referer"] = str(http_referer)
                if x_title: self.headers["X-Title"] = str(x_title)
            
            # Garante que o cliente HTTPX seja recriado com os novos cabeçalhos/configurações
            self._async_client = None 
            logger.info(f"LLMClient reconfigurado para HTTPX: Provedor='{self.provider.value}', Modelo='{self.model_name}'.")

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
        gemini_messages = []
        system_content = ""
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n\n"
            elif msg["role"] == "assistant":
                gemini_messages.append({'role': "model", 'parts': [msg['content']]})
            elif msg["role"] == "user":
                content = msg["content"]
                if system_content and not gemini_messages:
                    content = system_content + content
                    system_content = ""
                gemini_messages.append({'role': "user", 'parts': [content]})
        
        if system_content and not any(msg['role'] == 'user' for msg in gemini_messages):
            gemini_messages.append({'role': "user", 'parts': [system_content + "Please provide your response."]})

        try:
            async with self._circuit_breaker:
                await self._rate_limiter.wait_for_token()
                logger.debug(f"Enviando requisição para Gemini: Modelo='{self.model_name}'")
                response = await self._gemini_model.generate_content_async(gemini_messages)
                return response.text
        except ConnectionAbortedError as e:
            logger.error(f"Circuit Breaker está aberto. A chamada para {self.model_name} foi bloqueada. Erro: {e}")
            return None
        except Exception as e:
            logger.opt(exception=True).error(f"Erro final ao gerar resposta do Gemini: {self.model_name}")
            # A exceção será capturada pelo Circuit Breaker, que decidirá se abre o circuito.
            raise e

    async def _generate_httpx_response(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> Optional[str]:
        endpoint_url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model_name, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        
        try:
            async with self._circuit_breaker:
                await self._rate_limiter.wait_for_token()
                logger.debug(f"Enviando requisição para LLM via HTTPX: Modelo='{self.model_name}'")
                client = await self._get_async_client()
                response = await client.post(endpoint_url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
        except ConnectionAbortedError as e:
            logger.error(f"Circuit Breaker está aberto. A chamada para {self.model_name} foi bloqueada. Erro: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP {e.response.status_code} para '{self.model_name}': {e.response.text}")
            raise e  # Re-lança para o Circuit Breaker
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error(f"Erro de conexão para '{self.model_name}': {str(e)}")
            raise e  # Re-lança para o Circuit Breaker
        except Exception as e:
            logger.opt(exception=True).error(f"Erro inesperado na requisição HTTPX para '{self.model_name}'")
            raise e

    async def _handle_fallback(self, failed_model_name: str, category: TaskCategory) -> bool:
        """
        Gerencia a lógica de fallback, marcando o modelo com falha como indisponível
        e tentando encontrar e configurar um novo modelo.
        """
        logger.warning(f"Iniciando processo de fallback para o modelo '{failed_model_name}' na categoria '{category.value}'.")
        self.model_router.mark_model_unavailable(failed_model_name)
        
        fallback_info = self.model_router.get_fallback_model(failed_model_name, category)
        
        if fallback_info:
            logger.info(f"Modelo de fallback encontrado: '{fallback_info.name}'. Reconfigurando cliente.")
            # Atualiza as propriedades do cliente para o novo modelo
            self.model_name = fallback_info.name
            self.provider = fallback_info.provider
            # A API key pode precisar ser atualizada dependendo do provedor
            # (assumindo que a factory que cria o client cuidará disso)
            self._configure_client()
            return True
        else:
            logger.error(f"Nenhum modelo de fallback disponível encontrado para '{failed_model_name}'.")
            return False

    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        category: TaskCategory,
        max_tokens: int = 8000, 
        temperature: float = 0.5,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Gera uma resposta do LLM com lógica de fallback e novas tentativas.
        """
        current_model = self.model_name
        
        for attempt in range(max_retries):
            try:
                if self.provider == LLMProvider.GOOGLE:
                    return await self._generate_gemini_response(messages)
                else:
                    return await self._generate_httpx_response(messages, max_tokens, temperature)
            
            except (ResourceExhausted, httpx.HTTPStatusError) as e:
                is_rate_limit_error = False
                if isinstance(e, ResourceExhausted):
                    is_rate_limit_error = True
                    logger.warning(f"Erro de cota/rate limit com o Gemini (modelo: {current_model}). Tentativa {attempt + 1}/{max_retries}.")
                elif isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                    is_rate_limit_error = True
                    logger.warning(f"Erro de rate limit (429) com o provedor HTTPX (modelo: {current_model}). Tentativa {attempt + 1}/{max_retries}.")
                
                if is_rate_limit_error:
                    fallback_successful = await self._handle_fallback(current_model, category)
                    if fallback_successful:
                        current_model = self.model_name  # Atualiza o nome do modelo para a próxima iteração
                        continue  # Tenta novamente com o modelo de fallback
                    else:
                        logger.critical("Falha no fallback. Nenhuma outra opção disponível. Lançando exceção.")
                        raise e  # Lança a exceção original se o fallback falhar
                else:
                    # Se for outro erro HTTP, não tenta o fallback e lança a exceção
                    raise e
            
            except Exception as e:
                logger.opt(exception=True).error(f"Erro inesperado na tentativa {attempt + 1}/{max_retries} com o modelo {current_model}.")
                raise e

        logger.error(f"Falha ao gerar resposta após {max_retries} tentativas.")
        return None
