import json
import asyncio
import os
import time
from typing import Optional, Dict, Any, List, Union

import httpx
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from loguru import logger

from evolux_engine.schemas.contracts import LLMProvider
from evolux_engine.llms.model_router import ModelRouter, TaskCategory, ModelInfo
from evolux_engine.utils.resilience import CircuitBreaker, RateLimiter
from evolux_engine.utils.token_optimizer import TokenOptimizer

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
        model_manager=None,
    ):
        if not api_key: raise ValueError("API key é obrigatória")
        if not model_name: raise ValueError("Nome do modelo é obrigatório")
        if not model_router: raise ValueError("ModelRouter é obrigatório")

        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.provider = LLMProvider(provider.lower()) if isinstance(provider, str) else provider
        self.model_router = model_router
        self._token_optimizer = TokenOptimizer(model_name=self.model_name)
        
        self._rate_limiter = RateLimiter(requests_per_minute=15, name=f"{self.provider.value}_{self.model_name}_limiter")
        self._circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60, name=f"{self.provider.value}_{self.model_name}_breaker")
        self.model_manager = model_manager  # Sistema inteligente de gerenciamento

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
                message = result.get('choices', [{}])[0].get('message', {})
                content = message.get('content', '')
                
                # Se content está vazio, tenta extrair do reasoning (para modelos como deepseek)
                if not content or not content.strip():
                    reasoning = message.get('reasoning', '')
                    if reasoning and reasoning.strip():
                        logger.info(f"LLM '{self.model_name}' retornou reasoning em vez de content, usando reasoning")
                        content = reasoning
                    else:
                        logger.warning(f"LLM '{self.model_name}' retornou conteúdo vazio. Resultado completo: {result}")
                
                return content
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
        max_retries: int = 3,
        max_prompt_tokens: int = 4096
    ) -> Optional[str]:
        """
        Generates a response from the LLM with robust retry and fallback logic.
        """
        initial_model = self.model_name
        current_model = initial_model
        start_time = time.time()  # Para medir tempo de resposta
        
        optimized_messages = self._token_optimizer.truncate_messages(messages, max_prompt_tokens)
        
        for attempt in range(max_retries):
            try:
                if self.provider == LLMProvider.GOOGLE:
                    response = await self._generate_gemini_response(optimized_messages)
                else:
                    response = await self._generate_httpx_response(optimized_messages, max_tokens, temperature)
                
                # Registrar sucesso no sistema inteligente
                if self.model_manager and response is not None:
                    response_time = (time.time() - start_time) * 1000  # em ms
                    is_empty = not response or not response.strip()
                    tokens_generated = len(response.split()) if response else 0
                    
                    self.model_manager.record_request(
                        model_name=current_model,
                        success=not is_empty,
                        response_empty=is_empty,
                        response_time=response_time,
                        tokens_generated=tokens_generated
                    )
                
                return response

            except (ResourceExhausted, httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                is_rate_limit_error = isinstance(e, ResourceExhausted) or (isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429)
                is_timeout_error = isinstance(e, (httpx.TimeoutException, httpx.ConnectError))

                if is_rate_limit_error:
                    logger.warning(f"Rate limit error with {current_model} on attempt {attempt + 1}/{max_retries}. Triggering fallback.")
                    fallback_successful = await self._handle_fallback(current_model, category)
                    if fallback_successful:
                        current_model = self.model_name
                        continue
                    else:
                        logger.critical(f"Fallback failed for {current_model}. No other models available.")
                        raise e
                
                elif is_timeout_error:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Timeout/Connection error with {current_model}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                else:
                    logger.error(f"Unhandled HTTP error with {current_model}: {e}")
                    raise e

            except Exception as e:
                logger.opt(exception=True).error(f"Unexpected error on attempt {attempt + 1}/{max_retries} with {current_model}.")
                raise e

        # Registrar falha no sistema inteligente
        if self.model_manager:
            response_time = (time.time() - start_time) * 1000  # em ms
            self.model_manager.record_request(
                model_name=initial_model,
                success=False,
                response_empty=False,
                response_time=response_time
            )
        
        logger.error(f"Failed to generate response from {initial_model} after {max_retries} attempts and potential fallbacks.")
        return None
