"""
Ferramenta de informações de modelos para o MCP LLM Server.

Esta ferramenta permite aos clientes obter informações sobre
modelos disponíveis de todos os provedores LLM suportados.
"""

import json
from typing import Dict, Any, List, Optional

from mcp.types import Tool

from ..clients import LLMClientFactory
from ..utils import LoggerMixin
from ..utils.exceptions import ValidationError, LLMProviderError


class ModelInfoTool(LoggerMixin):
    """
    Ferramenta MCP para obter informações sobre modelos LLM.
    
    Permite listar modelos disponíveis e obter informações detalhadas
    sobre modelos específicos de todos os provedores suportados.
    """
    
    def __init__(self, llm_factory: LLMClientFactory):
        """
        Inicializa a ferramenta de informações de modelos.
        
        Args:
            llm_factory: Factory para criação de clientes LLM
        """
        self.llm_factory = llm_factory
        self.logger.info("Model info tool initialized")
    
    async def get_definition(self) -> Tool:
        """
        Retorna a definição da ferramenta MCP.
        
        Returns:
            Definição da ferramenta
        """
        return Tool(
            name="model_info",
            description="Get information about available LLM models",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["list_all", "list_provider", "get_model", "get_providers", "search_models"]
                    },
                    "provider": {
                        "type": "string",
                        "description": "Specific provider to query (required for list_provider and get_model)",
                        "enum": ["openai", "claude", "openrouter", "gemini"]
                    },
                    "model_id": {
                        "type": "string",
                        "description": "Specific model ID to get info about (required for get_model)"
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Search term for finding models (required for search_models)"
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "Whether to include detailed model information",
                        "default": False
                    }
                },
                "required": ["action"]
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Executa a ferramenta de informações de modelos.
        
        Args:
            arguments: Argumentos da ferramenta
            
        Returns:
            Informações dos modelos em formato JSON
            
        Raises:
            ValidationError: Se os argumentos forem inválidos
            LLMProviderError: Se houver erro na execução
        """
        self.log_method_call("execute", args=arguments)
        
        try:
            action = arguments.get("action")
            if not action:
                raise ValidationError("Action is required")
            
            provider = arguments.get("provider")
            model_id = arguments.get("model_id")
            search_term = arguments.get("search_term")
            include_details = arguments.get("include_details", False)
            
            if action == "list_all":
                result = await self._list_all_models(include_details)
            
            elif action == "list_provider":
                if not provider:
                    raise ValidationError("Provider is required for list_provider action")
                result = await self._list_provider_models(provider, include_details)
            
            elif action == "get_model":
                if not model_id:
                    raise ValidationError("Model ID is required for get_model action")
                result = await self._get_model_info(model_id, provider)
            
            elif action == "get_providers":
                result = await self._get_providers_info()
            
            elif action == "search_models":
                if not search_term:
                    raise ValidationError("Search term is required for search_models action")
                result = await self._search_models(search_term, include_details)
            
            else:
                raise ValidationError(f"Unknown action: {action}")
            
            self.logger.info("Model info request completed", action=action)
            
            return json.dumps(result, indent=2)
            
        except ValidationError:
            raise
        except Exception as e:
            self.log_error(e)
            raise LLMProviderError("model_info", f"Model info execution failed: {e}")
    
    async def _list_all_models(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Lista todos os modelos de todos os provedores.
        
        Args:
            include_details: Se deve incluir detalhes dos modelos
            
        Returns:
            Dicionário com modelos agrupados por provedor
        """
        self.logger.debug("Listing all models", include_details=include_details)
        
        all_models = await self.llm_factory.get_all_models()
        
        result = {
            "action": "list_all",
            "providers": {},
            "summary": {
                "total_providers": len(all_models),
                "total_models": sum(len(models) for models in all_models.values())
            }
        }
        
        for provider, models in all_models.items():
            provider_data = {
                "model_count": len(models),
                "models": []
            }
            
            for model in models:
                model_data = {
                    "id": model.id,
                    "name": model.name
                }
                
                if include_details:
                    model_data.update({
                        "description": model.description,
                        "max_tokens": model.max_tokens,
                        "supports_chat": model.supports_chat,
                        "supports_completion": model.supports_completion,
                        "supports_streaming": model.supports_streaming,
                        "metadata": model.metadata
                    })
                
                provider_data["models"].append(model_data)
            
            result["providers"][provider] = provider_data
        
        return result
    
    async def _list_provider_models(self, provider: str, include_details: bool = False) -> Dict[str, Any]:
        """
        Lista modelos de um provedor específico.
        
        Args:
            provider: Nome do provedor
            include_details: Se deve incluir detalhes dos modelos
            
        Returns:
            Dicionário com modelos do provedor
        """
        self.logger.debug("Listing provider models", provider=provider, include_details=include_details)
        
        if provider not in self.llm_factory.get_available_providers():
            raise ValidationError(f"Provider '{provider}' not available")
        
        client = await self.llm_factory.get_client(provider)
        models = await client.get_models()
        
        result = {
            "action": "list_provider",
            "provider": provider,
            "model_count": len(models),
            "models": []
        }
        
        for model in models:
            model_data = {
                "id": model.id,
                "name": model.name
            }
            
            if include_details:
                model_data.update({
                    "description": model.description,
                    "max_tokens": model.max_tokens,
                    "supports_chat": model.supports_chat,
                    "supports_completion": model.supports_completion,
                    "supports_streaming": model.supports_streaming,
                    "metadata": model.metadata
                })
            
            result["models"].append(model_data)
        
        return result
    
    async def _get_model_info(self, model_id: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre um modelo específico.
        
        Args:
            model_id: ID do modelo
            provider: Provedor específico (opcional)
            
        Returns:
            Informações detalhadas do modelo
        """
        self.logger.debug("Getting model info", model_id=model_id, provider=provider)
        
        if provider:
            # Busca em provedor específico
            if provider not in self.llm_factory.get_available_providers():
                raise ValidationError(f"Provider '{provider}' not available")
            
            client = await self.llm_factory.get_client(provider)
            model_info = await client.get_model_info(model_id)
            
            if not model_info:
                return {
                    "action": "get_model",
                    "model_id": model_id,
                    "provider": provider,
                    "found": False,
                    "error": "Model not found"
                }
            
            return {
                "action": "get_model",
                "model_id": model_id,
                "provider": provider,
                "found": True,
                "model": {
                    "id": model_info.id,
                    "name": model_info.name,
                    "provider": model_info.provider,
                    "description": model_info.description,
                    "max_tokens": model_info.max_tokens,
                    "supports_chat": model_info.supports_chat,
                    "supports_completion": model_info.supports_completion,
                    "supports_streaming": model_info.supports_streaming,
                    "metadata": model_info.metadata
                }
            }
        else:
            # Busca em todos os provedores
            result = await self.llm_factory.find_model(model_id)
            
            if not result:
                return {
                    "action": "get_model",
                    "model_id": model_id,
                    "found": False,
                    "error": "Model not found in any provider"
                }
            
            found_provider, model_info = result
            
            return {
                "action": "get_model",
                "model_id": model_id,
                "found": True,
                "provider": found_provider,
                "model": {
                    "id": model_info.id,
                    "name": model_info.name,
                    "provider": model_info.provider,
                    "description": model_info.description,
                    "max_tokens": model_info.max_tokens,
                    "supports_chat": model_info.supports_chat,
                    "supports_completion": model_info.supports_completion,
                    "supports_streaming": model_info.supports_streaming,
                    "metadata": model_info.metadata
                }
            }
    
    async def _get_providers_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre provedores disponíveis.
        
        Returns:
            Informações dos provedores
        """
        self.logger.debug("Getting providers info")
        
        available_providers = self.llm_factory.get_available_providers()
        initialized_providers = self.llm_factory.get_initialized_providers()
        
        providers_info = {}
        
        for provider in available_providers:
            try:
                client = await self.llm_factory.get_client(provider)
                provider_info = client.get_provider_info()
                models = await client.get_models()
                
                providers_info[provider] = {
                    "name": provider_info["name"],
                    "initialized": provider_info["initialized"],
                    "default_model": provider_info["default_model"],
                    "model_count": len(models),
                    "config": provider_info["config"]
                }
            except Exception as e:
                providers_info[provider] = {
                    "name": provider,
                    "initialized": False,
                    "error": str(e)
                }
        
        return {
            "action": "get_providers",
            "available_providers": available_providers,
            "initialized_providers": initialized_providers,
            "default_provider": self.llm_factory.get_status()["default_provider"],
            "providers": providers_info
        }
    
    async def _search_models(self, search_term: str, include_details: bool = False) -> Dict[str, Any]:
        """
        Busca modelos por termo de pesquisa.
        
        Args:
            search_term: Termo de busca
            include_details: Se deve incluir detalhes dos modelos
            
        Returns:
            Modelos que correspondem ao termo de busca
        """
        self.logger.debug("Searching models", search_term=search_term, include_details=include_details)
        
        all_models = await self.llm_factory.get_all_models()
        search_term_lower = search_term.lower()
        
        matches = []
        
        for provider, models in all_models.items():
            for model in models:
                # Busca no ID, nome e descrição
                if (search_term_lower in model.id.lower() or 
                    search_term_lower in model.name.lower() or
                    (model.description and search_term_lower in model.description.lower())):
                    
                    model_data = {
                        "id": model.id,
                        "name": model.name,
                        "provider": provider
                    }
                    
                    if include_details:
                        model_data.update({
                            "description": model.description,
                            "max_tokens": model.max_tokens,
                            "supports_chat": model.supports_chat,
                            "supports_completion": model.supports_completion,
                            "supports_streaming": model.supports_streaming,
                            "metadata": model.metadata
                        })
                    
                    matches.append(model_data)
        
        return {
            "action": "search_models",
            "search_term": search_term,
            "match_count": len(matches),
            "models": matches
        }