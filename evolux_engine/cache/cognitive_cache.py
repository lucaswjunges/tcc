import json
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from evolux_engine.schemas.contracts import Task

class CognitiveCache:
    """
    Armazena e recupera soluções para tarefas, evitando chamadas repetitivas à LLM.
    O cache é baseado na semântica da tarefa, não apenas no texto exato do prompt.
    Versão melhorada com TTL, limpeza automática e matching semântico.
    """
    def __init__(self, default_ttl: int = 3600, max_cache_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}  # key -> {data, timestamp, access_count}
        self._semantic_index: Dict[str, List[str]] = {}  # palavra -> [keys]
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self._last_cleanup = time.time()
        self._access_stats = {"hits": 0, "misses": 0}
        logger.info(f"CognitiveCache inicializado com TTL={default_ttl}s, max_size={max_cache_size}")

    def _generate_cache_key(self, task: Task) -> str:
        """
        Gera uma chave de cache baseada no tipo e na descrição semântica da tarefa.
        Versão melhorada com hash para consistência.
        """
        # Criar dados normalizados para hashing
        task_data = {
            "type": task.type.value,
            "description": task.description.lower().strip(),
        }
        
        # Adicionar detalhes relevantes se disponíveis
        if hasattr(task, 'details') and task.details:
            if hasattr(task.details, 'expected_outcome'):
                task_data["expected_outcome"] = task.details.expected_outcome.lower().strip()
            if hasattr(task.details, 'file_path'):
                task_data["file_path"] = task.details.file_path
                
        # Gerar hash consistente
        task_str = json.dumps(task_data, sort_keys=True)
        return hashlib.md5(task_str.encode()).hexdigest()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave de um texto para indexação semântica."""
        import re
        
        # Remove caracteres especiais e divide em palavras
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove palavras muito comuns (stop words básicas)
        stop_words = {'e', 'o', 'a', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'por', 'ser', 'ter', 'que', 'se', 'na', 'no', 'as', 'os'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return list(set(keywords))  # Remove duplicatas
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry['timestamp'] > self.default_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_from_semantic_index(key)
            del self._cache[key]
            
        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
    
    def _remove_from_semantic_index(self, key: str):
        """Remove uma chave do índice semântico."""
        for keywords in self._semantic_index.values():
            if key in keywords:
                keywords.remove(key)
    
    def _evict_least_used(self):
        """Remove as entradas menos usadas quando o cache está cheio."""
        if len(self._cache) <= self.max_cache_size:
            return
            
        # Ordenar por número de acessos e timestamp
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: (x[1]['access_count'], x[1]['timestamp'])
        )
        
        # Remove 20% das entradas menos usadas
        remove_count = len(self._cache) // 5
        for key, _ in sorted_items[:remove_count]:
            self._remove_from_semantic_index(key)
            del self._cache[key]
            
        logger.info(f"Cache eviction: removed {remove_count} least used entries")

    def get(self, task: Task) -> Optional[Any]:
        """
        Tenta recuperar uma solução em cache para uma determinada tarefa.
        Versão melhorada com limpeza automática e estatísticas.
        """
        # Limpeza periódica do cache
        current_time = time.time()
        if current_time - self._last_cleanup > 300:  # Cleanup a cada 5 minutos
            self._cleanup_expired()
            self._last_cleanup = current_time
        
        key = self._generate_cache_key(task)
        entry = self._cache.get(key)

        if entry and current_time - entry['timestamp'] <= self.default_ttl:
            # Atualizar estatísticas de acesso
            entry['access_count'] += 1
            entry['last_access'] = current_time
            self._access_stats["hits"] += 1
            
            logger.info(f"Cache HIT para a tarefa: {task.description[:50]}... (accessed {entry['access_count']} times)")
            return entry['data']
        
        # Tentar busca semântica se busca exata falhou
        semantic_result = self._semantic_search(task)
        if semantic_result:
            self._access_stats["hits"] += 1
            logger.info(f"Cache SEMANTIC HIT para a tarefa: {task.description[:50]}...")
            return semantic_result
        
        self._access_stats["misses"] += 1
        logger.info(f"Cache MISS para a tarefa: {task.description[:50]}...")
        return None
    
    def _semantic_search(self, task: Task) -> Optional[Any]:
        """Busca semântica baseada em palavras-chave."""
        keywords = self._extract_keywords(task.description)
        if not keywords:
            return None
            
        # Encontrar chaves que compartilham palavras-chave
        candidate_keys = set()
        for keyword in keywords:
            if keyword in self._semantic_index:
                candidate_keys.update(self._semantic_index[keyword])
        
        if not candidate_keys:
            return None
            
        # Avaliar candidatos por relevância
        best_score = 0
        best_result = None
        current_time = time.time()
        
        for key in candidate_keys:
            entry = self._cache.get(key)
            if not entry or current_time - entry['timestamp'] > self.default_ttl:
                continue
                
            # Calcular score de similaridade simples
            score = len(set(keywords) & set(entry.get('keywords', [])))
            if score > best_score:
                best_score = score
                best_result = entry['data']
                
        return best_result if best_score >= len(keywords) * 0.5 else None  # Pelo menos 50% de match

    def put(self, task: Task, solution: Any):
        """
        Armazena a solução de uma tarefa no cache.
        A solução deve ser um objeto serializável em JSON.
        """
        if not isinstance(solution, (dict, list, str, int, float, bool, type(None))):
            logger.warning(f"Solução para a tarefa {task.task_id} não é serializável em JSON e não será armazenada em cache.")
            return

        # Verificar e fazer limpeza se necessário
        self._evict_least_used()

        key = self._generate_cache_key(task)
        keywords = self._extract_keywords(task.description)
        current_time = time.time()

        try:
            # Armazenar com metadados
            entry = {
                'data': solution,
                'timestamp': current_time,
                'last_access': current_time,
                'access_count': 0,
                'keywords': keywords,
                'task_type': task.type.value
            }
            
            self._cache[key] = entry
            
            # Atualizar índice semântico
            for keyword in keywords:
                if keyword not in self._semantic_index:
                    self._semantic_index[keyword] = []
                self._semantic_index[keyword].append(key)
            
            logger.info(f"Solução para a tarefa '{task.description[:50]}...' armazenada no cache com {len(keywords)} palavras-chave.")
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Erro ao serializar solução para a tarefa {task.task_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_requests = self._access_stats["hits"] + self._access_stats["misses"]
        hit_rate = (self._access_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._cache),
            "max_size": self.max_cache_size,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_hits": self._access_stats["hits"],
            "total_misses": self._access_stats["misses"],
            "semantic_keywords": len(self._semantic_index),
            "ttl_seconds": self.default_ttl
        }

    def clear(self):
        """Limpa completamente o cache."""
        self._cache.clear()
        self._semantic_index.clear()
        self._access_stats = {"hits": 0, "misses": 0}
        logger.info("Cache completamente limpo.")

# Singleton para garantir que o mesmo cache seja usado em todo o sistema
_cognitive_cache_instance: Optional[CognitiveCache] = None

def get_cognitive_cache() -> CognitiveCache:
    """Retorna a instância singleton do CognitiveCache."""
    global _cognitive_cache_instance
    if _cognitive_cache_instance is None:
        _cognitive_cache_instance = CognitiveCache()
    return _cognitive_cache_instance
