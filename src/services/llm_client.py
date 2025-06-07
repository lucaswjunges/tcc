# src/services/llm_client.py (VERSÃO CORRIGIDA)
import os
from openai import OpenAI
from src.services.observability_service import log

class LLMClient:
    """
    Cliente unificado para interagir com diferentes provedores de LLM.
    Atualmente suporta OpenRouter.
    """
    def __init__(self, provider: str, api_key: str = None):
        """
        Inicializa o cliente LLM.

        Args:
            provider (str): O nome do provedor de LLM (ex: 'openrouter').
            api_key (str, optional): A chave de API. Se não for fornecida,
                                     ela será lida da variável de ambiente.
        """
        self.provider = provider
        log.info(f"Initializing LLMClient for provider: {self.provider}")

        if self.provider == "openrouter":
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                raise ValueError("OpenRouter API key not found. Please set it in .env as OPENROUTER_API_KEY.")
            
            # OpenRouter usa a mesma interface do cliente OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            log.info("OpenRouter client configured successfully.")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def call_llm(self, model: str, messages: list, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """
        Faz uma chamada para o modelo de linguagem.

        Args:
            model (str): O nome do modelo a ser usado (ex: 'anthropic/claude-3-haiku').
            messages (list): A lista de mensagens no formato da API OpenAI.
            temperature (float): A temperatura para a geração.
            max_tokens (int): O número máximo de tokens a serem gerados.

        Returns:
            str: A resposta do modelo.
        """
        try:
            log.info(f"Calling LLM: {model} with {len(messages)} messages.")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            log.info(f"LLM call successful. Received response from {model}.", response_length=len(content))
            return content
        except Exception as e:
            log.critical(f"LLM call failed for model {model}.", error=str(e), exc_info=True)
            raise

