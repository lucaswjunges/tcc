"""
Cliente base abstrato para provedores de LLM.

Este módulo define a interface comum que todos os clientes LLM devem implementar,
garantindo consistência e facilitando a adição de novos provedores.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from ..utils import LoggerMixin


class MessageRole(Enum):
    """Roles de mensagem padronizados."""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """Representa uma mensagem de chat."""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatRequest:
    """Requisição de chat para um LLM."""
    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Resposta de chat de um LLM."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CompletionRequest:
    """Requisição de completion para um LLM."""
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CompletionResponse:
    """Resposta de completion de um LLM."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelInfo:
    """Informações sobre um modelo LLM."""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_chat: bool = True
    supports_completion: bool = True
    supports_streaming: bool = True
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMClient(ABC, LoggerMixin):
    """
    Cliente base abstrato para provedores de LLM.
    
    Todos os clientes de LLM devem herdar desta classe e implementar
    os métodos abstratos definidos aqui.
    """
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Inicializa o cliente base.
        
        Args:
            provider_name: Nome do provedor (ex: "openai", "claude")
            config: Configurações específicas do provedor
        """
        self.provider_name = provider_name
        self.config = config
        self._client = None
        self._is_initialized = False
        
        self.logger.info(
            "Initializing LLM client",
            provider=provider_name,
            config_keys=list(config.keys())
        )
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Inicializa o cliente do provedor.
        
        Este método deve configurar a conexão com o provedor
        e verificar se as credenciais são válidas.
        """
        pass
    
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Executa uma requisição de chat.
        
        Args:
            request: Requisição de chat
            
        Returns:
            Resposta do chat
        """
        pass
    
    @abstractmethod
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Executa uma requisição de chat com streaming.
        
        Args:
            request: Requisição de chat com stream=True
            
        Yields:
            Chunks de texto da resposta
        """
        pass
    
    @abstractmethod
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Executa uma requisição de completion.
        
        Args:
            request: Requisição de completion
            
        Returns:
            Resposta do completion
        """
        pass
    
    @abstractmethod
    async def stream_completion(self, request: CompletionRequest) -> AsyncGenerator[str, None]:
        """
        Executa uma requisição de completion com streaming.
        
        Args:
            request: Requisição de completion com stream=True
            
        Yields:
            Chunks de texto da resposta
        """
        pass
    
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """
        Retorna lista de modelos disponíveis.
        
        Returns:
            Lista de informações dos modelos
        """
        pass
    
    @abstractmethod
    async def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Retorna informações sobre um modelo específico.
        
        Args:
            model_id: ID do modelo
            
        Returns:
            Informações do modelo ou None se não encontrado
        """
        pass
    
    async def close(self) -> None:
        """
        Fecha o cliente e limpa recursos.
        
        Implementação padrão que pode ser sobrescrita pelos provedores.
        """
        self.logger.info("Closing LLM client", provider=self.provider_name)
        
        if hasattr(self._client, 'close'):
            await self._client.close()
        elif hasattr(self._client, 'aclose'):
            await self._client.aclose()
        
        self._is_initialized = False
        self._client = None
    
    def _ensure_initialized(self) -> None:
        """Verifica se o cliente foi inicializado."""
        if not self._is_initialized:
            raise RuntimeError(f"Client {self.provider_name} not initialized. Call initialize() first.")
    
    def _get_default_model(self) -> str:
        """Retorna o modelo padrão para este provedor."""
        return self.config.get("default_model", "")
    
    def _get_max_tokens(self, request_max_tokens: Optional[int] = None) -> int:
        """
        Retorna o max_tokens a ser usado, priorizando o da requisição.
        
        Args:
            request_max_tokens: Max tokens especificado na requisição
            
        Returns:
            Max tokens a ser usado
        """
        return request_max_tokens or self.config.get("max_tokens", 4096)
    
    def _get_temperature(self, request_temperature: Optional[float] = None) -> float:
        """
        Retorna a temperature a ser usada, priorizando a da requisição.
        
        Args:
            request_temperature: Temperature especificada na requisição
            
        Returns:
            Temperature a ser usada
        """
        return request_temperature if request_temperature is not None else self.config.get("temperature", 0.7)
    
    def _format_messages_for_provider(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Formata mensagens para o formato específico do provedor.
        
        Implementação padrão que pode ser sobrescrita pelos provedores.
        
        Args:
            messages: Mensagens no formato padrão
            
        Returns:
            Mensagens no formato do provedor
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def _parse_usage_info(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Padroniza informações de usage de diferentes provedores.
        
        Args:
            usage_data: Dados de usage do provedor
            
        Returns:
            Dados de usage padronizados
        """
        # Implementação padrão - pode ser sobrescrita
        return {
            "prompt_tokens": usage_data.get("prompt_tokens", 0),
            "completion_tokens": usage_data.get("completion_tokens", 0),
            "total_tokens": usage_data.get("total_tokens", 0)
        }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o provedor.
        
        Returns:
            Informações do provedor
        """
        return {
            "name": self.provider_name,
            "initialized": self._is_initialized,
            "default_model": self._get_default_model(),
            "config": {k: v for k, v in self.config.items() if "key" not in k.lower()}  # Não expor API keys
        }