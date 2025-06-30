"""
Clientes LLM para o MCP LLM Server.

Este módulo contém implementações de clientes para diferentes provedores de LLM,
incluindo OpenAI, Claude (Anthropic), OpenRouter e Gemini (Google).
"""

from typing import Dict, Any, List, Optional, Tuple

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
from .openai import OpenAIClient
from .claude import ClaudeClient
from .openrouter import OpenRouterClient
from .gemini import GeminiClient

from ..config import settings
from ..utils import get_logger, LoggerMixin
from ..utils.exceptions import ConfigurationError, LLMProviderError


class LLMClientFactory(LoggerMixin):
    """
    Factory para criação e gerenciamento de clientes LLM.
    
    Esta classe gerencia a criação de clientes para diferentes provedores,
    mantém cache de instâncias e oferece interface unificada.
    """
    
    def __init__(self):
        """Inicializa a factory de clientes LLM."""
        self._clients: Dict[str, BaseLLMClient] = {}
        self._initialized_clients: Dict[str, bool] = {}
        
        # Mapeia provedores para classes de cliente
        self._client_classes = {
            "openai": OpenAIClient,
            "claude": ClaudeClient,
            "openrouter": OpenRouterClient,
            "gemini": GeminiClient,
        }
        
        self.logger.info("LLM Client Factory initialized")
    
    async def get_client(self, provider: str) -> BaseLLMClient:
        """
        Obtém um cliente para o provedor especificado.
        
        Args:
            provider: Nome do provedor (openai, claude, openrouter, gemini)
            
        Returns:
            Cliente inicializado para o provedor
            
        Raises:
            ConfigurationError: Se o provedor não estiver configurado
            LLMProviderError: Se houver erro na inicialização
        """
        if provider not in self._client_classes:
            raise ConfigurationError(f"Unknown provider: {provider}")
        
        # Retorna cliente do cache se já existe
        if provider in self._clients and self._initialized_clients.get(provider, False):
            return self._clients[provider]
        
        # Obtém configuração do provedor
        try:
            config = settings.get_provider_config(provider)
        except Exception as e:
            raise ConfigurationError(f"Provider {provider} not configured: {e}")
        
        # Cria e inicializa cliente
        client_class = self._client_classes[provider]
        client = client_class(config)
        
        try:
            await client.initialize()
            self._clients[provider] = client
            self._initialized_clients[provider] = True
            
            self.logger.info("Client initialized successfully", provider=provider)
            return client
            
        except Exception as e:
            self.log_error(e, {"provider": provider})
            raise LLMProviderError(provider, f"Failed to initialize client: {e}")
    
    async def get_default_client(self) -> BaseLLMClient:
        """
        Obtém o cliente para o provedor padrão.
        
        Returns:
            Cliente padrão inicializado
        """
        default_provider = settings.llm.default_provider
        return await self.get_client(default_provider)
    
    def get_available_providers(self) -> List[str]:
        """
        Retorna lista de provedores disponíveis.
        
        Returns:
            Lista de nomes de provedores
        """
        available = []
        
        for provider in self._client_classes.keys():
            try:
                settings.get_provider_config(provider)
                available.append(provider)
            except:
                continue  # Provedor não configurado
        
        return available
    
    def get_initialized_providers(self) -> List[str]:
        """
        Retorna lista de provedores já inicializados.
        
        Returns:
            Lista de provedores inicializados
        """
        return [
            provider for provider, initialized 
            in self._initialized_clients.items() 
            if initialized
        ]
    
    async def get_all_models(self) -> Dict[str, List[ModelInfo]]:
        """
        Obtém lista de modelos de todos os provedores disponíveis.
        
        Returns:
            Dicionário mapeando provedor -> lista de modelos
        """
        all_models = {}
        
        for provider in self.get_available_providers():
            try:
                client = await self.get_client(provider)
                models = await client.get_models()
                all_models[provider] = models
                
                self.logger.debug(
                    "Retrieved models from provider",
                    provider=provider,
                    model_count=len(models)
                )
                
            except Exception as e:
                self.log_error(e, {"provider": provider, "operation": "get_models"})
                all_models[provider] = []
        
        total_models = sum(len(models) for models in all_models.values())
        self.logger.info(
            "Retrieved models from all providers",
            provider_count=len(all_models),
            total_models=total_models
        )
        
        return all_models
    
    async def find_model(self, model_id: str) -> Optional[Tuple[str, ModelInfo]]:
        """
        Encontra um modelo específico em todos os provedores.
        
        Args:
            model_id: ID do modelo a procurar
            
        Returns:
            Tupla (provider, model_info) se encontrado, None caso contrário
        """
        for provider in self.get_available_providers():
            try:
                client = await self.get_client(provider)
                model_info = await client.get_model_info(model_id)
                
                if model_info:
                    self.logger.debug("Model found", model_id=model_id, provider=provider)
                    return (provider, model_info)
                    
            except Exception as e:
                self.log_error(e, {
                    "provider": provider, 
                    "model_id": model_id,
                    "operation": "find_model"
                })
                continue
        
        self.logger.debug("Model not found", model_id=model_id)
        return None
    
    async def close_all(self) -> None:
        """Fecha todos os clientes inicializados."""
        self.logger.info("Closing all LLM clients")
        
        for provider, client in self._clients.items():
            if self._initialized_clients.get(provider, False):
                try:
                    await client.close()
                    self.logger.debug("Client closed", provider=provider)
                except Exception as e:
                    self.log_error(e, {"provider": provider, "operation": "close"})
        
        self._clients.clear()
        self._initialized_clients.clear()
        
        self.logger.info("All LLM clients closed")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status da factory e todos os clientes.
        
        Returns:
            Dicionário com status detalhado
        """
        return {
            "available_providers": self.get_available_providers(),
            "initialized_providers": self.get_initialized_providers(),
            "default_provider": settings.llm.default_provider,
            "client_count": len(self._clients),
            "clients": {
                provider: client.get_provider_info()
                for provider, client in self._clients.items()
                if self._initialized_clients.get(provider, False)
            }
        }


__all__ = [
    # Base classes
    "BaseLLMClient",
    "ChatRequest",
    "ChatResponse", 
    "CompletionRequest",
    "CompletionResponse",
    "ModelInfo",
    "MessageRole",
    "ChatMessage",
    
    # Client implementations
    "OpenAIClient",
    "ClaudeClient",
    "OpenRouterClient",
    "GeminiClient",
    
    # Factory
    "LLMClientFactory",
]