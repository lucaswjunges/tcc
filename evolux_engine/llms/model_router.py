from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import LLMProvider

logger = get_structured_logger("model_router")

class TaskCategory(Enum):
    """Categorias de tarefas para seleção de modelo otimizada"""
    CODE_GENERATION = "code_generation"
    PLANNING = "planning"
    VALIDATION = "validation"
    ERROR_ANALYSIS = "error_analysis"
    DOCUMENTATION = "documentation"
    GENERIC = "generic"

@dataclass
class ModelPerformance:
    """Métricas de performance de um modelo para uma categoria específica"""
    model_name: str
    category: TaskCategory
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_per_token: float = 0.0
    total_calls: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_metrics(self, success: bool, latency_ms: float, cost: float = 0.0):
        """Atualiza métricas baseado em nova execução"""
        self.total_calls += 1
        
        # Update success rate with exponential smoothing
        alpha = 0.1  # Smoothing factor
        new_success_rate = 1.0 if success else 0.0
        self.success_rate = alpha * new_success_rate + (1 - alpha) * self.success_rate
        
        # Update latency with exponential smoothing
        self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms
        
        # Update cost
        if cost > 0:
            self.avg_cost_per_token = alpha * cost + (1 - alpha) * self.avg_cost_per_token
        
        self.last_updated = datetime.now()

@dataclass 
class ModelInfo:
    """Informações sobre um modelo disponível"""
    name: str
    provider: LLMProvider
    max_tokens: int
    cost_per_1k_tokens: float
    capabilities: List[TaskCategory]
    quality_tier: int = 1  # 1=highest, 2=medium, 3=basic
    is_available: bool = True

class ModelRouter:
    """
    Router inteligente que seleciona o modelo LLM ótimo baseado em:
    - Tipo de tarefa
    - Performance histórica
    - Custo vs qualidade
    - Disponibilidade
    """
    
    def __init__(self):
        self.available_models: Dict[str, ModelInfo] = {}
        self.performance_history: Dict[str, Dict[TaskCategory, ModelPerformance]] = {}
        self.fallback_chain: Dict[TaskCategory, List[str]] = {}
        self.provider_preference = [LLMProvider.GOOGLE, LLMProvider.OPENROUTER, LLMProvider.OPENAI]
        
        self._initialize_default_models()
        self._initialize_fallback_chains()
        
        logger.info(f"ModelRouter initialized with {len(self.available_models)} available models")
    
    def _initialize_default_models(self):
        """Inicializa modelos disponíveis com configurações padrão"""
        
        # DeepSeek models (free tier)
        self.available_models["deepseek/deepseek-r1-0528-qwen3-8b:free"] = ModelInfo(
            name="deepseek/deepseek-r1-0528-qwen3-8b:free",
            provider=LLMProvider.OPENROUTER,
            max_tokens=8000,
            cost_per_1k_tokens=0.0,  # Free
            capabilities=[TaskCategory.CODE_GENERATION, TaskCategory.PLANNING, TaskCategory.GENERIC],
            quality_tier=2
        )
        
        # OpenAI models
        self.available_models["gpt-4o-mini"] = ModelInfo(
            name="gpt-4o-mini",
            provider=LLMProvider.OPENAI,
            max_tokens=4000,
            cost_per_1k_tokens=0.0015,
            capabilities=[TaskCategory.CODE_GENERATION, TaskCategory.VALIDATION, TaskCategory.ERROR_ANALYSIS],
            quality_tier=1
        )
        
        self.available_models["gpt-3.5-turbo"] = ModelInfo(
            name="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            max_tokens=4000,
            cost_per_1k_tokens=0.0005,
            capabilities=[TaskCategory.DOCUMENTATION, TaskCategory.GENERIC],
            quality_tier=2
        )
        
        # Claude models
        self.available_models["anthropic/claude-3-haiku"] = ModelInfo(
            name="anthropic/claude-3-haiku",
            provider=LLMProvider.OPENROUTER,
            max_tokens=4000,
            cost_per_1k_tokens=0.0008,
            capabilities=[TaskCategory.CODE_GENERATION, TaskCategory.VALIDATION],
            quality_tier=1
        )
        
        # Gemini models
        self.available_models["gemini-1.5-flash"] = ModelInfo(
            name="gemini-1.5-flash",
            provider=LLMProvider.GOOGLE,
            max_tokens=8000,
            cost_per_1k_tokens=0.0002,
            capabilities=[TaskCategory.PLANNING, TaskCategory.DOCUMENTATION, TaskCategory.GENERIC],
            quality_tier=2
        )
        
        # Gemini 2.5 Flash - Fast and efficient model for most tasks
        self.available_models["gemini-2.5-flash"] = ModelInfo(
            name="gemini-2.5-flash",
            provider=LLMProvider.GOOGLE,
            max_tokens=32000,
            cost_per_1k_tokens=0.002,  # Much more cost-effective than Pro
            capabilities=[TaskCategory.CODE_GENERATION, TaskCategory.PLANNING, TaskCategory.VALIDATION, 
                         TaskCategory.ERROR_ANALYSIS, TaskCategory.DOCUMENTATION, TaskCategory.GENERIC],
            quality_tier=1  # High quality tier with better speed
        )
        
        # Gemini 2.5 Pro - Premium model for complex tasks (keeping as fallback)
        self.available_models["gemini-2.5-pro"] = ModelInfo(
            name="gemini-2.5-pro",
            provider=LLMProvider.GOOGLE,
            max_tokens=32000,
            cost_per_1k_tokens=0.01,  # Premium pricing
            capabilities=[TaskCategory.CODE_GENERATION, TaskCategory.PLANNING, TaskCategory.VALIDATION, 
                         TaskCategory.ERROR_ANALYSIS, TaskCategory.DOCUMENTATION, TaskCategory.GENERIC],
            quality_tier=1  # Highest quality tier
        )
    
    def _initialize_fallback_chains(self):
        """Define cadeias de fallback por categoria"""
        self.fallback_chain = {
            TaskCategory.CODE_GENERATION: [
                "gemini-2.5-flash",  # Fast and efficient for most code generation
                "gemini-2.5-pro",   # Fallback to Pro for complex cases
                "anthropic/claude-3-haiku",
                "gpt-4o-mini",
                "gemini-1.5-flash",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"  # Moved to last due to content issues
            ],
            TaskCategory.PLANNING: [
                "gemini-2.5-flash",  # Fast planning with excellent quality
                "gemini-2.5-pro",   # For complex planning scenarios
                "anthropic/claude-3-haiku",
                "gpt-4o-mini",
                "gemini-1.5-flash",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"  # Moved to last due to empty responses
            ],
            TaskCategory.VALIDATION: [
                "gemini-2.5-flash",  # Fast validation with strong reasoning
                "gemini-2.5-pro",   # For complex validation cases
                "anthropic/claude-3-haiku",
                "gpt-4o-mini",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ],
            TaskCategory.ERROR_ANALYSIS: [
                "gemini-2.5-flash",  # Excellent for error analysis with speed
                "gemini-2.5-pro",   # For very complex error scenarios
                "gpt-4o-mini",
                "anthropic/claude-3-haiku",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ],
            TaskCategory.DOCUMENTATION: [
                "gemini-2.5-flash",  # Great for fast documentation generation
                "gemini-2.5-pro",   # For comprehensive documentation
                "gemini-1.5-flash",
                "gpt-3.5-turbo",
                "deepseek/deepseek-r1-0528-qwen3-8b:free"
            ],
            TaskCategory.GENERIC: [
                "gemini-2.5-flash",  # Primary general purpose model
                "gemini-2.5-pro",   # Fallback for complex generic tasks
                "deepseek/deepseek-r1-0528-qwen3-8b:free",
                "gemini-1.5-flash",
                "gpt-3.5-turbo"
            ]
        }
    
    def select_model(self, 
                    task_category: TaskCategory,
                    prefer_cost_optimization: bool = True,
                    required_tokens: int = 2000) -> Optional[str]:
        """
        Seleciona o modelo ótimo para uma categoria de tarefa.
        
        Args:
            task_category: Categoria da tarefa
            prefer_cost_optimization: Se deve priorizar custo vs qualidade
            required_tokens: Tokens necessários estimados
            
        Returns:
            Nome do modelo selecionado ou None se nenhum disponível
        """
        
        # Filtrar modelos compatíveis
        compatible_models = []
        for model_name, model_info in self.available_models.items():
            if (task_category in model_info.capabilities and 
                model_info.is_available and
                model_info.max_tokens >= required_tokens):
                compatible_models.append((model_name, model_info))
        
        if not compatible_models:
            logger.warning(f"No compatible models found for task_category: {task_category.value}, required_tokens: {required_tokens}")
            return None
        
        # Aplicar estratégia de seleção
        if prefer_cost_optimization:
            selected = self._select_by_cost_efficiency(compatible_models, task_category)
        else:
            selected = self._select_by_quality(compatible_models, task_category)
        
        logger.info(f"Model selected: {selected} for task_category: {task_category.value} with strategy: {'cost_optimization' if prefer_cost_optimization else 'quality'}")
        
        return selected
    
    def _select_by_cost_efficiency(self, 
                                  models: List[tuple], 
                                  category: TaskCategory) -> str:
        """Seleciona modelo baseado em eficiência de custo"""
        
        # Prioriza modelos gratuitos primeiro
        free_models = [(name, info) for name, info in models if info.cost_per_1k_tokens == 0.0]
        if free_models:
            # Entre os gratuitos, escolhe por performance histórica
            return self._select_by_performance(free_models, category)
        
        # Se não há modelos gratuitos, otimiza por custo-benefício
        scored_models = []
        for model_name, model_info in models:
            perf = self._get_performance(model_name, category)
            
            # Score baseado em: success_rate / (cost * latency_factor)
            cost_factor = max(model_info.cost_per_1k_tokens, 0.0001)  # Evita divisão por zero
            latency_factor = max(perf.avg_latency_ms / 1000.0, 0.1)   # Normaliza latência
            
            score = perf.success_rate / (cost_factor * latency_factor)
            scored_models.append((model_name, score))
        
        # Retorna modelo com melhor score
        best_model = max(scored_models, key=lambda x: x[1])
        return best_model[0]
    
    def _select_by_quality(self, 
                          models: List[tuple], 
                          category: TaskCategory) -> str:
        """Seleciona modelo baseado em qualidade máxima"""
        
        # Prefer Gemini 2.5 Flash first (optimal balance of speed and quality)
        for model_name, model_info in models:
            if model_name == "gemini-2.5-flash":
                return model_name
        
        # Then prefer Gemini 2.5 Pro if Flash not available
        for model_name, model_info in models:
            if model_name == "gemini-2.5-pro":
                return model_name
        
        # Fallback to original logic if no Gemini models available
        quality_sorted = sorted(models, key=lambda x: (x[1].quality_tier, -self._get_performance(x[0], category).success_rate))
        return quality_sorted[0][0]
    
    def _select_by_performance(self, 
                              models: List[tuple], 
                              category: TaskCategory) -> str:
        """Seleciona modelo baseado apenas em performance histórica"""
        
        if len(models) == 1:
            return models[0][0]
        
        performance_scored = []
        for model_name, _ in models:
            perf = self._get_performance(model_name, category)
            # Score considera success rate e inverso da latência
            score = perf.success_rate - (perf.avg_latency_ms / 10000.0)
            performance_scored.append((model_name, score))
        
        best_model = max(performance_scored, key=lambda x: x[1])
        return best_model[0]
    
    def _get_performance(self, model_name: str, category: TaskCategory) -> ModelPerformance:
        """Obtém métricas de performance ou cria padrão"""
        
        if model_name not in self.performance_history:
            self.performance_history[model_name] = {}
        
        if category not in self.performance_history[model_name]:
            # Inicializa com valores padrão baseados no tier do modelo
            model_info = self.available_models.get(model_name)
            default_success_rate = 0.9 if model_info and model_info.quality_tier == 1 else 0.8
            default_latency = 2000.0 if model_info and model_info.quality_tier == 1 else 3000.0
            
            self.performance_history[model_name][category] = ModelPerformance(
                model_name=model_name,
                category=category,
                success_rate=default_success_rate,
                avg_latency_ms=default_latency
            )
        
        return self.performance_history[model_name][category]
    
    def update_model_performance(self, 
                               model_name: str,
                               category: TaskCategory,
                               success: bool,
                               latency_ms: float,
                               cost: float = 0.0):
        """Atualiza métricas de performance de um modelo"""
        
        perf = self._get_performance(model_name, category)
        perf.update_metrics(success, latency_ms, cost)
        
        logger.debug(f"Model performance updated for model: {model_name}, category: {category.value}, success: {success}, new_success_rate: {round(perf.success_rate, 3)}")
    
    def get_fallback_model(self, 
                           failed_model_name: str, 
                           category: TaskCategory) -> Optional[ModelInfo]:
        """
        Obtém o próximo modelo de fallback disponível de uma cadeia pré-definida.
        
        Args:
            failed_model_name: O nome do modelo que falhou.
            category: A categoria da tarefa para a qual encontrar um fallback.
            
        Returns:
            Um objeto ModelInfo do próximo modelo disponível ou None se nenhum for encontrado.
        """
        fallback_list = self.fallback_chain.get(category, [])
        
        try:
            # Encontra o índice do modelo que falhou na lista de fallback
            failed_index = fallback_list.index(failed_model_name)
        except ValueError:
            # Se o modelo que falhou não está na lista, começa do início
            failed_index = -1

        # Itera na lista de fallback a partir da posição seguinte ao modelo que falhou
        for i in range(failed_index + 1, len(fallback_list)):
            fallback_name = fallback_list[i]
            fallback_info = self.available_models.get(fallback_name)
            
            # Verifica se o modelo de fallback existe e está disponível
            if fallback_info and fallback_info.is_available:
                logger.info(f"Fallback model found for category '{category.value}'. Failed model: '{failed_model_name}'. New model: '{fallback_name}'.")
                return fallback_info
        
        logger.error(f"No available fallback model found in the chain for category '{category.value}' after '{failed_model_name}' failed.")
        return None
    
    def mark_model_unavailable(self, model_name: str):
        """Marca modelo como indisponível temporariamente"""
        if model_name in self.available_models:
            self.available_models[model_name].is_available = False
            logger.warning(f"Model marked as unavailable: {model_name}")
    
    def mark_model_available(self, model_name: str):
        """Marca modelo como disponível novamente"""
        if model_name in self.available_models:
            self.available_models[model_name].is_available = True
            logger.info(f"Model marked as available: {model_name}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de roteamento de modelos"""
        
        stats = {
            'total_models': len(self.available_models),
            'available_models': sum(1 for m in self.available_models.values() if m.is_available),
            'categories_covered': len(self.fallback_chain),
            'performance_data': {}
        }
        
        for model_name, categories in self.performance_history.items():
            model_stats = {}
            for category, perf in categories.items():
                model_stats[category.value] = {
                    'success_rate': round(perf.success_rate, 3),
                    'avg_latency_ms': round(perf.avg_latency_ms, 1),
                    'total_calls': perf.total_calls
                }
            stats['performance_data'][model_name] = model_stats
        
        return stats
