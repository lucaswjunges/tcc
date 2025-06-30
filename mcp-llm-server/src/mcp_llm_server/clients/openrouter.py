"""
Cliente OpenRouter para o MCP LLM Server.

Este módulo implementa o cliente específico para a API do OpenRouter,
que oferece acesso a múltiplos modelos de diferentes provedores através
de uma interface unificada compatível com OpenAI.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import json

import httpx
from openai import AsyncOpenAI

from .base import (
    BaseLLMClient,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    ModelInfo,
    MessageRole,
    ChatMessage
)
from ..utils.exceptions import LLMProviderError, AuthenticationError, NetworkError


class OpenRouterClient(BaseLLMClient):
    """
    Cliente para a API do OpenRouter.
    
    OpenRouter oferece acesso a múltiplos modelos (Claude, GPT, Llama, etc.)
    através de uma interface compatível com OpenAI, facilitando switching
    entre diferentes provedores e modelos.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o cliente OpenRouter.
        
        Args:
            config: Configurações incluindo api_key, base_url, etc.
        """
        super().__init__("openrouter", config)
        
        # Validação de configuração
        if not config.get("api_key"):
            raise ValueError("OpenRouter API key is required")
    
    async def initialize(self) -> None:
        """Inicializa o cliente OpenRouter."""
        try:
            # OpenRouter é compatível com a API OpenAI
            self._client = AsyncOpenAI(
                api_key=self.config["api_key"],
                base_url=self.config.get("base_url", "https://openrouter.ai/api/v1"),
                timeout=self.config.get("timeout_seconds", 30),
                default_headers={
                    "HTTP-Referer": self.config.get("http_referer", "https://localhost"),
                    "X-Title": self.config.get("app_name", "MCP LLM Server")
                }
            )
            
            # Cliente separado para acessar API específica do OpenRouter
            self._openrouter_client = httpx.AsyncClient(
                base_url=self.config.get("base_url", "https://openrouter.ai/api/v1"),
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "HTTP-Referer": self.config.get("http_referer", "https://localhost"),
                    "X-Title": self.config.get("app_name", "MCP LLM Server"),
                    "Content-Type": "application/json"
                },
                timeout=self.config.get("timeout_seconds", 30)
            )
            
            # Testa a conexão listando modelos
            models_response = await self._openrouter_client.get("/models")
            models_response.raise_for_status()
            models_data = models_response.json()
            
            self.logger.info(
                "OpenRouter client initialized successfully",
                available_models=len(models_data.get("data", []))
            )
            
            self._is_initialized = True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.log_error(e)
                raise AuthenticationError(f"OpenRouter authentication failed: {e}")
            else:
                self.log_error(e)
                raise LLMProviderError("openrouter", f"HTTP error: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openrouter", f"Initialization failed: {e}")
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Executa requisição de chat."""
        self._ensure_initialized()
        
        try:
            # Prepara parâmetros da requisição
            messages = self._format_messages_for_provider(request.messages)
            model = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            self.logger.debug(
                "Sending chat request to OpenRouter",
                model=model,
                message_count=len(messages),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Executa requisição
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            # Processa resposta
            content = response.choices[0].message.content or ""
            usage = self._parse_usage_info(response.usage.dict() if response.usage else {})
            
            self.logger.info(
                "Chat request completed successfully",
                model=model,
                response_length=len(content),
                usage=usage
            )
            
            return ChatResponse(
                content=content,
                model=model,
                usage=usage,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openrouter", f"Chat request failed: {e}")
    
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Executa requisição de chat com streaming."""
        self._ensure_initialized()
        
        try:
            # Prepara parâmetros da requisição
            messages = self._format_messages_for_provider(request.messages)
            model = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            self.logger.debug(
                "Starting streaming chat request to OpenRouter",
                model=model,
                message_count=len(messages)
            )
            
            # Executa requisição com streaming
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # Processa chunks de resposta
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
            
            self.logger.info("Streaming chat request completed", model=model)
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openrouter", f"Streaming chat request failed: {e}")
    
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executa requisição de completion.
        
        OpenRouter suporta tanto chat quanto completion, convertemos para chat.
        """
        # Converte completion para chat
        chat_request = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content=request.prompt)],
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=False,
            metadata=request.metadata
        )
        
        chat_response = await self.chat(chat_request)
        
        return CompletionResponse(
            content=chat_response.content,
            model=chat_response.model,
            usage=chat_response.usage,
            metadata=chat_response.metadata
        )
    
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """
        Executa requisição de completion com streaming.
        
        OpenRouter suporta tanto chat quanto completion, convertemos para chat.
        """
        # Converte completion para chat
        chat_request = ChatRequest(
            messages=[ChatMessage(role=MessageRole.USER, content=request.prompt)],
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
            metadata=request.metadata
        )
        
        async for chunk in self.stream_chat(chat_request):
            yield chunk
    
    async def get_models(self) -> List[ModelInfo]:
        """Retorna lista de modelos OpenRouter disponíveis."""
        self._ensure_initialized()
        
        try:
            response = await self._openrouter_client.get("/models")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model_data in data.get("data", []):
                models.append(ModelInfo(
                    id=model_data["id"],
                    name=model_data.get("name", model_data["id"]),
                    provider="openrouter",
                    description=model_data.get("description", ""),
                    max_tokens=model_data.get("context_length"),
                    supports_chat=True,
                    supports_completion=True,
                    supports_streaming=True,
                    metadata={
                        "pricing": model_data.get("pricing", {}),
                        "top_provider": model_data.get("top_provider", {}),
                        "per_request_limits": model_data.get("per_request_limits")
                    }
                ))
            
            self.logger.info("Retrieved OpenRouter models", model_count=len(models))
            return models
            
        except httpx.HTTPStatusError as e:
            self.log_error(e)
            raise NetworkError(f"Failed to get models: HTTP {e.response.status_code}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openrouter", f"Failed to get models: {e}")
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retorna informações sobre um modelo específico."""
        models = await self.get_models()
        
        for model in models:
            if model.id == model_id:
                return model
        
        return None
    
    async def get_generation_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de geração do OpenRouter.
        
        Esta é uma funcionalidade específica do OpenRouter.
        """
        self._ensure_initialized()
        
        try:
            response = await self._openrouter_client.get("/generation")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openrouter", f"Failed to get generation stats: {e}")
    
    async def close(self) -> None:
        """Fecha clientes e limpa recursos."""
        await super().close()
        
        if hasattr(self, '_openrouter_client'):
            await self._openrouter_client.aclose()
    
    def _get_default_model(self) -> str:
        """Retorna modelo padrão do OpenRouter."""
        return self.config.get("default_model", "anthropic/claude-3-sonnet")