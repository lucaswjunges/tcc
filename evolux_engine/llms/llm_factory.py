from typing import Dict, Type, Optional, Any
import asyncio
from dataclasses import dataclass

from evolux_engine.schemas.contracts import LLMProvider
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.llms.model_router import ModelRouter, TaskCategory
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("llm_factory")

@dataclass
class LLMConfiguration:
    """Configuração para criação de cliente LLM"""
    provider: LLMProvider
    api_key: str
    model_name: str
    api_base_url: Optional[str] = None
    timeout: int = 180
    max_retries: int = 3
    http_referer: Optional[str] = None
    x_title: Optional[str] = None

class LLMFactory:
    """
    Factory para criação e gerenciamento de clientes LLM com:
    - Roteamento inteligente de modelos
    - Pool de conexões reutilizáveis  
    - Fallback automático em caso de falha
    - Otimização de custo vs performance
    """
    
    def __init__(self, model_router: Optional[ModelRouter] = None):
        self.model_router = model_router or ModelRouter()
        self.client_pool: Dict[str, LLMClient] = {}
        self.configurations: Dict[LLMProvider, LLMConfiguration] = {}
        self.active_connections = 0
        
        logger.info("LLMFactory initialized", 
                   router_models=len(self.model_router.available_models))
    
    def configure_provider(self, provider: LLMProvider, config: LLMConfiguration):
        """Configura um provedor de LLM"""
        self.configurations[provider] = config
        logger.info("Provider configured", 
                   provider=provider.value,
                   model=config.model_name)
    
    def configure_from_advanced_config(self, config: 'AdvancedSystemConfig'):
        """Configura provedores baseado no AdvancedSystemConfig"""
        
        # OpenRouter configuration
        openrouter_key = config.get_api_key("openrouter")
        if openrouter_key:
            self.configure_provider(
                LLMProvider.OPENROUTER,
                LLMConfiguration(
                    provider=LLMProvider.OPENROUTER,
                    api_key=openrouter_key,
                    model_name=config.default_model_executor,
                    api_base_url="https://openrouter.ai/api/v1",
                    timeout=config.request_timeout,
                    max_retries=config.max_retries,
                    http_referer=config.http_referer,
                    x_title=config.x_title
                )
            )
        
        # OpenAI configuration
        openai_key = config.get_api_key("openai")
        if openai_key:
            self.configure_provider(
                LLMProvider.OPENAI,
                LLMConfiguration(
                    provider=LLMProvider.OPENAI,
                    api_key=openai_key,
                    model_name="gpt-4o-mini",
                    api_base_url="https://api.openai.com/v1",
                    timeout=config.request_timeout,
                    max_retries=config.max_retries
                )
            )
        
        # Google configuration
        google_key = config.get_api_key("google")
        if google_key:
            self.configure_provider(
                LLMProvider.GOOGLE,
                LLMConfiguration(
                    provider=LLMProvider.GOOGLE,
                    api_key=google_key,
                    model_name="gemini-2.5-flash",
                    timeout=config.request_timeout,
                    max_retries=config.max_retries
                )
            )
        
        logger.info("LLM Factory configured from AdvancedSystemConfig",
                   providers_configured=len(self.configurations),
                   default_model=config.default_model_executor)
    
    def configure_from_env(self, config_manager):
        """Configura provedores baseado no ConfigManager (compatibilidade)"""
        
        # OpenRouter configuration
        openrouter_key = config_manager.get_api_key("openrouter")
        if openrouter_key:
            self.configure_provider(
                LLMProvider.OPENROUTER,
                LLMConfiguration(
                    provider=LLMProvider.OPENROUTER,
                    api_key=openrouter_key,
                    model_name=config_manager.get_global_setting("default_model_executor", "gemini-2.5-flash"),
                    api_base_url="https://openrouter.ai/api/v1",
                    http_referer=config_manager.get_global_setting("http_referer"),
                    x_title=config_manager.get_global_setting("x_title", "Evolux Engine")
                )
            )
        
        # OpenAI configuration
        openai_key = config_manager.get_api_key("openai")
        if openai_key:
            self.configure_provider(
                LLMProvider.OPENAI,
                LLMConfiguration(
                    provider=LLMProvider.OPENAI,
                    api_key=openai_key,
                    model_name="gpt-4o-mini",
                    api_base_url="https://api.openai.com/v1"
                )
            )
        
        # Google configuration
        google_key = config_manager.get_api_key("google")
        if google_key:
            self.configure_provider(
                LLMProvider.GOOGLE,
                LLMConfiguration(
                    provider=LLMProvider.GOOGLE,
                    api_key=google_key,
                    model_name="gemini-2.5-flash"
                )
            )
    
    async def create_client(self, 
                           task_category: TaskCategory = TaskCategory.GENERIC,
                           prefer_cost_optimization: bool = False,
                           required_tokens: int = 2000,
                           force_model: Optional[str] = None) -> Optional[LLMClient]:
        """
        Cria cliente LLM otimizado para a categoria de tarefa.
        
        Args:
            task_category: Categoria da tarefa para otimização
            prefer_cost_optimization: Priorizar custo vs qualidade
            required_tokens: Tokens estimados necessários
            force_model: Forçar uso de modelo específico
            
        Returns:
            Cliente LLM configurado ou None se não disponível
        """
        
        # Selecionar modelo
        if force_model:
            selected_model = force_model
            logger.info("Using forced model", model=force_model)
        else:
            selected_model = self.model_router.select_model(
                task_category=task_category,
                prefer_cost_optimization=prefer_cost_optimization,
                required_tokens=required_tokens
            )
        
        if not selected_model:
            logger.error("No suitable model found",
                        task_category=task_category.value,
                        required_tokens=required_tokens)
            return None
        
        # Verificar se já existe cliente no pool
        if selected_model in self.client_pool:
            logger.debug("Reusing existing client", model=selected_model)
            return self.client_pool[selected_model]
        
        # Criar novo cliente
        client = await self._create_client_for_model(selected_model)
        if client:
            self.client_pool[selected_model] = client
            self.active_connections += 1
            logger.info("New LLM client created", 
                       model=selected_model,
                       active_connections=self.active_connections)
        
        return client
    
    async def _create_client_for_model(self, model_name: str) -> Optional[LLMClient]:
        """Cria cliente para modelo específico"""
        
        # Encontrar configuração do provedor
        model_info = self.model_router.available_models.get(model_name)
        if not model_info:
            logger.error("Model info not found", model=model_name)
            return None
        
        config = self.configurations.get(model_info.provider)
        if not config:
            logger.error("Provider not configured", 
                        provider=model_info.provider.value,
                        model=model_name)
            return None
        
        try:
            # Criar configuração específica para o modelo
            model_config = LLMConfiguration(
                provider=config.provider,
                api_key=config.api_key,
                model_name=model_name,  # Usar o modelo selecionado
                api_base_url=config.api_base_url,
                timeout=config.timeout,
                max_retries=config.max_retries,
                http_referer=config.http_referer,
                x_title=config.x_title
            )
            
            # Criar cliente
            client = LLMClient(
                api_key=model_config.api_key,
                model_name=model_config.model_name,
                provider=model_config.provider,
                api_base_url=model_config.api_base_url,
                timeout=model_config.timeout,
                http_referer=model_config.http_referer,
                x_title=model_config.x_title
            )
            
            logger.debug("Client created successfully", 
                        model=model_name,
                        provider=model_config.provider.value)
            
            return client
            
        except Exception as e:
            logger.error("Failed to create client",
                        model=model_name,
                        error=str(e))
            # Marcar modelo como indisponível temporariamente
            self.model_router.mark_model_unavailable(model_name)
            return None
    
    async def create_client_with_fallback(self, 
                                        task_category: TaskCategory = TaskCategory.GENERIC,
                                        prefer_cost_optimization: bool = False,
                                        max_fallbacks: int = 3) -> Optional[LLMClient]:
        """
        Cria cliente com fallback automático em caso de falha.
        
        Args:
            task_category: Categoria da tarefa
            prefer_cost_optimization: Priorizar custo
            max_fallbacks: Máximo de tentativas de fallback
            
        Returns:
            Cliente LLM funcional ou None
        """
        
        attempts = 0
        current_model = None
        
        while attempts <= max_fallbacks:
            try:
                # Primeira tentativa: seleção normal
                if attempts == 0:
                    client = await self.create_client(
                        task_category=task_category,
                        prefer_cost_optimization=prefer_cost_optimization
                    )
                    if client:
                        current_model = client.model_name
                        return client
                else:
                    # Tentativas subsequentes: usar fallback
                    fallback_model = self.model_router.get_fallback_model(current_model, task_category)
                    if not fallback_model:
                        logger.warning("No more fallback models available",
                                     current_model=current_model,
                                     attempts=attempts)
                        break
                    
                    client = await self.create_client(force_model=fallback_model)
                    if client:
                        current_model = fallback_model
                        logger.info("Fallback client created successfully",
                                   fallback_model=fallback_model,
                                   attempts=attempts)
                        return client
                    else:
                        current_model = fallback_model
                
                attempts += 1
                
            except Exception as e:
                logger.error("Client creation attempt failed",
                           attempt=attempts,
                           model=current_model,
                           error=str(e))
                attempts += 1
                
                # Pequeno delay antes da próxima tentativa
                if attempts <= max_fallbacks:
                    await asyncio.sleep(1.0)
        
        logger.error("All client creation attempts failed",
                    total_attempts=attempts,
                    task_category=task_category.value)
        return None
    
    async def update_model_performance(self, 
                                     model_name: str,
                                     task_category: TaskCategory,
                                     success: bool,
                                     latency_ms: float,
                                     cost: float = 0.0):
        """Atualiza métricas de performance do modelo"""
        self.model_router.update_model_performance(
            model_name=model_name,
            category=task_category,
            success=success,
            latency_ms=latency_ms,
            cost=cost
        )
    
    async def close_all_clients(self):
        """Fecha todas as conexões de clientes"""
        logger.info("Closing all LLM clients", count=len(self.client_pool))
        
        for model_name, client in self.client_pool.items():
            try:
                await client.close()
                logger.debug("Client closed", model=model_name)
            except Exception as e:
                logger.warning("Error closing client", 
                             model=model_name, 
                             error=str(e))
        
        self.client_pool.clear()
        self.active_connections = 0
        logger.info("All LLM clients closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde de todos os clientes configurados"""
        health_status = {
            'factory_status': 'healthy',
            'active_connections': self.active_connections,
            'configured_providers': len(self.configurations),
            'pool_size': len(self.client_pool),
            'model_router_stats': self.model_router.get_routing_stats(),
            'provider_health': {}
        }
        
        # Testar cada provedor configurado
        for provider, config in self.configurations.items():
            try:
                test_client = await self._create_client_for_model(config.model_name)
                if test_client:
                    health_status['provider_health'][provider.value] = 'healthy'
                    await test_client.close()
                else:
                    health_status['provider_health'][provider.value] = 'unhealthy'
            except Exception as e:
                health_status['provider_health'][provider.value] = f'error: {str(e)}'
        
        # Verificar se pelo menos um provedor está saudável
        healthy_providers = sum(1 for status in health_status['provider_health'].values() 
                              if status == 'healthy')
        
        if healthy_providers == 0:
            health_status['factory_status'] = 'critical'
        elif healthy_providers < len(self.configurations):
            health_status['factory_status'] = 'degraded'
        
        return health_status
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da factory"""
        return {
            'active_connections': self.active_connections,
            'pool_size': len(self.client_pool),
            'configured_providers': list(self.configurations.keys()),
            'pooled_models': list(self.client_pool.keys()),
            'router_stats': self.model_router.get_routing_stats()
        }