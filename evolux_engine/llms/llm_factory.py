# Conteúdo para: evolux_engine/llms/llm_factory.py
from typing import Optional
# import os # Não precisamos mais de os.getenv aqui se a API key é passada explicitamente

from .llm_client import LLMClient
from evolux_engine.utils.logging_utils import log
# from evolux_engine.utils.env_vars import settings # Só se precisar de outras configs da factory

class LLMFactory:
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa a LLMFactory.
        A api_key deve ser fornecida aqui, vinda das configurações do agente principal.
        """
        if not api_key:
            log.error("LLMFactory: API key não fornecida na inicialização.")
            # Alternativamente, poderia tentar buscar de settings.OPENROUTER_API_KEY ou settings.OPENAI_API_KEY
            # mas é melhor que o Agent controle qual chave passar.
            raise ValueError("API key deve ser fornecida para LLMFactory.")
        
        self.api_key = api_key
        log.info(f"LLMFactory initialized com API key fornecida.")

    def get_llm_client(self, model: str) -> LLMClient: # Modelo agora é obrigatório
        """
        Retorna uma instância configurada de LLMClient para um modelo específico.
        """
        if not model:
            log.error("LLMFactory.get_llm_client: Nome do modelo não fornecido.")
            raise ValueError("Nome do modelo é obrigatório para obter um LLMClient.")
            
        log.info(f"LLMFactory criando LLMClient para o modelo: {model}")
        # Aqui você poderia ter lógica para diferentes tipos de clientes se suportar mais que OpenRouter
        # Por exemplo, se model indicar OpenAI, instanciar um OpenAIClient.
        # Por enquanto, assume que todos os modelos são acessados via o mesmo LLMClient (OpenRouter).
        return LLMClient(api_key=self.api_key, model=model)
