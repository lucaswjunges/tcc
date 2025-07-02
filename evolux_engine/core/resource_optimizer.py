"""
Resource Optimization Algorithms for Multi-Agent System

This module implements sophisticated resource allocation and optimization algorithms
that treat tokens as a finite commodity subject to economic principles with
game-theoretic considerations.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import asyncio
from datetime import datetime, timedelta
import json
import heapq
from collections import defaultdict, deque
import math
from scipy.optimize import minimize
from scipy.special import softmax

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier, TokenAllocation

logger = get_structured_logger("resource_optimizer")


class AllocationStrategy(Enum):
    """Resource allocation strategies"""
    FAIR_SHARE = "fair_share"           # Equal allocation
    PERFORMANCE_BASED = "performance"   # Based on historical performance
    UTILITY_MAXIMIZING = "utility_max"  # Maximum expected utility
    RISK_ADJUSTED = "risk_adjusted"     # Adjusted for risk profiles
    COLLABORATIVE = "collaborative"     # Optimized for collaboration
    ADAPTIVE = "adaptive"               # Dynamic strategy selection


@dataclass
class ResourceDemand:
    """Resource demand request from an agent"""
    agent_id: str
    requested_tokens: int
    task_priority: float
    expected_utility: float
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    risk_level: float = 0.5
    collaboration_potential: float = 0.0


@dataclass
class AllocationDecision:
    """Resource allocation decision"""
    agent_id: str
    allocated_tokens: int
    allocation_ratio: float  # allocated / requested
    expected_roi: float
    allocation_strategy: AllocationStrategy
    constraints_applied: List[str] = field(default_factory=list)


class GameTheoreticOptimizer:
    """Game theory-based resource allocation using Nash equilibrium concepts"""
    
    def __init__(self, num_agents: int):
        self.num_agents = num_agents
        self.payoff_matrix = np.zeros((num_agents, num_agents))
        self.cooperation_history = defaultdict(list)
        
    def compute_nash_equilibrium(
        self, 
        agent_utilities: Dict[str, float],
        resource_pool: int
    ) -> Dict[str, int]:
        """
        Compute Nash equilibrium for resource allocation using iterative best response
        """
        
        agents = list(agent_utilities.keys())
        n_agents = len(agents)
        
        if n_agents == 0:
            return {}
        
        # Initialize with equal allocation
        allocations = {agent_id: resource_pool // n_agents for agent_id in agents}
        
        # Iterative best response algorithm
        max_iterations = 50
        convergence_threshold = 0.01
        
        for iteration in range(max_iterations):
            old_allocations = allocations.copy()
            
            for i, agent_id in enumerate(agents):
                # Compute best response for this agent given others' allocations
                others_total = sum(allocations[other_id] for other_id in agents if other_id != agent_id)
                available_for_this_agent = resource_pool - others_total
                
                # Agent's utility function (diminishing returns)
                base_utility = agent_utilities[agent_id]
                
                # Optimal allocation for this agent (simplified utility maximization)
                optimal_allocation = min(
                    available_for_this_agent,
                    int(base_utility * resource_pool / sum(agent_utilities.values()))
                )
                
                allocations[agent_id] = max(1, optimal_allocation)  # Ensure minimum allocation
            
            # Check convergence
            total_change = sum(abs(allocations[agent_id] - old_allocations[agent_id]) 
                             for agent_id in agents)
            
            if total_change < convergence_threshold * resource_pool:
                logger.debug(f"Nash equilibrium converged in {iteration + 1} iterations")
                break
        
        return allocations


class PortfolioOptimizer:
    """Modern Portfolio Theory-inspired resource allocation"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # Baseline utility rate
        self.covariance_matrix = None
        
    def optimize_allocation(
        self, 
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_tolerance: float = 0.5
    ) -> np.ndarray:
        """
        Optimize resource allocation using Markowitz portfolio optimization
        """
        
        n_assets = len(expected_returns)
        
        # Objective function: minimize variance - risk_tolerance * expected_return
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
            return portfolio_variance - risk_tolerance * portfolio_return
        
        # Constraints: weights sum to 1, all weights non-negative
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        ]
        
        bounds = [(0.01, 1.0) for _ in range(n_assets)]  # Minimum 1% allocation
        
        # Initial guess: equal weights
        initial_guess = np.ones(n_assets) / n_assets
        
        try:
            result = minimize(
                objective,
                initial_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("Portfolio optimization failed, using equal weights")
                return initial_guess
                
        except Exception as e:
            logger.error(f"Portfolio optimization error: {str(e)}")
            return initial_guess


class DynamicResourceOptimizer:
    """
    Advanced resource optimizer implementing multiple allocation strategies
    with real-time adaptation and emergent behavior tracking
    """
    
    def __init__(self, total_budget: int, strategy: AllocationStrategy = AllocationStrategy.ADAPTIVE):
        self.total_budget = total_budget
        self.available_budget = total_budget
        self.current_strategy = strategy
        
        self.agent_registry: Dict[str, ResourceAwareAgent] = {}
        self.allocation_history: List[Dict[str, Any]] = []
        self.performance_tracker = defaultdict(list)
        
        # Optimization components
        self.game_optimizer = GameTheoreticOptimizer(0)
        self.portfolio_optimizer = PortfolioOptimizer()
        
        # Strategy performance tracking
        self.strategy_performance = defaultdict(lambda: {'success_rate': 0.5, 'efficiency': 0.5, 'usage_count': 0})
        
        # Dynamic parameters
        self.rebalancing_threshold = 0.1  # Trigger rebalancing when efficiency drops
        self.strategy_switch_threshold = 0.15  # Switch strategies when performance differs by this much
        
        logger.info(f"Initialized DynamicResourceOptimizer with budget {total_budget}")
    
    def register_agent(self, agent: ResourceAwareAgent):
        """Register an agent for resource management"""
        self.agent_registry[agent.agent_id] = agent
        self.game_optimizer = GameTheoreticOptimizer(len(self.agent_registry))
        logger.info(f"Registered agent {agent.agent_id}, total agents: {len(self.agent_registry)}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agent_registry:
            del self.agent_registry[agent_id]
            self.game_optimizer = GameTheoreticOptimizer(len(self.agent_registry))
            logger.info(f"Unregistered agent {agent_id}")
    
    async def optimize_allocation(
        self, 
        demands: List[ResourceDemand],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[AllocationDecision]:
        """
        Main optimization method that selects and applies the best allocation strategy
        """
        
        if not demands:
            return []
        
        # Determine optimal strategy
        if self.current_strategy == AllocationStrategy.ADAPTIVE:
            strategy = await self._select_optimal_strategy(demands)
        else:
            strategy = self.current_strategy
        
        # Apply selected strategy
        decisions = await self._apply_strategy(strategy, demands, constraints)
        
        # Record allocation
        self._record_allocation(strategy, demands, decisions)
        
        # Update available budget
        total_allocated = sum(decision.allocated_tokens for decision in decisions)
        self.available_budget -= total_allocated
        
        logger.info(f"Allocated {total_allocated} tokens using {strategy.value} strategy")
        logger.info(f"Remaining budget: {self.available_budget}")
        
        return decisions
    
    async def _select_optimal_strategy(self, demands: List[ResourceDemand]) -> AllocationStrategy:
        """Select optimal allocation strategy based on current conditions"""
        
        # Analyze current situation
        total_demand = sum(demand.requested_tokens for demand in demands)
        demand_pressure = total_demand / max(self.available_budget, 1)
        
        avg_priority = np.mean([demand.task_priority for demand in demands])
        avg_utility = np.mean([demand.expected_utility for demand in demands])
        avg_risk = np.mean([demand.risk_level for demand in demands])
        
        collaboration_potential = sum(demand.collaboration_potential for demand in demands) / len(demands)
        
        # Strategy selection logic
        strategy_scores = {}
        
        # Fair share: Good when resources are abundant and priorities are similar
        strategy_scores[AllocationStrategy.FAIR_SHARE] = (
            (1.0 - demand_pressure) * 0.4 +  # Abundant resources
            (1.0 - np.std([d.task_priority for d in demands])) * 0.6  # Similar priorities
        )
        
        # Performance-based: Good when agents have different track records
        agent_performance_variance = 0.0
        if len(self.agent_registry) > 1:
            success_rates = [agent.performance_metrics.success_rate for agent in self.agent_registry.values()]
            agent_performance_variance = np.std(success_rates)
        
        strategy_scores[AllocationStrategy.PERFORMANCE_BASED] = agent_performance_variance * 2.0
        
        # Utility maximizing: Good for high-utility tasks
        strategy_scores[AllocationStrategy.UTILITY_MAXIMIZING] = avg_utility * 0.8
        
        # Risk-adjusted: Good for high-risk scenarios
        strategy_scores[AllocationStrategy.RISK_ADJUSTED] = avg_risk * 1.2
        
        # Collaborative: Good when collaboration potential is high
        strategy_scores[AllocationStrategy.COLLABORATIVE] = collaboration_potential * 1.5
        
        # Apply strategy performance history
        for strategy in strategy_scores:
            historical_performance = self.strategy_performance[strategy]['success_rate']
            strategy_scores[strategy] *= (0.5 + historical_performance)
        
        # Select strategy with highest score
        best_strategy = max(strategy_scores.keys(), key=lambda s: strategy_scores[s])
        
        logger.debug(f"Strategy scores: {strategy_scores}")
        logger.info(f"Selected strategy: {best_strategy.value}")
        
        return best_strategy
    
    async def _apply_strategy(
        self, 
        strategy: AllocationStrategy, 
        demands: List[ResourceDemand],
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[AllocationDecision]:
        """Apply specific allocation strategy"""
        
        if constraints is None:
            constraints = {}
        
        if strategy == AllocationStrategy.FAIR_SHARE:
            return await self._fair_share_allocation(demands, constraints)
        elif strategy == AllocationStrategy.PERFORMANCE_BASED:
            return await self._performance_based_allocation(demands, constraints)
        elif strategy == AllocationStrategy.UTILITY_MAXIMIZING:
            return await self._utility_maximizing_allocation(demands, constraints)
        elif strategy == AllocationStrategy.RISK_ADJUSTED:
            return await self._risk_adjusted_allocation(demands, constraints)
        elif strategy == AllocationStrategy.COLLABORATIVE:
            return await self._collaborative_allocation(demands, constraints)
        else:
            # Fallback to fair share
            return await self._fair_share_allocation(demands, constraints)
    
    async def _fair_share_allocation(
        self, 
        demands: List[ResourceDemand], 
        constraints: Dict[str, Any]
    ) -> List[AllocationDecision]:
        """Equal allocation with priority adjustments"""
        
        if not demands:
            return []
        
        total_demand = sum(demand.requested_tokens for demand in demands)
        
        decisions = []
        
        if total_demand <= self.available_budget:
            # Sufficient resources: allocate as requested
            for demand in demands:
                decisions.append(AllocationDecision(
                    agent_id=demand.agent_id,
                    allocated_tokens=demand.requested_tokens,
                    allocation_ratio=1.0,
                    expected_roi=demand.expected_utility,
                    allocation_strategy=AllocationStrategy.FAIR_SHARE
                ))
        else:
            # Insufficient resources: proportional allocation with priority weighting
            priority_weights = softmax([demand.task_priority for demand in demands])
            
            for i, demand in enumerate(demands):
                allocated = int(self.available_budget * priority_weights[i])
                allocated = max(1, min(allocated, demand.requested_tokens))  # Ensure minimum and maximum
                
                decisions.append(AllocationDecision(
                    agent_id=demand.agent_id,
                    allocated_tokens=allocated,
                    allocation_ratio=allocated / demand.requested_tokens,
                    expected_roi=demand.expected_utility * (allocated / demand.requested_tokens),
                    allocation_strategy=AllocationStrategy.FAIR_SHARE,
                    constraints_applied=['priority_weighted', 'resource_constrained']
                ))
        
        return decisions
    
    async def _performance_based_allocation(
        self, 
        demands: List[ResourceDemand], 
        constraints: Dict[str, Any]
    ) -> List[AllocationDecision]:
        """Allocation based on historical agent performance"""
        
        decisions = []
        
        # Get performance metrics for each agent
        agent_performance = {}
        for demand in demands:
            if demand.agent_id in self.agent_registry:
                agent = self.agent_registry[demand.agent_id]
                # Combined performance score
                performance_score = (
                    agent.performance_metrics.success_rate * 0.4 +
                    agent.allocation.efficiency_score * 0.3 +
                    agent.performance_metrics.avg_value_per_token * 0.3
                )
                agent_performance[demand.agent_id] = performance_score
            else:
                agent_performance[demand.agent_id] = 0.5  # Default for unknown agents
        
        # Normalize performance scores
        total_performance = sum(agent_performance.values())
        performance_weights = {
            agent_id: score / total_performance if total_performance > 0 else 1.0 / len(demands)
            for agent_id, score in agent_performance.items()
        }
        
        # Allocate based on performance
        for demand in demands:
            weight = performance_weights[demand.agent_id]
            allocated = int(self.available_budget * weight)
            allocated = max(1, min(allocated, demand.requested_tokens))
            
            decisions.append(AllocationDecision(
                agent_id=demand.agent_id,
                allocated_tokens=allocated,
                allocation_ratio=allocated / demand.requested_tokens,
                expected_roi=demand.expected_utility * agent_performance[demand.agent_id],
                allocation_strategy=AllocationStrategy.PERFORMANCE_BASED,
                constraints_applied=['performance_weighted']
            ))
        
        return decisions
    
    async def _utility_maximizing_allocation(
        self, 
        demands: List[ResourceDemand], 
        constraints: Dict[str, Any]
    ) -> List[AllocationDecision]:
        """Allocation to maximize total expected utility"""
        
        # Sort demands by utility per token (efficiency)
        efficiency_sorted = sorted(
            demands, 
            key=lambda d: d.expected_utility / d.requested_tokens, 
            reverse=True
        )
        
        decisions = []
        remaining_budget = self.available_budget
        
        # Greedy allocation by efficiency
        for demand in efficiency_sorted:
            if remaining_budget <= 0:
                # No budget left
                decisions.append(AllocationDecision(
                    agent_id=demand.agent_id,
                    allocated_tokens=0,
                    allocation_ratio=0.0,
                    expected_roi=0.0,
                    allocation_strategy=AllocationStrategy.UTILITY_MAXIMIZING,
                    constraints_applied=['budget_exhausted']
                ))
            else:
                allocated = min(demand.requested_tokens, remaining_budget)
                remaining_budget -= allocated
                
                decisions.append(AllocationDecision(
                    agent_id=demand.agent_id,
                    allocated_tokens=allocated,
                    allocation_ratio=allocated / demand.requested_tokens,
                    expected_roi=demand.expected_utility * (allocated / demand.requested_tokens),
                    allocation_strategy=AllocationStrategy.UTILITY_MAXIMIZING,
                    constraints_applied=['efficiency_prioritized']
                ))
        
        return decisions
    
    async def _risk_adjusted_allocation(
        self, 
        demands: List[ResourceDemand], 
        constraints: Dict[str, Any]
    ) -> List[AllocationDecision]:
        """Risk-adjusted allocation using portfolio optimization principles"""
        
        if len(demands) < 2:
            return await self._fair_share_allocation(demands, constraints)
        
        # Prepare data for portfolio optimization
        expected_returns = np.array([demand.expected_utility for demand in demands])
        risk_levels = np.array([demand.risk_level for demand in demands])
        
        # Create covariance matrix (simplified)
        n = len(demands)
        covariance_matrix = np.eye(n) * 0.1  # Base variance
        
        # Add correlations based on agent similarity (simplified)
        for i in range(n):
            for j in range(i + 1, n):
                # Correlation based on agent roles (if same role, higher correlation)
                agent_i = self.agent_registry.get(demands[i].agent_id)
                agent_j = self.agent_registry.get(demands[j].agent_id)
                
                if agent_i and agent_j and agent_i.role == agent_j.role:
                    correlation = 0.3
                else:
                    correlation = 0.1
                
                covariance_matrix[i, j] = correlation * risk_levels[i] * risk_levels[j]
                covariance_matrix[j, i] = covariance_matrix[i, j]
        
        # Get optimal weights
        optimal_weights = self.portfolio_optimizer.optimize_allocation(
            expected_returns, covariance_matrix, risk_tolerance=0.5
        )
        
        # Convert weights to token allocations
        decisions = []
        for i, demand in enumerate(demands):
            allocated = int(self.available_budget * optimal_weights[i])
            allocated = max(1, min(allocated, demand.requested_tokens))
            
            decisions.append(AllocationDecision(
                agent_id=demand.agent_id,
                allocated_tokens=allocated,
                allocation_ratio=allocated / demand.requested_tokens,
                expected_roi=demand.expected_utility * optimal_weights[i],
                allocation_strategy=AllocationStrategy.RISK_ADJUSTED,
                constraints_applied=['portfolio_optimized']
            ))
        
        return decisions
    
    async def _collaborative_allocation(
        self, 
        demands: List[ResourceDemand], 
        constraints: Dict[str, Any]
    ) -> List[AllocationDecision]:
        """Allocation optimized for collaboration potential"""
        
        # Build collaboration graph
        collaboration_graph = defaultdict(list)
        
        for demand in demands:
            for other_demand in demands:
                if demand != other_demand and demand.collaboration_potential > 0.3:
                    collaboration_graph[demand.agent_id].append(other_demand.agent_id)
        
        # Use game-theoretic optimization
        agent_utilities = {demand.agent_id: demand.expected_utility for demand in demands}
        nash_allocation = self.game_optimizer.compute_nash_equilibrium(
            agent_utilities, self.available_budget
        )
        
        decisions = []
        for demand in demands:
            allocated = nash_allocation.get(demand.agent_id, 0)
            allocated = min(allocated, demand.requested_tokens)
            
            # Bonus for high collaboration potential
            if demand.collaboration_potential > 0.5:
                bonus = int(allocated * 0.1)  # 10% bonus
                allocated = min(allocated + bonus, demand.requested_tokens)
            
            decisions.append(AllocationDecision(
                agent_id=demand.agent_id,
                allocated_tokens=allocated,
                allocation_ratio=allocated / demand.requested_tokens if demand.requested_tokens > 0 else 0,
                expected_roi=demand.expected_utility * (1 + demand.collaboration_potential),
                allocation_strategy=AllocationStrategy.COLLABORATIVE,
                constraints_applied=['nash_equilibrium', 'collaboration_bonus']
            ))
        
        return decisions
    
    def _record_allocation(
        self, 
        strategy: AllocationStrategy, 
        demands: List[ResourceDemand], 
        decisions: List[AllocationDecision]
    ):
        """Record allocation for performance tracking"""
        
        allocation_record = {
            'timestamp': datetime.now(),
            'strategy': strategy.value,
            'total_demand': sum(d.requested_tokens for d in demands),
            'total_allocated': sum(d.allocated_tokens for d in decisions),
            'num_agents': len(demands),
            'avg_allocation_ratio': np.mean([d.allocation_ratio for d in decisions]),
            'expected_total_roi': sum(d.expected_roi for d in decisions)
        }
        
        self.allocation_history.append(allocation_record)
        
        # Update strategy performance tracking
        self.strategy_performance[strategy]['usage_count'] += 1
    
    async def rebalance_resources(self) -> Dict[str, Any]:
        """Periodically rebalance resources based on performance"""
        
        if len(self.allocation_history) < 3:
            return {'rebalancing': 'insufficient_data'}
        
        # Analyze recent performance
        recent_allocations = self.allocation_history[-5:]
        
        avg_efficiency = np.mean([
            alloc.get('expected_total_roi', 0) / max(alloc.get('total_allocated', 1), 1)
            for alloc in recent_allocations
        ])
        
        # Check if rebalancing is needed
        if avg_efficiency < self.rebalancing_threshold:
            logger.info("Triggering resource rebalancing due to low efficiency")
            
            # Reallocate unused resources
            total_unused = 0
            for agent in self.agent_registry.values():
                if agent.allocation.utilization_rate < 0.5:  # Less than 50% utilized
                    unused = int(agent.allocation.available * 0.3)  # Reclaim 30%
                    agent.allocation.initial_budget -= unused
                    total_unused += unused
            
            # Redistribute to high-performing agents
            high_performers = [
                agent for agent in self.agent_registry.values()
                if agent.performance_metrics.success_rate > 0.8 and
                   agent.allocation.utilization_rate > 0.7
            ]
            
            if high_performers and total_unused > 0:
                bonus_per_agent = total_unused // len(high_performers)
                for agent in high_performers:
                    agent.allocation.initial_budget += bonus_per_agent
                
                logger.info(f"Redistributed {total_unused} tokens to {len(high_performers)} high performers")
            
            return {
                'rebalancing': 'completed',
                'tokens_redistributed': total_unused,
                'beneficiary_agents': len(high_performers)
            }
        
        return {'rebalancing': 'not_needed', 'current_efficiency': avg_efficiency}
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive optimization metrics"""
        
        if not self.allocation_history:
            return {'status': 'no_data'}
        
        recent_allocations = self.allocation_history[-10:]
        
        return {
            'total_budget': self.total_budget,
            'available_budget': self.available_budget,
            'utilization_rate': (self.total_budget - self.available_budget) / self.total_budget,
            'num_registered_agents': len(self.agent_registry),
            'allocation_efficiency': np.mean([
                alloc.get('avg_allocation_ratio', 0) for alloc in recent_allocations
            ]),
            'strategy_performance': dict(self.strategy_performance),
            'current_strategy': self.current_strategy.value,
            'total_allocations': len(self.allocation_history)
        }