"""
EVOLUX: Autonomous Multi-Agent System with Resource-Constrained Optimization

This module implements a state-of-the-art Multi-Agent System (MAS) that operates 
under strict computational resource constraints, treating tokens as a finite 
commodity subject to economic principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import asyncio
import uuid
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, deque
import math

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import LLMProvider, Task, TaskType, TaskStatus, ExecutionResult
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.core.evolux_a2a_integration import A2ACapableMixin

logger = get_structured_logger("resource_aware_agent")


class ModelTier(Enum):
    """Economic model tiers with cost optimization"""
    ECONOMY = ("haiku", 0.25, 0.5, 1.0)      # (model_name, cost_per_1k_input, cost_per_1k_output, performance_factor)
    BALANCED = ("sonnet", 3.0, 15.0, 1.5)    
    PREMIUM = ("opus", 15.0, 75.0, 2.0)      
    ULTRA = ("gpt-4", 30.0, 60.0, 2.5)        

    def __init__(self, model_name: str, input_cost: float, output_cost: float, performance_factor: float):
        self.model_name = model_name
        self.input_cost = input_cost
        self.output_cost = output_cost
        self.performance_factor = performance_factor

    @property
    def total_cost_per_1k(self) -> float:
        """Average cost per 1k tokens assuming 60/40 input/output ratio"""
        return (self.input_cost * 0.6) + (self.output_cost * 0.4)


@dataclass
class TokenAllocation:
    """Token allocation management with economic tracking"""
    initial_budget: int
    consumed: int = 0
    reserved: int = 0
    model_tier: ModelTier = ModelTier.BALANCED
    allocation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def available(self) -> int:
        return max(0, self.initial_budget - self.consumed - self.reserved)
    
    @property
    def utilization_rate(self) -> float:
        return self.consumed / self.initial_budget if self.initial_budget > 0 else 0.0
    
    @property
    def efficiency_score(self) -> float:
        """Compute efficiency as value delivered per token consumed"""
        if self.consumed == 0:
            return 1.0
        
        total_value = sum(entry.get('value_generated', 0) for entry in self.allocation_history)
        return total_value / self.consumed if self.consumed > 0 else 0.0
    
    def allocate_tokens(self, amount: int, purpose: str, expected_value: float = 0.0) -> bool:
        """Allocate tokens for a specific purpose with value tracking"""
        if amount > self.available:
            return False
        
        self.consumed += amount
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'amount': amount,
            'purpose': purpose,
            'expected_value': expected_value,
            'value_generated': 0.0,  # To be updated later
            'model_tier': self.model_tier.name
        })
        return True
    
    def update_value_generated(self, allocation_index: int, actual_value: float):
        """Update the actual value generated for a specific allocation"""
        if 0 <= allocation_index < len(self.allocation_history):
            self.allocation_history[allocation_index]['value_generated'] = actual_value


@dataclass
class AgentPerformanceMetrics:
    """Performance tracking for resource optimization"""
    total_tasks_completed: int = 0
    success_rate: float = 1.0
    avg_tokens_per_task: float = 0.0
    avg_value_per_token: float = 0.0
    collaboration_efficiency: float = 1.0
    meta_cognitive_accuracy: float = 1.0
    
    def update_metrics(self, task_success: bool, tokens_used: int, value_generated: float):
        """Update performance metrics with exponential smoothing"""
        alpha = 0.1  # Smoothing factor
        
        self.total_tasks_completed += 1
        
        # Update success rate
        new_success = 1.0 if task_success else 0.0
        self.success_rate = alpha * new_success + (1 - alpha) * self.success_rate
        
        # Update token efficiency
        self.avg_tokens_per_task = alpha * tokens_used + (1 - alpha) * self.avg_tokens_per_task
        
        # Update value efficiency
        if tokens_used > 0:
            value_per_token = value_generated / tokens_used
            self.avg_value_per_token = alpha * value_per_token + (1 - alpha) * self.avg_value_per_token


class CollaborationProtocol:
    """Inter-agent communication protocol with token negotiation"""
    
    @dataclass
    class CollaborationRequest:
        source_agent_id: str
        target_agent_id: str
        request_id: str
        query: str
        offered_tokens: int
        priority: float
        context_embedding: Dict[str, Any]
        timeout_seconds: int = 30
        requires_response: bool = True
        
    @dataclass
    class CollaborationResponse:
        request_id: str
        accepted: bool
        response_data: Optional[Dict[str, Any]] = None
        tokens_consumed: int = 0
        confidence_score: float = 0.0
        
    def __init__(self):
        self.pending_requests: Dict[str, CollaborationProtocol.CollaborationRequest] = {}
        self.collaboration_history: List[Dict[str, Any]] = []
        
    async def initiate_collaboration(
        self, 
        source_agent: 'ResourceAwareAgent',
        target_agent_id: str,
        query: str,
        max_tokens: int,
        priority: float = 0.5
    ) -> Optional[CollaborationResponse]:
        """Initiate collaboration with token negotiation"""
        
        request_id = str(uuid.uuid4())
        request = self.CollaborationRequest(
            source_agent_id=source_agent.agent_id,
            target_agent_id=target_agent_id,
            request_id=request_id,
            query=query,
            offered_tokens=max_tokens,
            priority=priority,
            context_embedding=source_agent._generate_minimal_context_embedding()
        )
        
        self.pending_requests[request_id] = request
        
        # In a real implementation, this would route to the target agent
        # For now, we'll simulate the protocol
        logger.info(f"Collaboration initiated: {source_agent.agent_id} -> {target_agent_id}")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Offered tokens: {max_tokens}")
        
        # Simulate response (in real implementation, this would be handled by message routing)
        response = self.CollaborationResponse(
            request_id=request_id,
            accepted=True,
            response_data={"simulated": True, "query": query},
            tokens_consumed=min(max_tokens, max_tokens // 2),
            confidence_score=0.8
        )
        
        self._record_collaboration(request, response)
        return response
    
    def _record_collaboration(self, request: CollaborationRequest, response: CollaborationResponse):
        """Record collaboration for analysis and optimization"""
        self.collaboration_history.append({
            'timestamp': datetime.now(),
            'source_agent': request.source_agent_id,
            'target_agent': request.target_agent_id,
            'tokens_offered': request.offered_tokens,
            'tokens_consumed': response.tokens_consumed,
            'accepted': response.accepted,
            'priority': request.priority,
            'confidence': response.confidence_score
        })


class ResourceAwareAgent(ABC, A2ACapableMixin):
    """
    Base class implementing resource-constrained decision making with 
    meta-cognitive capabilities and inter-agent communication protocols.
    """
    
    def __init__(
        self, 
        agent_id: str,
        role: str,
        initial_token_budget: int,
        model_tier: ModelTier = ModelTier.BALANCED,
        meta_cognitive_threshold: float = 0.7,
        risk_tolerance: float = 0.5,
        collaboration_propensity: float = 0.6
    ):
        super().__init__()
        self.agent_id = agent_id
        self.role = role
        self.allocation = TokenAllocation(
            initial_budget=initial_token_budget,
            model_tier=model_tier
        )
        self.meta_cognitive_threshold = meta_cognitive_threshold
        self.risk_tolerance = risk_tolerance
        self.collaboration_propensity = collaboration_propensity
        
        self.execution_history: List[Dict[str, Any]] = []
        self.performance_metrics = AgentPerformanceMetrics()
        self.collaboration_protocol = CollaborationProtocol()
        
        # Value function components
        self.value_function = self._initialize_value_function()
        self.bayesian_prior = self._initialize_bayesian_prior()
        
        # Learning and adaptation
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        self.strategy_weights = defaultdict(float)
        
        logger.info(f"Initialized ResourceAwareAgent: {agent_id} with {initial_token_budget} tokens")
    
    def _initialize_value_function(self) -> Callable[[str, Dict[str, Any]], float]:
        """Initialize value function for utility computation"""
        def value_function(action: str, context: Dict[str, Any]) -> float:
            # Base value from action type
            action_values = {
                'create_file': 2.0,
                'modify_file': 1.5,
                'execute_command': 1.0,
                'validate_artifact': 1.2,
                'collaborate': 1.8,
                'meta_reflect': 0.8
            }
            
            base_value = action_values.get(action.lower(), 1.0)
            
            # Context modifiers
            complexity_modifier = context.get('complexity', 1.0)
            urgency_modifier = context.get('urgency', 1.0)
            strategic_importance = context.get('strategic_importance', 1.0)
            
            return base_value * complexity_modifier * urgency_modifier * strategic_importance
        
        return value_function
    
    def _initialize_bayesian_prior(self) -> Dict[str, float]:
        """Initialize Bayesian priors for success probability estimation"""
        return {
            'base_success_rate': 0.8,
            'complexity_impact': 0.1,
            'resource_constraint_impact': 0.15,
            'collaboration_benefit': 0.2
        }
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method with resource tracking"""
        pass
    
    def compute_expected_utility(self, action: str, token_cost: int, context: Dict[str, Any] = None) -> float:
        """
        Compute expected utility using Bayesian decision theory:
        U(a) = Σ P(s|a) * V(s) - C(a)
        """
        if context is None:
            context = {}
        
        # Estimate success probability
        success_probability = self._estimate_success_probability(action, context)
        
        # Estimate value of successful outcome
        expected_value = self.value_function(action, context)
        
        # Normalize cost relative to budget
        normalized_cost = token_cost / self.allocation.initial_budget if self.allocation.initial_budget > 0 else 1.0
        
        # Apply risk adjustment
        risk_adjustment = 1.0 - (self.risk_tolerance * 0.2)  # Conservative adjustment
        
        utility = (success_probability * expected_value * risk_adjustment) - normalized_cost
        
        logger.debug(f"Utility computation for {action}: P(success)={success_probability:.3f}, "
                    f"Value={expected_value:.3f}, Cost={normalized_cost:.3f}, Utility={utility:.3f}")
        
        return utility
    
    def _estimate_success_probability(self, action: str, context: Dict[str, Any]) -> float:
        """Estimate probability of success using Bayesian inference"""
        
        # Base probability from Bayesian prior
        base_prob = self.bayesian_prior['base_success_rate']
        
        # Adjust for complexity
        complexity = context.get('complexity', 1.0)
        complexity_adjustment = -self.bayesian_prior['complexity_impact'] * (complexity - 1.0)
        
        # Adjust for resource constraints
        resource_ratio = self.allocation.available / self.allocation.initial_budget
        resource_adjustment = -self.bayesian_prior['resource_constraint_impact'] * (1.0 - resource_ratio)
        
        # Historical performance adjustment
        performance_adjustment = (self.performance_metrics.success_rate - 0.5) * 0.3
        
        # Model tier performance adjustment
        model_adjustment = (self.allocation.model_tier.performance_factor - 1.0) * 0.1
        
        probability = base_prob + complexity_adjustment + resource_adjustment + performance_adjustment + model_adjustment
        
        # Ensure probability is in valid range
        return max(0.1, min(0.95, probability))
    
    async def request_inter_agent_collaboration(
        self, 
        target_agent_id: str, 
        query: str, 
        max_tokens: int,
        priority: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Initiate synchronous inter-agent communication with 
        token negotiation and context transfer.
        """
        
        # Check if we have enough tokens
        if max_tokens > self.allocation.available:
            logger.warning(f"Insufficient tokens for collaboration: need {max_tokens}, have {self.allocation.available}")
            return None
        
        # Compute utility of collaboration
        collaboration_context = {
            'complexity': len(query) / 1000,  # Simple complexity heuristic
            'urgency': priority,
            'strategic_importance': 1.2  # Collaboration often has strategic value
        }
        
        utility = self.compute_expected_utility('collaborate', max_tokens, collaboration_context)
        
        # Proceed only if utility is positive and above threshold
        if utility < 0.1:
            logger.info(f"Collaboration utility too low: {utility:.3f}")
            return None
        
        # Reserve tokens for collaboration
        if not self.allocation.allocate_tokens(max_tokens, f"collaboration_with_{target_agent_id}", utility):
            logger.error("Failed to allocate tokens for collaboration")
            return None
        
        try:
            response = await self.collaboration_protocol.initiate_collaboration(
                self, target_agent_id, query, max_tokens, priority
            )
            
            if response and response.accepted:
                # Update metrics
                actual_tokens_used = response.tokens_consumed
                value_generated = response.confidence_score * 2.0  # Convert confidence to value
                
                self.performance_metrics.update_metrics(True, actual_tokens_used, value_generated)
                
                # Update allocation history
                if self.allocation.allocation_history:
                    last_allocation_idx = len(self.allocation.allocation_history) - 1
                    self.allocation.update_value_generated(last_allocation_idx, value_generated)
                
                logger.info(f"Successful collaboration with {target_agent_id}: "
                           f"{actual_tokens_used} tokens, confidence {response.confidence_score:.3f}")
                
                return response.response_data
            else:
                logger.warning(f"Collaboration rejected by {target_agent_id}")
                return None
                
        except Exception as e:
            logger.error(f"Collaboration failed: {str(e)}")
            return None
    
    def _generate_minimal_context_embedding(self) -> Dict[str, Any]:
        """Generate minimal context for efficient transfer"""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'current_task_count': len(self.execution_history),
            'success_rate': self.performance_metrics.success_rate,
            'available_tokens': self.allocation.available,
            'model_tier': self.allocation.model_tier.name,
            'specializations': getattr(self, 'specializations', [])
        }
    
    def should_upgrade_model_tier(self, task_complexity: float, importance: float) -> bool:
        """Determine if model tier should be upgraded for better performance"""
        
        # Current tier performance estimate
        current_expected_success = self._estimate_success_probability('current_task', {
            'complexity': task_complexity
        })
        
        # Upgraded tier performance estimate (hypothetical)
        upgrade_benefit = 0.15 * (task_complexity - 1.0)  # More benefit for complex tasks
        upgraded_expected_success = min(0.95, current_expected_success + upgrade_benefit)
        
        # Cost-benefit analysis
        current_tier_cost = self.allocation.model_tier.total_cost_per_1k
        
        # Find next tier up
        tiers = list(ModelTier)
        current_tier_idx = tiers.index(self.allocation.model_tier)
        
        if current_tier_idx < len(tiers) - 1:
            next_tier = tiers[current_tier_idx + 1]
            upgrade_cost_ratio = next_tier.total_cost_per_1k / current_tier_cost
            
            # Expected value increase should justify cost increase
            value_increase_ratio = upgraded_expected_success / current_expected_success
            
            # Upgrade if value increase exceeds cost increase, weighted by importance
            should_upgrade = (value_increase_ratio * importance) > upgrade_cost_ratio
            
            logger.debug(f"Upgrade analysis: value_ratio={value_increase_ratio:.3f}, "
                        f"cost_ratio={upgrade_cost_ratio:.3f}, importance={importance:.3f}, "
                        f"upgrade={should_upgrade}")
            
            return should_upgrade
        
        return False
    
    def adapt_strategy_weights(self, task_outcome: Dict[str, Any]):
        """Adapt strategy weights based on task outcomes using reinforcement learning"""
        
        strategy_used = task_outcome.get('strategy', 'default')
        success = task_outcome.get('success', False)
        efficiency = task_outcome.get('efficiency', 0.5)
        
        # Reward signal combines success and efficiency
        reward = (1.0 if success else -0.5) + (efficiency - 0.5)
        
        # Update strategy weight using simple policy gradient
        self.strategy_weights[strategy_used] += self.learning_rate * reward
        
        # Decay other strategy weights slightly to maintain exploration
        for strategy in self.strategy_weights:
            if strategy != strategy_used:
                self.strategy_weights[strategy] *= 0.99
        
        logger.debug(f"Strategy weights updated: {dict(self.strategy_weights)}")
    
    async def meta_cognitive_reflection(self) -> Dict[str, Any]:
        """
        Perform meta-cognitive reflection on recent performance and adapt strategies
        """
        
        if len(self.execution_history) < 3:
            return {'reflection': 'insufficient_data', 'adaptations': []}
        
        recent_tasks = self.execution_history[-5:]  # Last 5 tasks
        
        # Analyze performance patterns
        success_pattern = [task.get('success', False) for task in recent_tasks]
        efficiency_pattern = [task.get('efficiency', 0.5) for task in recent_tasks]
        
        avg_success = np.mean(success_pattern)
        avg_efficiency = np.mean(efficiency_pattern)
        
        # Identify concerning trends
        adaptations = []
        
        if avg_success < 0.6:
            adaptations.append({
                'type': 'increase_caution',
                'reason': 'low_success_rate',
                'action': 'increase_meta_cognitive_threshold'
            })
            self.meta_cognitive_threshold = min(0.9, self.meta_cognitive_threshold + 0.1)
        
        if avg_efficiency < 0.4:
            adaptations.append({
                'type': 'optimize_resource_usage',
                'reason': 'low_efficiency',
                'action': 'increase_collaboration_propensity'
            })
            self.collaboration_propensity = min(0.9, self.collaboration_propensity + 0.1)
        
        if self.allocation.utilization_rate > 0.8:
            adaptations.append({
                'type': 'resource_conservation',
                'reason': 'high_utilization',
                'action': 'decrease_risk_tolerance'
            })
            self.risk_tolerance = max(0.1, self.risk_tolerance - 0.1)
        
        reflection_result = {
            'timestamp': datetime.now(),
            'avg_success_rate': avg_success,
            'avg_efficiency': avg_efficiency,
            'utilization_rate': self.allocation.utilization_rate,
            'adaptations': adaptations,
            'performance_trend': 'improving' if avg_success > self.performance_metrics.success_rate else 'declining'
        }
        
        logger.info(f"Meta-cognitive reflection completed: {len(adaptations)} adaptations made")
        
        return reflection_result
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get comprehensive resource status for monitoring"""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'tokens': {
                'initial_budget': self.allocation.initial_budget,
                'consumed': self.allocation.consumed,
                'available': self.allocation.available,
                'utilization_rate': self.allocation.utilization_rate,
                'efficiency_score': self.allocation.efficiency_score
            },
            'performance': {
                'total_tasks': self.performance_metrics.total_tasks_completed,
                'success_rate': self.performance_metrics.success_rate,
                'avg_tokens_per_task': self.performance_metrics.avg_tokens_per_task,
                'avg_value_per_token': self.performance_metrics.avg_value_per_token
            },
            'model_tier': self.allocation.model_tier.name,
            'meta_cognitive_threshold': self.meta_cognitive_threshold,
            'collaboration_propensity': self.collaboration_propensity,
            'risk_tolerance': self.risk_tolerance
        }