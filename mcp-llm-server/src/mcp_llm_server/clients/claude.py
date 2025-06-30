"""
Cliente Claude (Anthropic) para o MCP LLM Server.

Este módulo implementa o cliente específico para a API da Anthropic Claude,
suportando as versões Claude 3 (Haiku, Sonnet, Opus) e Claude 3.5.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator

import anthropic
from anthropic import AsyncAnthropic

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


class ClaudeClient(BaseLLMClient):
    """
    Cliente para a API da Anthropic Claude.
    
    Suporta modelos Claude 3 (Haiku, Sonnet, Opus) e Claude 3.5
    com messages API e streaming.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o cliente Claude.
        
        Args:
            config: Configurações incluindo api_key, base_url, etc.
        """
        super().__init__("claude", config)
        
        # Validação de configuração
        if not config.get("api_key"):
            raise ValueError("Claude API key is required")
    
    async def initialize(self) -> None:
        """Inicializa o cliente Claude."""
        try:
            self._client = AsyncAnthropic(
                api_key=self.config["api_key"],
                base_url=self.config.get("base_url", "https://api.anthropic.com"),
                timeout=self.config.get("timeout_seconds", 30)
            )
            
            # Testa a conexão com uma requisição simples
            # Claude não tem endpoint de modelos, então fazemos um teste básico
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await self._client.messages.create(
                model=self._get_default_model(),
                max_tokens=10,
                messages=test_messages
            )
            
            self.logger.info(
                "Claude client initialized successfully",
                default_model=self._get_default_model(),
                test_response_length=len(response.content[0].text if response.content else "")
            )
            
            self._is_initialized = True
            
        except anthropic.AuthenticationError as e:
            self.log_error(e)
            raise AuthenticationError(f"Claude authentication failed: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("claude", f"Initialization failed: {e}")
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Executa requisição de chat."""
        self._ensure_initialized()
        
        try:
            # Separa mensagens do sistema das outras
            system_message = None
            messages = []
            
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            # Prepara parâmetros da requisição
            model = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            self.logger.debug(
                "Sending chat request to Claude",
                model=model,
                message_count=len(messages),
                has_system=system_message is not None,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Prepara argumentos da requisição
            request_args = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "stream": False
            }
            
            # Adiciona mensagem do sistema se presente
            if system_message:
                request_args["system"] = system_message
            
            # Executa requisição
            response = await self._client.messages.create(**request_args)
            
            # Processa resposta
            content = ""
            if response.content:
                content = response.content[0].text if response.content[0].type == "text" else ""
            
            usage = self._parse_claude_usage(response.usage)
            
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
                    "stop_reason": response.stop_reason,
                    "response_id": response.id
                }
            )
            
        except anthropic.APIError as e:
            self.log_error(e)
            raise LLMProviderError("claude", f"API error: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("claude", f"Chat request failed: {e}")
    
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Executa requisição de chat com streaming."""
        self._ensure_initialized()
        
        try:
            # Separa mensagens do sistema das outras
            system_message = None
            messages = []
            
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            # Prepara parâmetros da requisição
            model = request.model or self._get_default_model()
            max_tokens = self._get_max_tokens(request.max_tokens)
            temperature = self._get_temperature(request.temperature)
            
            self.logger.debug(
                "Starting streaming chat request to Claude",
                model=model,
                message_count=len(messages)
            )
            
            # Prepara argumentos da requisição
            request_args = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "stream": True
            }
            
            # Adiciona mensagem do sistema se presente
            if system_message:
                request_args["system"] = system_message
            
            # Executa requisição com streaming
            stream = await self._client.messages.create(**request_args)
            
            # Processa chunks de resposta
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, 'text'):
                        yield chunk.delta.text
            
            self.logger.info("Streaming chat request completed", model=model)
            
        except anthropic.APIError as e:
            self.log_error(e)
            raise LLMProviderError("claude", f"Streaming API error: {e}")
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("claude", f"Streaming chat request failed: {e}")
    
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executa requisição de completion.
        
        Claude usa Messages API, então convertemos para formato de chat.
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
        
        Claude usa Messages API, então convertemos para formato de chat.
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
        """
        Retorna lista de modelos Claude disponíveis.
        
        Claude não tem endpoint de modelos, então retornamos uma lista conhecida.
        """
        # Modelos Claude conhecidos
        known_models = [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "description": "Most intelligent model with enhanced reasoning and coding capabilities",
                "max_tokens": 200000
            },
            {
                "id": "claude-3-5-haiku-20241022", 
                "name": "Claude 3.5 Haiku",
                "description": "Fastest and most affordable model for everyday tasks",
                "max_tokens": 200000
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful model for highly complex tasks",
                "max_tokens": 200000
            },
            {
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet", 
                "description": "Balance of intelligence and speed for enterprise workloads",
                "max_tokens": 200000
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fastest and most compact model for near-instant responsiveness",
                "max_tokens": 200000
            }
        ]
        
        models = []
        for model_data in known_models:
            models.append(ModelInfo(
                id=model_data["id"],
                name=model_data["name"],
                provider="claude",
                description=model_data["description"],
                max_tokens=model_data["max_tokens"],
                supports_chat=True,
                supports_completion=True,
                supports_streaming=True,
                metadata={
                    "context_window": model_data["max_tokens"],
                    "family": "claude-3" if "claude-3" in model_data["id"] else "claude"
                }
            ))
        
        self.logger.info("Retrieved Claude models", model_count=len(models))
        return models
    
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Retorna informações sobre um modelo específico."""
        models = await self.get_models()
        
        for model in models:
            if model.id == model_id:
                return model
        
        return None
    
    def _get_default_model(self) -> str:
        """Retorna modelo padrão do Claude."""
        return self.config.get("default_model", "claude-3-sonnet-20240229")
    
    def _parse_claude_usage(self, usage) -> Dict[str, Any]:
        """
        Converte informações de usage do Claude para formato padrão.
        
        Args:
            usage: Objeto de usage do Claude
            
        Returns:
            Dicionário com informações de usage padronizadas
        """
        if not usage:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        return {
            "prompt_tokens": getattr(usage, "input_tokens", 0),
            "completion_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)
        }