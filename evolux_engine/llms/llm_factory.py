from typing import Dict, Optional
from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.llms.model_router import ModelRouter, TaskCategory
from evolux_engine.schemas.contracts import LLMProvider
from evolux_engine.services.config_manager import ConfigManager

class LLMFactory:
    """
    Fábrica responsável por criar e gerenciar instâncias de LLMClient.
    Utiliza um ModelRouter para selecionar o modelo ideal e gerenciar fallbacks.
    """
    _clients: Dict[str, LLMClient] = {}
    _model_router: Optional[ModelRouter] = None
    _config_manager: Optional[ConfigManager] = None

    @classmethod
    def _initialize(cls):
        """Inicializa os componentes singletons da fábrica."""
        if cls._model_router is None:
            cls._model_router = ModelRouter()
        if cls._config_manager is None:
            cls._config_manager = ConfigManager()

    @classmethod
    def get_client(
        cls,
        task_category: TaskCategory,
        prefer_cost_optimization: bool = True
    ) -> LLMClient:
        """
        Obtém um cliente LLM configurado para a tarefa especificada.
        A seleção do modelo é delegada ao ModelRouter.
        """
        cls._initialize()

        model_name = cls._model_router.select_model(
            task_category=task_category,
            prefer_cost_optimization=prefer_cost_optimization
        )
        
        if not model_name:
            raise ValueError(f"Nenhum modelo disponível encontrado para a categoria de tarefa: {task_category.value}")

        # A chave do cliente é baseada apenas no nome do modelo, pois ele é único
        if model_name not in cls._clients:
            logger.info(f"Criando novo cliente LLM para o modelo selecionado: {model_name}")
            
            model_info = cls._model_router.available_models.get(model_name)
            if not model_info:
                raise ValueError(f"Informações do modelo '{model_name}' não encontradas no ModelRouter.")

            provider = model_info.provider
            api_key = cls._config_manager.get_api_key(provider.value)
            if not api_key:
                raise ValueError(f"API Key para o provedor '{provider.value}' não encontrada.")

            cls._clients[model_name] = LLMClient(
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                model_router=cls._model_router,
                http_referer=cls._config_manager.get_global_setting("openrouter_http_referer"),
                x_title=cls._config_manager.get_global_setting("openrouter_x_title")
            )
        
        logger.debug(f"Retornando cliente LLM para o modelo: {model_name}")
        return cls._clients[model_name]
