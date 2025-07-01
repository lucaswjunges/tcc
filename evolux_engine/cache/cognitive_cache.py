import json
from typing import Optional, Dict, Any
from loguru import logger
from evolux_engine.schemas.contracts import Task

class CognitiveCache:
    """
    Armazena e recupera soluções para tarefas, evitando chamadas repetitivas à LLM.
    O cache é baseado na semântica da tarefa, não apenas no texto exato do prompt.
    """
    def __init__(self):
        self._cache: Dict[str, str] = {}
        logger.info("CognitiveCache inicializado.")

    def _generate_cache_key(self, task: Task) -> str:
        """
        Gera uma chave de cache baseada no tipo e na descrição semântica da tarefa.
        Esta é uma implementação simples; uma versão mais avançada usaria embeddings vetoriais.
        """
        # Normalizar a descrição para criar uma chave mais robusta
        normalized_description = "".join(filter(str.isalnum, task.description.lower()))
        key = f"{task.type.value}:{normalized_description}"
        # Limitar o tamanho da chave para evitar problemas
        return key[:256]

    def get(self, task: Task) -> Optional[Any]:
        """
        Tenta recuperar uma solução em cache para uma determinada tarefa.
        """
        key = self._generate_cache_key(task)
        cached_solution_json = self._cache.get(key)

        if cached_solution_json:
            logger.info(f"Cache HIT para a tarefa: {task.description[:50]}...")
            try:
                return json.loads(cached_solution_json)
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar solução em cache para a chave: {key}")
                return None
        
        logger.info(f"Cache MISS para a tarefa: {task.description[:50]}...")
        return None

    def put(self, task: Task, solution: Any):
        """
        Armazena a solução de uma tarefa no cache.
        A solução deve ser um objeto serializável em JSON.
        """
        if not isinstance(solution, (dict, list, str, int, float, bool, type(None))):
            logger.warning(f"Solução para a tarefa {task.task_id} não é serializável em JSON e não será armazenada em cache.")
            return

        key = self._generate_cache_key(task)
        try:
            solution_json = json.dumps(solution)
            self._cache[key] = solution_json
            logger.info(f"Solução para a tarefa '{task.description[:50]}...' armazenada em cache.")
        except TypeError as e:
            logger.error(f"Erro ao serializar solução para JSON para a chave {key}: {e}")

    def clear(self):
        """Limpa todo o cache."""
        self._cache.clear()
        logger.info("CognitiveCache foi limpo.")

# Singleton para garantir que o mesmo cache seja usado em todo o sistema
_cognitive_cache_instance: Optional[CognitiveCache] = None

def get_cognitive_cache() -> CognitiveCache:
    """Retorna a instância singleton do CognitiveCache."""
    global _cognitive_cache_instance
    if _cognitive_cache_instance is None:
        _cognitive_cache_instance = CognitiveCache()
    return _cognitive_cache_instance
