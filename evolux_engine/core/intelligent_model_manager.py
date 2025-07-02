"""
Sistema inteligente de gerenciamento de modelos que detecta falhas e ajusta automaticamente.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from evolux_engine.schemas.contracts import TaskCategory

logger = logging.getLogger(__name__)

@dataclass
class ModelFailureInfo:
    """Informações sobre falhas de um modelo específico."""
    model_name: str
    failure_count: int = 0
    empty_response_count: int = 0
    total_requests: int = 0
    last_failure: Optional[datetime] = None
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=10))
    
    @property
    def failure_rate(self) -> float:
        """Taxa de falha do modelo."""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests
    
    @property
    def empty_response_rate(self) -> float:
        """Taxa de respostas vazias do modelo."""
        if self.total_requests == 0:
            return 0.0
        return self.empty_response_count / self.total_requests

@dataclass
class ModelPerformanceMetrics:
    """Métricas de performance de um modelo."""
    model_name: str
    avg_response_time: float = 0.0
    success_count: int = 0
    total_tokens_generated: int = 0
    quality_score: float = 1.0  # 0.0 to 1.0
    last_updated: datetime = field(default_factory=datetime.now)

class IntelligentModelManager:
    """
    Gerenciador inteligente que monitora performance de modelos e ajusta seleção automaticamente.
    """
    
    def __init__(self):
        self.failure_info: Dict[str, ModelFailureInfo] = {}
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.blacklisted_models: set = set()
        self.model_rankings: Dict[TaskCategory, List[str]] = {}
        
        # Configurações de detecção de problemas
        self.max_failure_rate = 0.4  # 40% de falhas máximo
        self.max_empty_response_rate = 0.3  # 30% de respostas vazias máximo
        self.min_requests_for_evaluation = 5  # Mínimo de requests para avaliar
        self.blacklist_duration = timedelta(minutes=30)  # Tempo em blacklist
        
        # Inicializar rankings padrão
        self._initialize_default_rankings()
        
    def _initialize_default_rankings(self):
        """Inicializa rankings padrão baseados na experiência."""
        default_ranking = [
            "gemini-2.5-flash",
            "gemini-2.5-pro", 
            "anthropic/claude-3-haiku",
            "gpt-4o-mini",
            "gemini-1.5-flash",
            "gpt-3.5-turbo",
            "deepseek/deepseek-r1-0528-qwen3-8b:free"  # Último devido a problemas conhecidos
        ]
        
        for category in TaskCategory:
            self.model_rankings[category] = default_ranking.copy()
    
    def record_request(self, model_name: str, success: bool, response_empty: bool = False, 
                      response_time: float = 0.0, tokens_generated: int = 0):
        """
        Registra uma requisição ao modelo para análise.
        """
        # Inicializar estruturas se necessário
        if model_name not in self.failure_info:
            self.failure_info[model_name] = ModelFailureInfo(model_name)
            
        if model_name not in self.performance_metrics:
            self.performance_metrics[model_name] = ModelPerformanceMetrics(model_name)
        
        # Atualizar contadores de falha
        failure_info = self.failure_info[model_name]
        failure_info.total_requests += 1
        
        if not success:
            failure_info.failure_count += 1
            failure_info.last_failure = datetime.now()
            failure_info.recent_failures.append(datetime.now())
            
        if response_empty:
            failure_info.empty_response_count += 1
            
        # Atualizar métricas de performance
        performance = self.performance_metrics[model_name]
        if success:
            performance.success_count += 1
            performance.total_tokens_generated += tokens_generated
            
        # Atualizar tempo de resposta com média móvel
        if response_time > 0:
            alpha = 0.3  # Fator de suavização
            performance.avg_response_time = (alpha * response_time + 
                                           (1 - alpha) * performance.avg_response_time)
        
        performance.last_updated = datetime.now()
        
        # Verificar se deve blacklistar
        self._evaluate_model_health(model_name)
        
    def _evaluate_model_health(self, model_name: str):
        """
        Avalia a saúde de um modelo e decide se deve ser blacklistado.
        """
        failure_info = self.failure_info[model_name]
        
        # Só avaliar se tiver requests suficientes
        if failure_info.total_requests < self.min_requests_for_evaluation:
            return
            
        # Verificar taxa de falhas
        if failure_info.failure_rate > self.max_failure_rate:
            self._blacklist_model(model_name, f"Taxa de falhas muito alta: {failure_info.failure_rate:.2%}")
            return
            
        # Verificar taxa de respostas vazias
        if failure_info.empty_response_rate > self.max_empty_response_rate:
            self._blacklist_model(model_name, f"Muitas respostas vazias: {failure_info.empty_response_rate:.2%}")
            return
            
        # Verificar falhas recentes (últimos 5 minutos)
        recent_cutoff = datetime.now() - timedelta(minutes=5)
        recent_failures = [f for f in failure_info.recent_failures if f > recent_cutoff]
        
        if len(recent_failures) >= 3:
            self._blacklist_model(model_name, f"Muitas falhas recentes: {len(recent_failures)} em 5 minutos")
            
    def _blacklist_model(self, model_name: str, reason: str):
        """
        Adiciona modelo à blacklist temporariamente.
        """
        if model_name not in self.blacklisted_models:
            self.blacklisted_models.add(model_name)
            logger.warning(f"🚫 Modelo '{model_name}' foi blacklistado: {reason}")
            
            # Remover modelo dos rankings temporariamente
            for category in self.model_rankings:
                if model_name in self.model_rankings[category]:
                    self.model_rankings[category].remove(model_name)
                    
    def get_best_model_for_category(self, category: TaskCategory) -> Optional[str]:
        """
        Retorna o melhor modelo disponível para uma categoria.
        """
        # Limpar blacklist expirada
        self._cleanup_expired_blacklist()
        
        # Retornar primeiro modelo não blacklistado
        for model_name in self.model_rankings.get(category, []):
            if model_name not in self.blacklisted_models:
                return model_name
                
        # Se todos estão blacklistados, retornar o primeiro (situação de emergência)
        if self.model_rankings.get(category):
            emergency_model = self.model_rankings[category][0]
            logger.warning(f"⚠️ Todos os modelos estão blacklistados para {category}, usando {emergency_model} como emergência")
            return emergency_model
            
        return None
        
    def _cleanup_expired_blacklist(self):
        """
        Remove modelos da blacklist que já expiraram.
        """
        now = datetime.now()
        to_remove = set()
        
        for model_name in self.blacklisted_models:
            failure_info = self.failure_info.get(model_name)
            if failure_info and failure_info.last_failure:
                if now - failure_info.last_failure > self.blacklist_duration:
                    to_remove.add(model_name)
                    logger.info(f"✅ Modelo '{model_name}' removido da blacklist após período de cooldown")
                    
        # Remover da blacklist e restaurar nos rankings
        for model_name in to_remove:
            self.blacklisted_models.discard(model_name)
            self._restore_model_to_rankings(model_name)
            
    def _restore_model_to_rankings(self, model_name: str):
        """
        Restaura um modelo aos rankings em sua posição original.
        """
        default_rankings = {
            TaskCategory.CODE_GENERATION: [
                "gemini-2.5-flash", "gemini-2.5-pro", "anthropic/claude-3-haiku",
                "gpt-4o-mini", "gemini-1.5-flash", "gpt-3.5-turbo",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ],
            TaskCategory.PLANNING: [
                "gemini-2.5-flash", "gemini-2.5-pro", "anthropic/claude-3-haiku",
                "gpt-4o-mini", "gemini-1.5-flash", "gpt-3.5-turbo",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ],
            TaskCategory.VALIDATION: [
                "gemini-2.5-flash", "gemini-2.5-pro", "anthropic/claude-3-haiku",
                "gpt-4o-mini", "gemini-1.5-flash", "gpt-3.5-turbo",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ]
        }
        
        for category, default_ranking in default_rankings.items():
            if model_name in default_ranking and model_name not in self.model_rankings[category]:
                # Inserir na posição original
                original_position = default_ranking.index(model_name)
                self.model_rankings[category].insert(original_position, model_name)
                
    def get_model_statistics(self) -> Dict[str, Dict]:
        """
        Retorna estatísticas detalhadas de todos os modelos.
        """
        stats = {}
        
        for model_name in set(list(self.failure_info.keys()) + list(self.performance_metrics.keys())):
            failure_info = self.failure_info.get(model_name, ModelFailureInfo(model_name))
            performance = self.performance_metrics.get(model_name, ModelPerformanceMetrics(model_name))
            
            stats[model_name] = {
                "total_requests": failure_info.total_requests,
                "failure_rate": failure_info.failure_rate,
                "empty_response_rate": failure_info.empty_response_rate,
                "success_count": performance.success_count,
                "avg_response_time": performance.avg_response_time,
                "tokens_generated": performance.total_tokens_generated,
                "is_blacklisted": model_name in self.blacklisted_models,
                "last_failure": failure_info.last_failure.isoformat() if failure_info.last_failure else None
            }
            
        return stats
        
    def force_unblacklist_model(self, model_name: str):
        """
        Remove um modelo da blacklist à força (para casos de emergência).
        """
        if model_name in self.blacklisted_models:
            self.blacklisted_models.discard(model_name)
            self._restore_model_to_rankings(model_name)
            logger.info(f"🔓 Modelo '{model_name}' foi forçadamente removido da blacklist")
            
    def reset_model_stats(self, model_name: str):
        """
        Reseta as estatísticas de um modelo específico.
        """
        if model_name in self.failure_info:
            del self.failure_info[model_name]
        if model_name in self.performance_metrics:
            del self.performance_metrics[model_name]
        logger.info(f"🔄 Estatísticas do modelo '{model_name}' foram resetadas")