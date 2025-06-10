from abc import ABC, abstractmethod
from typing import Optional

class BaseLLM(ABC):
    def __init__(self, api_key: str, model_name: str): # Adicionado model_name aqui
        if not api_key:
            raise ValueError("API Key é obrigatória para o cliente LLM.")
        if not model_name:
            raise ValueError("Nome do modelo é obrigatório para o cliente LLM.")
        self.api_key = api_key
        self.model_name = model_name # Armazena o nome do modelo

    @abstractmethod
    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1500) -> Optional[str]:
        """
        Gera uma resposta baseada no prompt fornecido.

        Args:
            prompt: O texto de entrada para o LLM.
            temperature: Controla a aleatoriedade da saída.
            max_tokens: O número máximo de tokens a serem gerados.

        Returns:
            A resposta gerada pelo LLM como string, ou None em caso de erro.
        """
        pass

    # Poderiam haver outros métodos comuns aqui, como contar tokens, etc.
