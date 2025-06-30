"""
Cliente OpenAI para o MCP LLM Server.

Este módulo implementa o cliente específico para a API da OpenAI,
suportando tanto chat quanto completion com streaming.
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator

import openai
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
from ..utils.exceptions import LLMProviderError, AuthenticationError


class OpenAIClient(BaseLLMClient):
    """
    Cliente para a API da OpenAI.
    
    Suporta GPT-4, GPT-3.5 e outros modelos da OpenAI com
    chat completions e text completions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o cliente OpenAI.
        
        Args:
            config: Configurações incluindo api_key, base_url, etc.
        """
        super().__init__("openai", config)
        
        # Validação de configuração
        if not config.get("api_key"):
            raise ValueError("OpenAI API key is required")
    
    async def initialize(self) -> None:
        """Inicializa o cliente OpenAI."""
        try:
            self._client = AsyncOpenAI(
                api_key=self.config["api_key"],
                base_url=self.config.get("base_url", "https://api.openai.com/v1"),
                timeout=self.config.get("timeout_seconds", 30)
            )
            
            # Testa a conexão listando modelos
            models = await self._client.models.list()
            self.logger.info(
                "OpenAI client initialized successfully",
                available_models=len(models.data)
            )
            
            self._is_initialized = True
            
        except openai.AuthenticationError as e:
            self.log_error(e)
            raise AuthenticationError(f"OpenAI authentication failed: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Initialization failed: {e}")
    
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
                "Sending chat request to OpenAI",
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
            
        except openai.APIError as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"API error: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Chat request failed: {e}")
    
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
                "Starting streaming chat request to OpenAI",
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
            
        except openai.APIError as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Streaming API error: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Streaming chat request failed: {e}")
    
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executa requisição de completion.
        
        Note: OpenAI deprecated text completions, so we convert to chat format.
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
        
        Note: OpenAI deprecated text completions, so we convert to chat format.
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
        """Retorna lista de modelos OpenAI disponíveis."""
        self._ensure_initialized()
        
        try:
            models_response = await self._client.models.list()
            models = []
            
            for model in models_response.data:
                # Filtra apenas modelos de chat/completion
                if any(prefix in model.id for prefix in ["gpt-", "text-", "davinci", "curie", "babbage", "ada"]):
                    models.append(ModelInfo(
                        id=model.id,
                        name=model.id,
                        provider="openai",
                        description=f"OpenAI model: {model.id}",
                        supports_chat=model.id.startswith("gpt-"),
                        supports_completion=True,
                        supports_streaming=True,
                        metadata={
                            "created": model.created,
                            "owned_by": model.owned_by
                        }
                    ))
            
            self.logger.info("Retrieved OpenAI models", model_count=len(models))
            return models
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Failed to get models: {e}")
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retorna informações sobre um modelo específico."""
        self._ensure_initialized()
        
        try:
            model = await self._client.models.retrieve(model_id)
            
            return ModelInfo(
                id=model.id,
                name=model.id,
                provider="openai",
                description=f"OpenAI model: {model.id}",
                supports_chat=model.id.startswith("gpt-"),
                supports_completion=True,
                supports_streaming=True,
                metadata={
                    "created": model.created,
                    "owned_by": model.owned_by
                }
            )
            
        except openai.NotFoundError:
            return None
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("openai", f"Failed to get model info: {e}")
    
    def _get_default_model(self) -> str:
        """Retorna modelo padrão da OpenAI."""
        return self.config.get("default_model", "gpt-4-turbo-preview")