"""
Cliente Gemini (Google) para o MCP LLM Server.

Este módulo implementa o cliente específico para a API do Google Gemini,
suportando modelos Gemini Pro, Gemini Flash e outras variantes.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from google.ai.generativelanguage_v1beta.types import content

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


class GeminiClient(BaseLLMClient):
    """
    Cliente para a API do Google Gemini.
    
    Suporta modelos Gemini 1.5 Pro, Gemini 1.5 Flash e outras variantes
    com chat e completion capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o cliente Gemini.
        
        Args:
            config: Configurações incluindo api_key, base_url, etc.
        """
        super().__init__("gemini", config)
        
        # Validação de configuração
        if not config.get("api_key"):
            raise ValueError("Gemini API key is required")
    
    async def initialize(self) -> None:
        """Inicializa o cliente Gemini."""
        try:
            # Configura a biblioteca do Gemini
            genai.configure(api_key=self.config["api_key"])
            
            # Testa a conexão listando modelos
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model)
            
            if not models:
                raise Exception("No compatible Gemini models found")
            
            # Cria cliente modelo padrão para testes
            model_name = self._get_default_model()
            self._default_model = genai.GenerativeModel(model_name)
            
            # Testa com uma requisição simples
            response = await self._generate_content_async(
                self._default_model,
                "Hello",
                max_output_tokens=10
            )
            
            self.logger.info(
                "Gemini client initialized successfully",
                available_models=len(models),
                default_model=model_name,
                test_response_length=len(response.text if response.text else "")
            )
            
            self._is_initialized = True
            
        except Exception as e:
            if "API_KEY_INVALID" in str(e) or "authentication" in str(e).lower():
                self.log_error(e)
                raise AuthenticationError(f"Gemini authentication failed: {e}")
            else:
                self.log_error(e)
                raise LLMProviderError("gemini", f"Initialization failed: {e}")
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Executa requisição de chat."""
        self._ensure_initialized()
        
        try:
            # Prepara parâmetros da requisição
            model_name = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            # Cria modelo com configurações específicas
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Converte mensagens para formato do Gemini
            gemini_messages = self._convert_messages_to_gemini(request.messages)
            
            self.logger.debug(
                "Sending chat request to Gemini",
                model=model_name,
                message_count=len(request.messages),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Executa requisição
            if len(gemini_messages) == 1:
                # Single prompt
                response = await self._generate_content_async(
                    model,
                    gemini_messages[0]["parts"][0]["text"],
                    max_output_tokens=max_tokens
                )
            else:
                # Chat com histórico
                chat = model.start_chat(history=gemini_messages[:-1])
                last_message = gemini_messages[-1]["parts"][0]["text"]
                response = await self._send_message_async(chat, last_message)
            
            # Processa resposta
            content = response.text if response.text else ""
            usage = self._parse_gemini_usage(response)
            
            self.logger.info(
                "Chat request completed successfully",
                model=model_name,
                response_length=len(content),
                usage=usage
            )
            
            return ChatResponse(
                content=content,
                model=model_name,
                usage=usage,
                metadata={
                    "finish_reason": self._get_finish_reason(response),
                    "safety_ratings": self._get_safety_ratings(response)
                }
            )
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("gemini", f"Chat request failed: {e}")
    
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Executa requisição de chat com streaming."""
        self._ensure_initialized()
        
        try:
            # Prepara parâmetros da requisição
            model_name = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            # Cria modelo com configurações específicas
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # Converte mensagens para formato do Gemini
            gemini_messages = self._convert_messages_to_gemini(request.messages)
            
            self.logger.debug(
                "Starting streaming chat request to Gemini",
                model=model_name,
                message_count=len(request.messages)
            )
            
            # Executa requisição com streaming
            if len(gemini_messages) == 1:
                # Single prompt
                response_stream = await self._generate_content_stream_async(
                    model,
                    gemini_messages[0]["parts"][0]["text"]
                )
            else:
                # Chat com histórico
                chat = model.start_chat(history=gemini_messages[:-1])
                last_message = gemini_messages[-1]["parts"][0]["text"]
                response_stream = await self._send_message_stream_async(chat, last_message)
            
            # Processa chunks de resposta
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            
            self.logger.info("Streaming chat request completed", model=model_name)
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("gemini", f"Streaming chat request failed: {e}")
    
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executa requisição de completion.
        
        Gemini usa generateContent, então convertemos para esse formato.
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
        
        Gemini usa generateContent, então convertemos para esse formato.
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
        """Retorna lista de modelos Gemini disponíveis."""
        try:
            models = []
            
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(ModelInfo(
                        id=model.name,
                        name=model.display_name or model.name,
                        provider="gemini",
                        description=model.description or f"Google Gemini model: {model.name}",
                        max_tokens=getattr(model, 'output_token_limit', None),
                        supports_chat=True,
                        supports_completion=True,
                        supports_streaming=True,
                        metadata={
                            "input_token_limit": getattr(model, 'input_token_limit', None),
                            "supported_generation_methods": model.supported_generation_methods,
                            "version": getattr(model, 'version', None)
                        }
                    ))
            
            self.logger.info("Retrieved Gemini models", model_count=len(models))
            return models
            
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("gemini", f"Failed to get models: {e}")
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retorna informações sobre um modelo específico."""
        try:
            model = genai.get_model(model_id)
            
            if 'generateContent' not in model.supported_generation_methods:
                return None
            
            return ModelInfo(
                id=model.name,
                name=model.display_name or model.name,
                provider="gemini",
                description=model.description or f"Google Gemini model: {model.name}",
                max_tokens=getattr(model, 'output_token_limit', None),
                supports_chat=True,
                supports_completion=True,
                supports_streaming=True,
                metadata={
                    "input_token_limit": getattr(model, 'input_token_limit', None),
                    "supported_generation_methods": model.supported_generation_methods,
                    "version": getattr(model, 'version', None)
                }
            )
            
        except Exception:
            return None
    
    def _get_default_model(self) -> str:
        """Retorna modelo padrão do Gemini."""
        return self.config.get("default_model", "gemini-1.5-pro")
    
    def _convert_messages_to_gemini(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Converte mensagens para formato do Gemini.
        
        Args:
            messages: Mensagens no formato padrão
            
        Returns:
            Mensagens no formato do Gemini
        """
        gemini_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Gemini não tem role system, incorpora no primeiro user message
                continue
            
            role = "user" if msg.role == MessageRole.USER else "model"
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        return gemini_messages
    
    def _parse_gemini_usage(self, response: GenerateContentResponse) -> Dict[str, Any]:
        """
        Converte informações de usage do Gemini para formato padrão.
        
        Args:
            response: Resposta do Gemini
            
        Returns:
            Dicionário com informações de usage padronizadas
        """
        usage_metadata = getattr(response, 'usage_metadata', None)
        if not usage_metadata:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        return {
            "prompt_tokens": getattr(usage_metadata, 'prompt_token_count', 0),
            "completion_tokens": getattr(usage_metadata, 'candidates_token_count', 0),
            "total_tokens": getattr(usage_metadata, 'total_token_count', 0)
        }
    
    def _get_finish_reason(self, response: GenerateContentResponse) -> Optional[str]:
        """Extrai finish reason da resposta."""
        if response.candidates:
            return getattr(response.candidates[0], 'finish_reason', None)
        return None
    
    def _get_safety_ratings(self, response: GenerateContentResponse) -> List[Dict[str, Any]]:
        """Extrai safety ratings da resposta."""
        if response.candidates and response.candidates[0].safety_ratings:
            return [
                {
                    "category": rating.category.name if hasattr(rating.category, 'name') else str(rating.category),
                    "probability": rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability)
                }
                for rating in response.candidates[0].safety_ratings
            ]
        return []
    
    # Métodos async wrapper para operações síncronas do Gemini
    
    async def _generate_content_async(self, model, prompt, **kwargs):
        """Wrapper async para generate_content."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: model.generate_content(prompt, **kwargs))
    
    async def _generate_content_stream_async(self, model, prompt, **kwargs):
        """Wrapper async para generate_content com stream."""
        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(None, lambda: model.generate_content(prompt, stream=True, **kwargs))
        
        for chunk in stream:
            yield chunk
    
    async def _send_message_async(self, chat, message):
        """Wrapper async para chat.send_message."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: chat.send_message(message))
    
    async def _send_message_stream_async(self, chat, message):
        """Wrapper async para chat.send_message com stream."""
        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(None, lambda: chat.send_message(message, stream=True))
        
        for chunk in stream:
            yield chunk