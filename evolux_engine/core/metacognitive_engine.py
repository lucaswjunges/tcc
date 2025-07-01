#!/usr/bin/env python3
"""
Sistema Metacognitivo para Evolux Engine
=======================================

Implementa metacognição verdadeira - o sistema "pensa sobre como pensa".
Reaproveitando e melhorando código dos commits anteriores.

Funcionalidades:
🧠 Auto-reflexão sobre processos cognitivos  
🔍 Meta-avaliação de estratégias de pensamento
🎯 Adaptação dinâmica de abordagens cognitivas
📚 Meta-aprendizado (aprender como aprender melhor)
🧩 Teoria da mente sobre si mesmo
⚡ Integração com Sistema A2A Inteligente
"""

import asyncio
import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import hashlib
from pathlib import Path

from evolux_engine.schemas.contracts import Task, TaskType, ExecutionResult, ValidationResult
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("metacognitive_engine")


class MetaCognitiveState(Enum):
    """Estados metacognitivos do sistema"""
    SELF_ANALYZING = "self_analyzing"      # Analisando próprios processos
    STRATEGY_REFLECTING = "strategy_reflecting"  # Refletindo sobre estratégias
    CAPABILITY_EVALUATING = "capability_evaluating"  # Avaliando capacidades
    PROCESS_OPTIMIZING = "process_optimizing"  # Otimizando processos
    META_LEARNING = "meta_learning"        # Aprendendo sobre aprendizado


class ThinkingStrategy(Enum):
    """Estratégias de pensamento disponíveis"""
    ANALYTICAL = "analytical"             # Análise lógica sequencial
    CREATIVE = "creative"                 # Pensamento divergente
    SYSTEMATIC = "systematic"             # Abordagem sistemática
    INTUITIVE = "intuitive"              # Insights baseados em padrões
    COLLABORATIVE = "collaborative"       # Pensamento distribuído (A2A)
    REFLECTIVE = "reflective"            # Auto-reflexão


class CognitiveLimit(Enum):
    """Tipos de limitações cognitivas identificadas"""
    WORKING_MEMORY = "working_memory"     # Limitações de memória de trabalho
    CONTEXT_SWITCHING = "context_switching"  # Dificuldade em trocar contexto
    PATTERN_RECOGNITION = "pattern_recognition"  # Limitações em reconhecimento
    STRATEGIC_PLANNING = "strategic_planning"  # Limitações no planejamento
    CREATIVE_THINKING = "creative_thinking"  # Limitações criativas


@dataclass
class MetaCognitiveInsight:
    """Insight metacognitivo sobre próprios processos"""
    insight_id: str
    timestamp: datetime
    insight_type: str  # "strategy_effectiveness", "cognitive_bias", "limitation_discovery"
    description: str
    evidence: Dict[str, Any]
    confidence: float
    impact_assessment: Dict[str, float]
    actionable_changes: List[str]


@dataclass
class ThinkingProcessAnalysis:
    """Análise de um processo de pensamento"""
    process_id: str
    strategy_used: ThinkingStrategy
    context: Dict[str, Any]
    steps_taken: List[Dict[str, Any]]
    effectiveness_score: float
    efficiency_score: float
    identified_issues: List[str]
    improvement_suggestions: List[str]
    meta_reflection: str


@dataclass
class CognitiveCapabilityProfile:
    """Perfil de capacidades cognitivas do sistema"""
    analytical_strength: float = 0.0
    creative_strength: float = 0.0
    pattern_recognition: float = 0.0
    strategic_planning: float = 0.0
    collaborative_ability: float = 0.0
    meta_awareness: float = 0.0
    identified_limits: Set[CognitiveLimit] = field(default_factory=set)
    strength_areas: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)


class MetaCognitiveEngine:
    """
    Motor Metacognitivo - Sistema que "pensa sobre como pensa"
    """
    
    def __init__(self):
        self.state = MetaCognitiveState.SELF_ANALYZING
        self.thinking_history: deque = deque(maxlen=1000)
        self.insights: List[MetaCognitiveInsight] = []
        self.cognitive_profile = CognitiveCapabilityProfile()
        self.strategy_effectiveness: Dict[ThinkingStrategy, float] = {}
        self.meta_learning_data: Dict[str, Any] = {}
        self.process_analyses: List[ThinkingProcessAnalysis] = []
        
        # Integração com A2A
        self.a2a_metacognition: Dict[str, Any] = {}
        self.collaborative_thinking_patterns: Dict[str, Any] = {}
        
        logger.info("🧠 MetaCognitiveEngine inicializado - Auto-reflexão ativada")
    
    async def reflect_on_thinking_process(self, process_context: Dict[str, Any]) -> ThinkingProcessAnalysis:
        """
        Reflexão sobre um processo de pensamento específico
        CORE DA METACOGNIÇÃO: O sistema analisa como pensou
        """
        logger.info("🤔 Iniciando reflexão sobre processo de pensamento")
        
        analysis = ThinkingProcessAnalysis(
            process_id=self._generate_process_id(),
            strategy_used=ThinkingStrategy(process_context.get("strategy", "analytical")),
            context=process_context,
            steps_taken=process_context.get("steps", []),
            effectiveness_score=0.0,
            efficiency_score=0.0,
            identified_issues=[],
            improvement_suggestions=[],
            meta_reflection=""
        )
        
        # Analisar efetividade da estratégia usada
        analysis.effectiveness_score = await self._evaluate_strategy_effectiveness(
            analysis.strategy_used, process_context
        )
        
        # Analisar eficiência do processo
        analysis.efficiency_score = await self._evaluate_process_efficiency(process_context)
        
        # Identificar problemas no próprio pensamento
        analysis.identified_issues = await self._identify_thinking_issues(process_context)
        
        # Gerar sugestões de melhoria
        analysis.improvement_suggestions = await self._generate_improvement_suggestions(analysis)
        
        # Meta-reflexão: reflexão sobre a reflexão
        analysis.meta_reflection = await self._generate_meta_reflection(analysis)
        
        self.process_analyses.append(analysis)
        
        logger.info(f"✅ Reflexão concluída - Efetividade: {analysis.effectiveness_score:.2f}")
        return analysis
    
    async def evaluate_own_capabilities(self) -> CognitiveCapabilityProfile:
        """
        Auto-avaliação das próprias capacidades cognitivas
        METACOGNIÇÃO: Conhecer as próprias limitações e forças
        """
        logger.info("🔍 Iniciando auto-avaliação de capacidades cognitivas")
        
        # Analisar histórico de performance por área
        if self.thinking_history:
            analytical_scores = []
            creative_scores = []
            pattern_scores = []
            strategic_scores = []
            
            for entry in self.thinking_history:
                if entry.get("type") == "analytical":
                    analytical_scores.append(entry.get("effectiveness", 0.5))
                elif entry.get("type") == "creative":
                    creative_scores.append(entry.get("effectiveness", 0.5))
                # ... mais tipos
            
            # Atualizar perfil baseado em dados históricos
            if analytical_scores:
                self.cognitive_profile.analytical_strength = np.mean(analytical_scores)
            if creative_scores:
                self.cognitive_profile.creative_strength = np.mean(creative_scores)
        
        # Identificar limitações através de análise de falhas
        await self._identify_cognitive_limitations()
        
        # Identificar áreas de força
        await self._identify_strength_areas()
        
        # Auto-consciência metacognitiva
        self.cognitive_profile.meta_awareness = await self._calculate_meta_awareness()
        
        logger.info(f"📊 Auto-avaliação concluída - Meta-awareness: {self.cognitive_profile.meta_awareness:.2f}")
        return self.cognitive_profile
    
    async def adapt_thinking_strategy(self, current_context: Dict[str, Any]) -> ThinkingStrategy:
        """
        Adapta estratégia de pensamento baseada em auto-reflexão
        METACOGNIÇÃO: Escolher como pensar baseado em como pensou antes
        """
        logger.info("🎯 Adaptando estratégia de pensamento baseada em auto-reflexão")
        
        # Analisar contexto atual
        problem_type = current_context.get("problem_type", "general")
        complexity = current_context.get("complexity", "medium")
        available_resources = current_context.get("resources", {})
        
        # Consultar histórico de efetividade por estratégia
        best_strategy = ThinkingStrategy.ANALYTICAL  # default
        best_score = 0.0
        
        for strategy, effectiveness in self.strategy_effectiveness.items():
            # Verificar se estratégia é adequada para o contexto
            if await self._is_strategy_suitable(strategy, current_context):
                if effectiveness > best_score:
                    best_score = effectiveness
                    best_strategy = strategy
        
        # Se temos agentes A2A disponíveis, considerar pensamento colaborativo
        if available_resources.get("a2a_agents", 0) >= 2:
            if self.strategy_effectiveness.get(ThinkingStrategy.COLLABORATIVE, 0) > best_score:
                best_strategy = ThinkingStrategy.COLLABORATIVE
        
        # Meta-decisão: questionar a própria escolha
        meta_confidence = await self._evaluate_strategy_choice_confidence(best_strategy, current_context)
        
        if meta_confidence < 0.7:
            # Baixa confiança na escolha - usar estratégia reflexiva
            best_strategy = ThinkingStrategy.REFLECTIVE
            logger.info("🤔 Baixa confiança na estratégia - usando abordagem reflexiva")
        
        logger.info(f"🎯 Estratégia selecionada: {best_strategy.value} (confiança: {meta_confidence:.2f})")
        return best_strategy
    
    async def meta_learn_from_experience(self, experience: Dict[str, Any]) -> MetaCognitiveInsight:
        """
        Meta-aprendizado: Aprender sobre como aprender melhor
        METACOGNIÇÃO: Otimizar próprios processos de aprendizado
        """
        logger.info("📚 Iniciando meta-aprendizado sobre experiência")
        
        # Extrair padrões sobre como o aprendizado ocorreu
        learning_pattern = await self._extract_learning_patterns(experience)
        
        # Identificar o que funcionou/não funcionou no processo de aprendizado
        learning_effectiveness = await self._evaluate_learning_effectiveness(experience)
        
        # Gerar insight metacognitivo
        insight = MetaCognitiveInsight(
            insight_id=self._generate_insight_id(),
            timestamp=datetime.utcnow(),
            insight_type="meta_learning",
            description=f"Aprendizado sobre processo de aprendizado: {learning_pattern['description']}",
            evidence=learning_pattern,
            confidence=learning_effectiveness,
            impact_assessment={"learning_efficiency": learning_effectiveness},
            actionable_changes=learning_pattern.get("improvements", [])
        )
        
        self.insights.append(insight)
        
        # Atualizar estratégias de aprendizado baseado no insight
        await self._update_learning_strategies(insight)
        
        logger.info(f"🧠 Meta-aprendizado concluído - Insight: {insight.description}")
        return insight
    
    async def integrate_with_a2a_system(self, a2a_system) -> Dict[str, Any]:
        """
        Integração metacognitiva com Sistema A2A
        METACOGNIÇÃO COLABORATIVA: Reflexão sobre colaboração entre agentes
        """
        logger.info("🤝 Integrando metacognição com Sistema A2A")
        
        # Analisar padrões de colaboração
        collaboration_patterns = await self._analyze_a2a_collaboration_patterns(a2a_system)
        
        # Reflexão sobre efetividade da colaboração
        collaboration_effectiveness = await self._evaluate_collaboration_thinking(a2a_system)
        
        # Meta-insights sobre pensamento distribuído
        distributed_thinking_insights = await self._generate_distributed_thinking_insights(
            collaboration_patterns, collaboration_effectiveness
        )
        
        # Otimizar estratégias de colaboração cognitiva
        optimized_strategies = await self._optimize_collaborative_thinking(distributed_thinking_insights)
        
        integration_result = {
            "collaboration_patterns": collaboration_patterns,
            "effectiveness_score": collaboration_effectiveness,
            "meta_insights": distributed_thinking_insights,
            "optimized_strategies": optimized_strategies,
            "integration_timestamp": datetime.utcnow().isoformat()
        }
        
        self.a2a_metacognition = integration_result
        
        logger.info(f"🧠 Integração A2A concluída - Efetividade: {collaboration_effectiveness:.2f}")
        return integration_result
    
    async def generate_self_model(self) -> Dict[str, Any]:
        """
        Gera um modelo interno de como o sistema funciona
        METACOGNIÇÃO: Auto-consciência estrutural
        """
        logger.info("🧩 Gerando modelo interno de auto-consciência")
        
        self_model = {
            "cognitive_architecture": {
                "thinking_strategies": [s.value for s in ThinkingStrategy],
                "current_state": self.state.value,
                "processing_capacity": await self._assess_processing_capacity(),
                "meta_awareness_level": self.cognitive_profile.meta_awareness
            },
            "operational_patterns": {
                "preferred_strategies": await self._identify_preferred_strategies(),
                "common_failure_modes": await self._identify_failure_modes(),
                "adaptation_speed": await self._calculate_adaptation_speed(),
                "learning_velocity": await self._calculate_learning_velocity()
            },
            "limitations": {
                "identified_limits": [limit.value for limit in self.cognitive_profile.identified_limits],
                "performance_boundaries": await self._map_performance_boundaries(),
                "resource_constraints": await self._identify_resource_constraints()
            },
            "strengths": {
                "capability_scores": {
                    "analytical": self.cognitive_profile.analytical_strength,
                    "creative": self.cognitive_profile.creative_strength,
                    "collaborative": self.cognitive_profile.collaborative_ability
                },
                "expertise_areas": self.cognitive_profile.strength_areas
            },
            "meta_knowledge": {
                "self_understanding_depth": await self._calculate_self_understanding(),
                "bias_awareness": await self._assess_bias_awareness(),
                "uncertainty_handling": await self._evaluate_uncertainty_handling()
            }
        }
        
        logger.info("🧩 Modelo de auto-consciência gerado")
        return self_model
    
    async def question_own_assumptions(self, context: Dict[str, Any]) -> List[str]:
        """
        Questiona as próprias suposições e vieses
        METACOGNIÇÃO: Auto-crítica construtiva
        """
        logger.info("❓ Questionando próprias suposições")
        
        questions = []
        
        # Questionar suposições sobre o problema
        if "problem_definition" in context:
            questions.extend([
                "Estou definindo o problema corretamente?",
                "Há aspectos do problema que estou ignorando?",
                "Minhas suposições sobre o problema são válidas?"
            ])
        
        # Questionar estratégia escolhida
        if "chosen_strategy" in context:
            questions.extend([
                "Por que escolhi esta estratégia específica?",
                "Existe uma abordagem melhor que não considerei?",
                "Estou sendo influenciado por sucessos/falhas passados?"
            ])
        
        # Questionar próprios vieses
        questions.extend([
            "Que vieses cognitivos podem estar afetando meu julgamento?",
            "Estou sendo overconfident ou underconfident?",
            "Há informações contraditórias que estou ignorando?"
        ])
        
        # Auto-questionar sobre metacognição
        questions.extend([
            "Estou sendo suficientemente reflexivo?",
            "Minha análise metacognitiva é profunda o suficiente?",
            "Estou questionando minhas próprias questões?"
        ])
        
        logger.info(f"❓ Geradas {len(questions)} questões auto-reflexivas")
        return questions
    
    # ============================================================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ============================================================================
    
    async def _evaluate_strategy_effectiveness(self, strategy: ThinkingStrategy, context: Dict[str, Any]) -> float:
        """Avalia efetividade de uma estratégia específica"""
        # Simular análise baseada em contexto e histórico
        base_score = self.strategy_effectiveness.get(strategy, 0.5)
        
        # Ajustar baseado no contexto
        if strategy == ThinkingStrategy.ANALYTICAL and context.get("complexity") == "high":
            base_score += 0.2
        elif strategy == ThinkingStrategy.CREATIVE and context.get("problem_type") == "novel":
            base_score += 0.3
        elif strategy == ThinkingStrategy.COLLABORATIVE and context.get("agents_available", 0) > 2:
            base_score += 0.25
        
        return min(1.0, max(0.0, base_score))
    
    async def _evaluate_process_efficiency(self, context: Dict[str, Any]) -> float:
        """Avalia eficiência de um processo"""
        time_taken = context.get("execution_time", 1.0)
        complexity = context.get("complexity", "medium")
        
        # Eficiência baseada em tempo vs complexidade
        expected_time = {"low": 0.5, "medium": 1.0, "high": 2.0}.get(complexity, 1.0)
        efficiency = expected_time / max(time_taken, 0.1)
        
        return min(1.0, efficiency)
    
    async def _identify_thinking_issues(self, context: Dict[str, Any]) -> List[str]:
        """Identifica problemas no processo de pensamento"""
        issues = []
        
        if context.get("iterations", 1) > 3:
            issues.append("Muitas iterações - possível lack of planning")
        
        if context.get("confidence", 1.0) < 0.5:
            issues.append("Baixa confiança - necessária mais validação")
        
        if context.get("context_switches", 0) > 5:
            issues.append("Muitas mudanças de contexto - possível falta de foco")
        
        return issues
    
    async def _generate_improvement_suggestions(self, analysis: ThinkingProcessAnalysis) -> List[str]:
        """Gera sugestões de melhoria baseadas na análise"""
        suggestions = []
        
        if analysis.effectiveness_score < 0.6:
            suggestions.append("Considerar estratégia alternativa de pensamento")
        
        if analysis.efficiency_score < 0.5:
            suggestions.append("Otimizar processo para reduzir tempo de execução")
        
        if "lack of planning" in analysis.identified_issues:
            suggestions.append("Investir mais tempo em planejamento inicial")
        
        return suggestions
    
    async def _generate_meta_reflection(self, analysis: ThinkingProcessAnalysis) -> str:
        """Gera meta-reflexão sobre a análise"""
        return f"Reflexão sobre {analysis.strategy_used.value}: " \
               f"Efetividade {analysis.effectiveness_score:.2f}, " \
               f"principais learnings: {', '.join(analysis.improvement_suggestions[:2])}"
    
    def _generate_process_id(self) -> str:
        """Gera ID único para processo"""
        return f"proc_{int(time.time())}_{hash(str(datetime.utcnow())) % 10000}"
    
    def _generate_insight_id(self) -> str:
        """Gera ID único para insight"""
        return f"insight_{int(time.time())}_{hash(str(datetime.utcnow())) % 10000}"
    
    async def _identify_cognitive_limitations(self):
        """Identifica limitações cognitivas através de análise de falhas"""
        # Analisar padrões de falha para identificar limitações
        failure_patterns = await self._analyze_failure_patterns()
        
        if failure_patterns.get("working_memory_overload", 0) > 0.3:
            self.cognitive_profile.identified_limits.add(CognitiveLimit.WORKING_MEMORY)
        
        if failure_patterns.get("context_confusion", 0) > 0.3:
            self.cognitive_profile.identified_limits.add(CognitiveLimit.CONTEXT_SWITCHING)
    
    async def _analyze_failure_patterns(self) -> Dict[str, float]:
        """Analisa padrões de falha"""
        # Simulação - em implementação real, analisaria histórico de falhas
        return {
            "working_memory_overload": 0.2,
            "context_confusion": 0.1,
            "pattern_miss": 0.15
        }
    
    async def _identify_strength_areas(self):
        """Identifica áreas de força cognitiva"""
        if self.cognitive_profile.analytical_strength > 0.8:
            self.cognitive_profile.strength_areas.append("analytical_reasoning")
        
        if self.cognitive_profile.collaborative_ability > 0.8:
            self.cognitive_profile.strength_areas.append("distributed_cognition")
    
    async def _calculate_meta_awareness(self) -> float:
        """Calcula nível de auto-consciência metacognitiva"""
        # Baseado em número de insights e qualidade de auto-reflexão
        insights_count = len(self.insights)
        reflection_depth = len(self.process_analyses)
        
        base_awareness = min(1.0, (insights_count * 0.1) + (reflection_depth * 0.05))
        return base_awareness
    
    async def _is_strategy_suitable(self, strategy: ThinkingStrategy, context: Dict[str, Any]) -> bool:
        """Verifica se estratégia é adequada para o contexto"""
        problem_type = context.get("problem_type", "general")
        
        if strategy == ThinkingStrategy.CREATIVE and problem_type in ["novel", "innovative"]:
            return True
        elif strategy == ThinkingStrategy.ANALYTICAL and problem_type in ["logical", "mathematical"]:
            return True
        elif strategy == ThinkingStrategy.COLLABORATIVE and context.get("agents_available", 0) >= 2:
            return True
        
        return True  # Estratégias gerais são sempre adequadas
    
    async def _evaluate_strategy_choice_confidence(self, strategy: ThinkingStrategy, context: Dict[str, Any]) -> float:
        """Avalia confiança na escolha de estratégia"""
        # Baseado em histórico de sucesso da estratégia no contexto similar
        historical_success = self.strategy_effectiveness.get(strategy, 0.5)
        context_fit = 0.8 if await self._is_strategy_suitable(strategy, context) else 0.3
        
        return (historical_success + context_fit) / 2
    
    async def _extract_learning_patterns(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai padrões de como o aprendizado ocorreu"""
        return {
            "description": "Padrão de aprendizado identificado",
            "learning_speed": experience.get("learning_speed", 1.0),
            "retention_rate": experience.get("retention", 0.8),
            "improvements": ["Melhor estruturação de informação", "Mais iterações reflexivas"]
        }
    
    async def _evaluate_learning_effectiveness(self, experience: Dict[str, Any]) -> float:
        """Avalia efetividade do processo de aprendizado"""
        return experience.get("learning_effectiveness", 0.7)
    
    async def _update_learning_strategies(self, insight: MetaCognitiveInsight):
        """Atualiza estratégias de aprendizado baseado em insight"""
        for change in insight.actionable_changes:
            # Implementar mudanças nas estratégias
            logger.info(f"📚 Implementando mudança: {change}")
    
    async def _analyze_a2a_collaboration_patterns(self, a2a_system) -> Dict[str, Any]:
        """Analisa padrões de colaboração A2A"""
        return {
            "collaboration_frequency": 0.8,
            "information_sharing_quality": 0.9,
            "distributed_decision_making": 0.7
        }
    
    async def _evaluate_collaboration_thinking(self, a2a_system) -> float:
        """Avalia efetividade do pensamento colaborativo"""
        return 0.85
    
    async def _generate_distributed_thinking_insights(self, patterns: Dict, effectiveness: float) -> List[str]:
        """Gera insights sobre pensamento distribuído"""
        return [
            "Colaboração A2A melhora qualidade de decisões complexas",
            "Distribuição de carga cognitiva aumenta eficiência",
            "Necessário melhor sincronização entre agentes"
        ]
    
    async def _optimize_collaborative_thinking(self, insights: List[str]) -> Dict[str, Any]:
        """Otimiza estratégias de pensamento colaborativo"""
        return {
            "improved_sync_mechanisms": True,
            "better_load_distribution": True,
            "enhanced_communication": True
        }
    
    async def _assess_processing_capacity(self) -> float:
        """Avalia capacidade de processamento atual"""
        return 0.75
    
    async def _identify_preferred_strategies(self) -> List[str]:
        """Identifica estratégias preferenciais"""
        return ["analytical", "collaborative"]
    
    async def _identify_failure_modes(self) -> List[str]:
        """Identifica modos comuns de falha"""
        return ["overconfidence", "context_loss", "insufficient_reflection"]
    
    async def _calculate_adaptation_speed(self) -> float:
        """Calcula velocidade de adaptação"""
        return 0.8
    
    async def _calculate_learning_velocity(self) -> float:
        """Calcula velocidade de aprendizado"""
        return 0.7
    
    async def _map_performance_boundaries(self) -> Dict[str, float]:
        """Mapeia limites de performance"""
        return {
            "max_concurrent_tasks": 10.0,
            "max_complexity_level": 8.0,
            "optimal_context_size": 5.0
        }
    
    async def _identify_resource_constraints(self) -> List[str]:
        """Identifica restrições de recursos"""
        return ["memory_capacity", "processing_time", "context_window"]
    
    async def _calculate_self_understanding(self) -> float:
        """Calcula profundidade de auto-compreensão"""
        return 0.6
    
    async def _assess_bias_awareness(self) -> float:
        """Avalia consciência de vieses próprios"""
        return 0.7
    
    async def _evaluate_uncertainty_handling(self) -> float:
        """Avalia capacidade de lidar com incerteza"""
        return 0.65


# Singleton para metacognição global
_metacognitive_engine = None

def get_metacognitive_engine() -> MetaCognitiveEngine:
    """Obtém instância singleton do motor metacognitivo"""
    global _metacognitive_engine
    if _metacognitive_engine is None:
        _metacognitive_engine = MetaCognitiveEngine()
    return _metacognitive_engine