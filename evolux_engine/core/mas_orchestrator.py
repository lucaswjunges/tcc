"""
Multi-Agent System Orchestrator with Emergent Behavior Tracking

This module implements a sophisticated Multi-Agent System orchestrator that manages
resource-aware agents, tracks emergent behaviors, and optimizes system-wide performance
through adaptive coordination strategies.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import numpy as np
from datetime import datetime, timedelta
import json
import heapq
from collections import defaultdict, deque
import uuid
import math
from itertools import combinations

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus, ProjectStatus, ExecutionResult
from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier, CollaborationProtocol
from evolux_engine.core.resource_optimizer import DynamicResourceOptimizer, ResourceDemand, AllocationStrategy
from evolux_engine.core.specialized_agents import (
    ResourceAwarePlannerAgent, 
    ResourceAwareExecutorAgent, 
    ResourceAwareCriticAgent
)
from evolux_engine.services.config_manager import ConfigManager

logger = get_structured_logger("mas_orchestrator")


class EmergentBehaviorType(Enum):
    """Types of emergent behaviors to track"""
    COLLABORATIVE_CLUSTERING = "collaborative_clustering"
    RESOURCE_SHARING_PATTERNS = "resource_sharing_patterns"
    SPECIALIZATION_DRIFT = "specialization_drift"
    HIERARCHICAL_ORGANIZATION = "hierarchical_organization"
    COMMUNICATION_NETWORKS = "communication_networks"
    ADAPTIVE_STRATEGIES = "adaptive_strategies"
    SWARM_INTELLIGENCE = "swarm_intelligence"


@dataclass
class EmergentBehavior:
    """Detected emergent behavior pattern"""
    behavior_type: EmergentBehaviorType
    detection_time: datetime
    involved_agents: List[str]
    pattern_strength: float  # 0.0 to 1.0
    persistence_duration: timedelta
    performance_impact: float  # -1.0 to 1.0
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    total_agents: int
    total_tasks_completed: int
    overall_success_rate: float
    resource_utilization_efficiency: float
    collaboration_frequency: float
    emergent_behaviors_detected: int
    system_adaptation_rate: float
    collective_intelligence_score: float


class NetworkAnalyzer:
    """Analyzes agent interaction networks and communication patterns"""
    
    def __init__(self):
        self.interaction_matrix = defaultdict(lambda: defaultdict(float))
        self.communication_history = deque(maxlen=1000)
        self.network_metrics_cache = {}
        self.cache_expiry = timedelta(minutes=5)
        self.last_analysis = datetime.min
    
    def record_interaction(self, agent_a: str, agent_b: str, interaction_type: str, strength: float):
        """Record interaction between agents"""
        self.interaction_matrix[agent_a][agent_b] += strength
        self.interaction_matrix[agent_b][agent_a] += strength
        
        self.communication_history.append({
            'timestamp': datetime.now(),
            'agent_a': agent_a,
            'agent_b': agent_b,
            'interaction_type': interaction_type,
            'strength': strength
        })
    
    def analyze_network_structure(self, agents: List[str]) -> Dict[str, Any]:
        """Analyze the structure of the agent interaction network"""
        
        if datetime.now() - self.last_analysis < self.cache_expiry:
            return self.network_metrics_cache
        
        n_agents = len(agents)
        if n_agents < 2:
            return {'network_density': 0.0, 'clustering_coefficient': 0.0}
        
        # Calculate network density
        total_possible_edges = n_agents * (n_agents - 1) / 2
        actual_edges = 0
        
        for agent_a in agents:
            for agent_b in agents:
                if agent_a != agent_b and self.interaction_matrix[agent_a][agent_b] > 0.1:
                    actual_edges += 1
        
        actual_edges = actual_edges / 2  # Undirected graph
        network_density = actual_edges / total_possible_edges if total_possible_edges > 0 else 0.0
        
        # Calculate clustering coefficient
        clustering_coefficients = []
        for agent in agents:
            neighbors = [
                neighbor for neighbor in agents 
                if neighbor != agent and self.interaction_matrix[agent][neighbor] > 0.1
            ]
            
            if len(neighbors) < 2:
                clustering_coefficients.append(0.0)
                continue
            
            neighbor_connections = 0
            for neighbor_a, neighbor_b in combinations(neighbors, 2):
                if self.interaction_matrix[neighbor_a][neighbor_b] > 0.1:
                    neighbor_connections += 1
            
            max_connections = len(neighbors) * (len(neighbors) - 1) / 2
            clustering_coefficient = neighbor_connections / max_connections if max_connections > 0 else 0.0
            clustering_coefficients.append(clustering_coefficient)
        
        avg_clustering = np.mean(clustering_coefficients) if clustering_coefficients else 0.0
        
        # Calculate centrality measures
        centrality_scores = {}
        for agent in agents:
            # Simple degree centrality
            degree = sum(1 for other in agents if self.interaction_matrix[agent][other] > 0.1)
            centrality_scores[agent] = degree / (n_agents - 1) if n_agents > 1 else 0.0
        
        self.network_metrics_cache = {
            'network_density': network_density,
            'clustering_coefficient': avg_clustering,
            'centrality_scores': centrality_scores,
            'num_connected_components': self._count_connected_components(agents),
            'average_path_length': self._calculate_average_path_length(agents)
        }
        
        self.last_analysis = datetime.now()
        return self.network_metrics_cache
    
    def _count_connected_components(self, agents: List[str]) -> int:
        """Count connected components in the network"""
        visited = set()
        components = 0
        
        for agent in agents:
            if agent not in visited:
                components += 1
                self._dfs_component(agent, agents, visited)
        
        return components
    
    def _dfs_component(self, agent: str, agents: List[str], visited: Set[str]):
        """DFS to find connected component"""
        visited.add(agent)
        
        for other_agent in agents:
            if other_agent not in visited and self.interaction_matrix[agent][other_agent] > 0.1:
                self._dfs_component(other_agent, agents, visited)
    
    def _calculate_average_path_length(self, agents: List[str]) -> float:
        """Calculate average shortest path length in the network"""
        if len(agents) < 2:
            return 0.0
        
        # Simple BFS-based shortest path calculation
        total_path_length = 0
        num_paths = 0
        
        for start_agent in agents:
            distances = self._bfs_distances(start_agent, agents)
            for end_agent, distance in distances.items():
                if distance > 0:  # Reachable
                    total_path_length += distance
                    num_paths += 1
        
        return total_path_length / num_paths if num_paths > 0 else float('inf')
    
    def _bfs_distances(self, start_agent: str, agents: List[str]) -> Dict[str, int]:
        """BFS to calculate distances from start_agent to all other agents"""
        distances = {agent: -1 for agent in agents}  # -1 means unreachable
        distances[start_agent] = 0
        queue = deque([start_agent])
        
        while queue:
            current = queue.popleft()
            current_distance = distances[current]
            
            for neighbor in agents:
                if (neighbor != current and 
                    distances[neighbor] == -1 and 
                    self.interaction_matrix[current][neighbor] > 0.1):
                    
                    distances[neighbor] = current_distance + 1
                    queue.append(neighbor)
        
        return distances


class EmergentBehaviorDetector:
    """Detects and analyzes emergent behaviors in the multi-agent system"""
    
    def __init__(self):
        self.behavior_history: List[EmergentBehavior] = []
        self.detection_thresholds = {
            EmergentBehaviorType.COLLABORATIVE_CLUSTERING: 0.6,
            EmergentBehaviorType.RESOURCE_SHARING_PATTERNS: 0.5,
            EmergentBehaviorType.SPECIALIZATION_DRIFT: 0.4,
            EmergentBehaviorType.HIERARCHICAL_ORGANIZATION: 0.7,
            EmergentBehaviorType.COMMUNICATION_NETWORKS: 0.5,
            EmergentBehaviorType.ADAPTIVE_STRATEGIES: 0.3,
            EmergentBehaviorType.SWARM_INTELLIGENCE: 0.8
        }
        
    def detect_emergent_behaviors(
        self, 
        agents: Dict[str, ResourceAwareAgent],
        network_analyzer: NetworkAnalyzer,
        system_metrics: SystemMetrics
    ) -> List[EmergentBehavior]:
        """Detect emergent behaviors in the system"""
        
        detected_behaviors = []
        
        # Detect collaborative clustering
        clustering_behavior = self._detect_collaborative_clustering(agents, network_analyzer)
        if clustering_behavior:
            detected_behaviors.append(clustering_behavior)
        
        # Detect resource sharing patterns
        sharing_behavior = self._detect_resource_sharing_patterns(agents)
        if sharing_behavior:
            detected_behaviors.append(sharing_behavior)
        
        # Detect specialization drift
        specialization_behavior = self._detect_specialization_drift(agents)
        if specialization_behavior:
            detected_behaviors.append(specialization_behavior)
        
        # Detect hierarchical organization
        hierarchy_behavior = self._detect_hierarchical_organization(agents, network_analyzer)
        if hierarchy_behavior:
            detected_behaviors.append(hierarchy_behavior)
        
        # Detect adaptive strategies
        adaptation_behavior = self._detect_adaptive_strategies(agents)
        if adaptation_behavior:
            detected_behaviors.append(adaptation_behavior)
        
        # Update behavior history
        self.behavior_history.extend(detected_behaviors)
        
        # Prune old behaviors
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.behavior_history = [
            behavior for behavior in self.behavior_history 
            if behavior.detection_time > cutoff_time
        ]
        
        return detected_behaviors
    
    def _detect_collaborative_clustering(
        self, 
        agents: Dict[str, ResourceAwareAgent], 
        network_analyzer: NetworkAnalyzer
    ) -> Optional[EmergentBehavior]:
        """Detect if agents are forming collaborative clusters"""
        
        network_metrics = network_analyzer.analyze_network_structure(list(agents.keys()))
        clustering_coefficient = network_metrics.get('clustering_coefficient', 0.0)
        
        threshold = self.detection_thresholds[EmergentBehaviorType.COLLABORATIVE_CLUSTERING]
        
        if clustering_coefficient > threshold:
            # Find the most connected agents
            centrality_scores = network_metrics.get('centrality_scores', {})
            top_agents = sorted(centrality_scores.keys(), 
                               key=lambda x: centrality_scores[x], reverse=True)[:3]
            
            return EmergentBehavior(
                behavior_type=EmergentBehaviorType.COLLABORATIVE_CLUSTERING,
                detection_time=datetime.now(),
                involved_agents=top_agents,
                pattern_strength=clustering_coefficient,
                persistence_duration=timedelta(minutes=30),  # Estimated
                performance_impact=0.3,  # Generally positive
                description=f"Agents forming tight collaborative clusters with {clustering_coefficient:.2f} clustering coefficient",
                metrics={'clustering_coefficient': clustering_coefficient, 'network_density': network_metrics.get('network_density', 0.0)}
            )
        
        return None
    
    def _detect_resource_sharing_patterns(self, agents: Dict[str, ResourceAwareAgent]) -> Optional[EmergentBehavior]:
        """Detect patterns in resource sharing behavior"""
        
        if len(agents) < 2:
            return None
        
        # Analyze collaboration history for resource sharing patterns
        total_collaborations = 0
        resource_efficient_collaborations = 0
        involved_agents = set()
        
        for agent in agents.values():
            collaborations = agent.collaboration_protocol.collaboration_history
            total_collaborations += len(collaborations)
            
            for collab in collaborations[-10:]:  # Last 10 collaborations
                if collab.get('tokens_consumed', 0) < collab.get('tokens_offered', 0) * 0.8:
                    resource_efficient_collaborations += 1
                    involved_agents.add(collab.get('source_agent', ''))
                    involved_agents.add(collab.get('target_agent', ''))
        
        if total_collaborations > 0:
            efficiency_ratio = resource_efficient_collaborations / total_collaborations
            threshold = self.detection_thresholds[EmergentBehaviorType.RESOURCE_SHARING_PATTERNS]
            
            if efficiency_ratio > threshold and len(involved_agents) >= 2:
                return EmergentBehavior(
                    behavior_type=EmergentBehaviorType.RESOURCE_SHARING_PATTERNS,
                    detection_time=datetime.now(),
                    involved_agents=list(involved_agents),
                    pattern_strength=efficiency_ratio,
                    persistence_duration=timedelta(hours=1),
                    performance_impact=0.4,  # Positive impact
                    description=f"Efficient resource sharing patterns detected with {efficiency_ratio:.2f} efficiency ratio",
                    metrics={'efficiency_ratio': efficiency_ratio, 'total_collaborations': total_collaborations}
                )
        
        return None
    
    def _detect_specialization_drift(self, agents: Dict[str, ResourceAwareAgent]) -> Optional[EmergentBehavior]:
        """Detect if agents are drifting towards specialization"""
        
        specialization_scores = {}
        
        for agent_id, agent in agents.items():
            if len(agent.execution_history) < 5:
                continue
            
            # Analyze task type distribution in recent history
            recent_tasks = agent.execution_history[-10:]
            task_type_counts = defaultdict(int)
            
            for task in recent_tasks:
                task_type = task.get('task_type', 'unknown')
                task_type_counts[task_type] += 1
            
            if task_type_counts:
                # Calculate specialization using entropy
                total_tasks = sum(task_type_counts.values())
                probabilities = [count / total_tasks for count in task_type_counts.values()]
                entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
                max_entropy = math.log2(len(task_type_counts))
                
                # Specialization score: 1.0 means fully specialized, 0.0 means uniform distribution
                specialization_score = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
                specialization_scores[agent_id] = specialization_score
        
        if specialization_scores:
            avg_specialization = np.mean(list(specialization_scores.values()))
            threshold = self.detection_thresholds[EmergentBehaviorType.SPECIALIZATION_DRIFT]
            
            if avg_specialization > threshold:
                # Find most specialized agents
                specialized_agents = [
                    agent_id for agent_id, score in specialization_scores.items() 
                    if score > threshold
                ]
                
                return EmergentBehavior(
                    behavior_type=EmergentBehaviorType.SPECIALIZATION_DRIFT,
                    detection_time=datetime.now(),
                    involved_agents=specialized_agents,
                    pattern_strength=avg_specialization,
                    persistence_duration=timedelta(hours=2),
                    performance_impact=0.2,  # Can be positive for efficiency
                    description=f"Agents showing specialization drift with avg score {avg_specialization:.2f}",
                    metrics={'specialization_scores': specialization_scores}
                )
        
        return None
    
    def _detect_hierarchical_organization(
        self, 
        agents: Dict[str, ResourceAwareAgent], 
        network_analyzer: NetworkAnalyzer
    ) -> Optional[EmergentBehavior]:
        """Detect emergence of hierarchical organization patterns"""
        
        network_metrics = network_analyzer.analyze_network_structure(list(agents.keys()))
        centrality_scores = network_metrics.get('centrality_scores', {})
        
        if len(centrality_scores) < 3:
            return None
        
        centrality_values = list(centrality_scores.values())
        centrality_variance = np.var(centrality_values)
        
        # High variance indicates hierarchical structure (some agents much more central)
        threshold = self.detection_thresholds[EmergentBehaviorType.HIERARCHICAL_ORGANIZATION]
        
        if centrality_variance > threshold:
            # Identify hub agents (top 20%)
            sorted_agents = sorted(centrality_scores.keys(), 
                                 key=lambda x: centrality_scores[x], reverse=True)
            num_hubs = max(1, len(sorted_agents) // 5)
            hub_agents = sorted_agents[:num_hubs]
            
            return EmergentBehavior(
                behavior_type=EmergentBehaviorType.HIERARCHICAL_ORGANIZATION,
                detection_time=datetime.now(),
                involved_agents=hub_agents,
                pattern_strength=centrality_variance,
                persistence_duration=timedelta(hours=3),
                performance_impact=0.1,  # Can improve coordination
                description=f"Hierarchical organization emerging with centrality variance {centrality_variance:.3f}",
                metrics={'centrality_variance': centrality_variance, 'hub_agents': hub_agents}
            )
        
        return None
    
    def _detect_adaptive_strategies(self, agents: Dict[str, ResourceAwareAgent]) -> Optional[EmergentBehavior]:
        """Detect adaptive strategy changes across agents"""
        
        adaptive_agents = []
        strategy_changes = 0
        
        for agent_id, agent in agents.items():
            if len(agent.execution_history) < 10:
                continue
            
            # Look for strategy changes in recent history
            recent_tasks = agent.execution_history[-10:]
            strategies = [task.get('strategy', 'default') for task in recent_tasks]
            
            # Count unique strategies
            unique_strategies = len(set(strategies))
            
            if unique_strategies >= 3:  # At least 3 different strategies
                adaptive_agents.append(agent_id)
                strategy_changes += unique_strategies
        
        if adaptive_agents:
            adaptation_rate = strategy_changes / len(adaptive_agents)
            threshold = self.detection_thresholds[EmergentBehaviorType.ADAPTIVE_STRATEGIES]
            
            if adaptation_rate > threshold:
                return EmergentBehavior(
                    behavior_type=EmergentBehaviorType.ADAPTIVE_STRATEGIES,
                    detection_time=datetime.now(),
                    involved_agents=adaptive_agents,
                    pattern_strength=adaptation_rate / 5.0,  # Normalize
                    persistence_duration=timedelta(hours=1),
                    performance_impact=0.3,  # Generally positive
                    description=f"Adaptive strategy emergence with {adaptation_rate:.1f} avg strategies per agent",
                    metrics={'adaptation_rate': adaptation_rate, 'strategy_changes': strategy_changes}
                )
        
        return None


class MultiAgentSystemOrchestrator:
    """
    Advanced Multi-Agent System orchestrator with emergent behavior tracking,
    adaptive coordination, and resource optimization at the system level
    """
    
    def __init__(self, total_system_budget: int, config_manager: ConfigManager):
        self.total_system_budget = total_system_budget
        self.config_manager = config_manager
        self.system_id = str(uuid.uuid4())
        
        # Agent management
        self.agents: Dict[str, ResourceAwareAgent] = {}
        self.agent_roles: Dict[str, str] = {}
        
        # Resource management
        self.resource_optimizer = DynamicResourceOptimizer(
            total_budget=total_system_budget,
            strategy=AllocationStrategy.ADAPTIVE
        )
        
        # Behavior analysis
        self.network_analyzer = NetworkAnalyzer()
        self.behavior_detector = EmergentBehaviorDetector()
        
        # System state
        self.system_metrics = SystemMetrics(
            total_agents=0,
            total_tasks_completed=0,
            overall_success_rate=1.0,
            resource_utilization_efficiency=0.0,
            collaboration_frequency=0.0,
            emergent_behaviors_detected=0,
            system_adaptation_rate=0.0,
            collective_intelligence_score=0.0
        )
        
        # Task management
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        self.failed_tasks: List[Dict[str, Any]] = []
        
        # Coordination parameters
        self.coordination_strategy = "adaptive"
        self.rebalancing_interval = timedelta(minutes=10)
        self.last_rebalancing = datetime.now()
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized MultiAgentSystemOrchestrator with budget {total_system_budget}")
    
    async def initialize_default_agents(self) -> Dict[str, str]:
        """Initialize default set of resource-aware agents"""
        
        # Calculate budget allocation for default agents
        planner_budget = int(self.total_system_budget * 0.3)  # 30% for planning
        executor_budget = int(self.total_system_budget * 0.5)  # 50% for execution
        critic_budget = int(self.total_system_budget * 0.2)    # 20% for criticism
        
        # Create specialized agents
        planner = ResourceAwarePlannerAgent("planner_001", planner_budget, self.config_manager)
        executor = ResourceAwareExecutorAgent("executor_001", executor_budget, self.config_manager)
        critic = ResourceAwareCriticAgent("critic_001", critic_budget, self.config_manager)
        
        # Register agents
        await self.register_agent(planner)
        await self.register_agent(executor)
        await self.register_agent(critic)
        
        return {
            "planner": planner.agent_id,
            "executor": executor.agent_id,
            "critic": critic.agent_id
        }
    
    async def register_agent(self, agent: ResourceAwareAgent):
        """Register a new agent with the system"""
        
        self.agents[agent.agent_id] = agent
        self.agent_roles[agent.agent_id] = agent.role
        
        # Register with resource optimizer
        self.resource_optimizer.register_agent(agent)
        
        # Update system metrics
        self.system_metrics.total_agents = len(self.agents)
        
        logger.info(f"Registered agent {agent.agent_id} with role {agent.role}")
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the system"""
        
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_roles[agent_id]
            
            # Unregister from resource optimizer
            self.resource_optimizer.unregister_agent(agent_id)
            
            # Update system metrics
            self.system_metrics.total_agents = len(self.agents)
            
            logger.info(f"Unregistered agent {agent_id}")
    
    async def submit_task(self, task: Dict[str, Any], priority: float = 0.5) -> str:
        """Submit a task to the system"""
        
        task_id = str(uuid.uuid4())
        task_submission = {
            'task_id': task_id,
            'task': task,
            'priority': priority,
            'submission_time': datetime.now(),
            'status': 'queued'
        }
        
        self.task_queue.append(task_submission)
        logger.info(f"Submitted task {task_id} with priority {priority}")
        
        return task_id
    
    async def process_task_queue(self) -> Dict[str, Any]:
        """Process all tasks in the queue with optimal agent allocation"""
        
        if not self.task_queue:
            return {'status': 'no_tasks', 'processed': 0}
        
        # Sort tasks by priority
        self.task_queue.sort(key=lambda x: x['priority'], reverse=True)
        
        processing_results = []
        
        while self.task_queue:
            task_submission = self.task_queue.pop(0)
            result = await self._process_single_task(task_submission)
            processing_results.append(result)
            
            # Periodic system maintenance
            if len(processing_results) % 5 == 0:
                await self._perform_system_maintenance()
        
        # Final system analysis
        await self._analyze_system_performance()
        
        return {
            'status': 'completed',
            'processed': len(processing_results),
            'successful': sum(1 for r in processing_results if r.get('success', False)),
            'failed': sum(1 for r in processing_results if not r.get('success', False))
        }
    
    async def _process_single_task(self, task_submission: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task with optimal agent selection"""
        
        task = task_submission['task']
        task_id = task_submission['task_id']
        priority = task_submission['priority']
        
        # Determine optimal agent for the task
        optimal_agent_id = await self._select_optimal_agent(task, priority)
        
        if not optimal_agent_id:
            logger.warning(f"No suitable agent found for task {task_id}")
            self.failed_tasks.append({
                'task_id': task_id,
                'task': task,
                'failure_reason': 'no_suitable_agent',
                'timestamp': datetime.now()
            })
            return {'success': False, 'error': 'no_suitable_agent'}
        
        # Create resource demand
        agent = self.agents[optimal_agent_id]
        estimated_tokens = self._estimate_task_tokens(task, agent)
        
        resource_demand = ResourceDemand(
            agent_id=optimal_agent_id,
            requested_tokens=estimated_tokens,
            task_priority=priority,
            expected_utility=agent.compute_expected_utility("task_execution", estimated_tokens, task),
            deadline=None,
            dependencies=[],
            risk_level=task.get('complexity', 1.0) / 2.0,  # Convert complexity to risk
            collaboration_potential=self._assess_collaboration_potential(task, agent)
        )
        
        # Optimize resource allocation
        allocation_decisions = await self.resource_optimizer.optimize_allocation([resource_demand])
        
        if not allocation_decisions or allocation_decisions[0].allocated_tokens == 0:
            logger.warning(f"No resources allocated for task {task_id}")
            self.failed_tasks.append({
                'task_id': task_id,
                'task': task,
                'failure_reason': 'no_resources_allocated',
                'timestamp': datetime.now()
            })
            return {'success': False, 'error': 'no_resources_allocated'}
        
        # Execute task
        try:
            context = {
                'complexity': task.get('complexity', 1.0),
                'importance': priority,
                'allocated_tokens': allocation_decisions[0].allocated_tokens,
                'task_id': task_id
            }
            
            start_time = datetime.now()
            result = await agent.execute(task, context)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record interaction for network analysis
            if result.get('success', False):
                self.network_analyzer.record_interaction(
                    optimal_agent_id, 'system', 'task_completion', 1.0
                )
            
            # Update task records
            task_record = {
                'task_id': task_id,
                'task': task,
                'agent_id': optimal_agent_id,
                'result': result,
                'execution_time': execution_time,
                'timestamp': datetime.now(),
                'priority': priority
            }
            
            if result.get('success', False):
                self.completed_tasks.append(task_record)
                self.system_metrics.total_tasks_completed += 1
            else:
                self.failed_tasks.append(task_record)
            
            # Update system metrics
            await self._update_system_metrics()
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            self.failed_tasks.append({
                'task_id': task_id,
                'task': task,
                'failure_reason': f"execution_error: {str(e)}",
                'timestamp': datetime.now()
            })
            return {'success': False, 'error': str(e)}
    
    async def _select_optimal_agent(self, task: Dict[str, Any], priority: float) -> Optional[str]:
        """Select the optimal agent for a given task"""
        
        if not self.agents:
            return None
        
        task_type = task.get('type', 'generic')
        
        # Role-based initial filtering
        role_preferences = {
            'planning': ['resource_aware_planner'],
            'execution': ['resource_aware_executor'],
            'validation': ['resource_aware_critic'],
            'create_file': ['resource_aware_executor', 'resource_aware_planner'],
            'modify_file': ['resource_aware_executor'],
            'execute_command': ['resource_aware_executor'],
            'validate_artifact': ['resource_aware_critic', 'resource_aware_executor']
        }
        
        preferred_roles = role_preferences.get(task_type, list(set(self.agent_roles.values())))
        
        # Score agents based on multiple criteria
        agent_scores = {}
        
        for agent_id, agent in self.agents.items():
            if agent.role not in preferred_roles:
                continue
            
            # Base score from role match
            role_score = 1.0 if agent.role in preferred_roles[:1] else 0.7
            
            # Performance score
            performance_score = agent.performance_metrics.success_rate
            
            # Resource availability score
            resource_ratio = agent.allocation.available / agent.allocation.initial_budget
            resource_score = min(1.0, resource_ratio * 2.0)  # Prefer agents with available resources
            
            # Efficiency score
            efficiency_score = agent.allocation.efficiency_score
            
            # Collaboration propensity (good for complex tasks)
            collaboration_score = agent.collaboration_propensity if priority > 0.7 else 0.5
            
            # Combine scores
            total_score = (
                role_score * 0.3 +
                performance_score * 0.25 +
                resource_score * 0.2 +
                efficiency_score * 0.15 +
                collaboration_score * 0.1
            )
            
            agent_scores[agent_id] = total_score
        
        if not agent_scores:
            return None
        
        # Select agent with highest score
        optimal_agent_id = max(agent_scores.keys(), key=lambda x: agent_scores[x])
        
        logger.debug(f"Selected agent {optimal_agent_id} with score {agent_scores[optimal_agent_id]:.3f}")
        
        return optimal_agent_id
    
    def _estimate_task_tokens(self, task: Dict[str, Any], agent: ResourceAwareAgent) -> int:
        """Estimate token requirements for a task"""
        
        # This is a simplified estimation - in practice, this would be more sophisticated
        base_estimate = 300
        
        complexity = task.get('complexity', 1.0)
        task_type = task.get('type', 'generic')
        
        type_multipliers = {
            'planning': 1.5,
            'create_file': 1.2,
            'modify_file': 0.8,
            'execute_command': 0.6,
            'validate_artifact': 1.0,
            'generic': 1.0
        }
        
        type_multiplier = type_multipliers.get(task_type, 1.0)
        
        estimate = int(base_estimate * complexity * type_multiplier)
        
        # Adjust for agent model tier
        tier_multiplier = agent.allocation.model_tier.performance_factor * 0.9
        
        return int(estimate * tier_multiplier)
    
    def _assess_collaboration_potential(self, task: Dict[str, Any], agent: ResourceAwareAgent) -> float:
        """Assess the collaboration potential for a task"""
        
        complexity = task.get('complexity', 1.0)
        
        # Higher complexity tasks benefit more from collaboration
        base_potential = min(1.0, complexity / 2.0)
        
        # Agents with high collaboration propensity are more likely to collaborate
        agent_factor = agent.collaboration_propensity
        
        return base_potential * agent_factor
    
    async def _perform_system_maintenance(self):
        """Perform periodic system maintenance and optimization"""
        
        current_time = datetime.now()
        
        # Check if rebalancing is needed
        if current_time - self.last_rebalancing > self.rebalancing_interval:
            await self._rebalance_system_resources()
            self.last_rebalancing = current_time
        
        # Detect emergent behaviors
        emergent_behaviors = self.behavior_detector.detect_emergent_behaviors(
            self.agents, self.network_analyzer, self.system_metrics
        )
        
        if emergent_behaviors:
            logger.info(f"Detected {len(emergent_behaviors)} emergent behaviors")
            for behavior in emergent_behaviors:
                logger.info(f"  - {behavior.behavior_type.value}: {behavior.description}")
            
            self.system_metrics.emergent_behaviors_detected += len(emergent_behaviors)
        
        # Trigger meta-cognitive reflection for agents
        for agent in self.agents.values():
            if len(agent.execution_history) >= 3:
                await agent.meta_cognitive_reflection()
    
    async def _rebalance_system_resources(self):
        """Rebalance resources across the system"""
        
        logger.info("Performing system resource rebalancing")
        
        rebalancing_result = await self.resource_optimizer.rebalance_resources()
        
        if rebalancing_result.get('rebalancing') == 'completed':
            tokens_redistributed = rebalancing_result.get('tokens_redistributed', 0)
            beneficiaries = rebalancing_result.get('beneficiary_agents', 0)
            
            logger.info(f"Redistributed {tokens_redistributed} tokens to {beneficiaries} agents")
            
            # Update system metrics
            self.system_metrics.system_adaptation_rate = min(1.0, 
                self.system_metrics.system_adaptation_rate + 0.1)
    
    async def _update_system_metrics(self):
        """Update system-wide performance metrics"""
        
        if not self.agents:
            return
        
        # Calculate overall success rate
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks)
        if total_tasks > 0:
            self.system_metrics.overall_success_rate = len(self.completed_tasks) / total_tasks
        
        # Calculate resource utilization efficiency
        total_consumed = sum(agent.allocation.consumed for agent in self.agents.values())
        total_budget = sum(agent.allocation.initial_budget for agent in self.agents.values())
        
        if total_budget > 0:
            utilization_rate = total_consumed / total_budget
            
            # Efficiency considers both utilization and success rate
            self.system_metrics.resource_utilization_efficiency = (
                utilization_rate * self.system_metrics.overall_success_rate
            )
        
        # Calculate collaboration frequency
        total_collaborations = sum(
            len(agent.collaboration_protocol.collaboration_history) 
            for agent in self.agents.values()
        )
        
        if total_tasks > 0:
            self.system_metrics.collaboration_frequency = total_collaborations / total_tasks
        
        # Calculate collective intelligence score
        avg_performance = np.mean([
            agent.performance_metrics.success_rate for agent in self.agents.values()
        ])
        
        network_metrics = self.network_analyzer.analyze_network_structure(list(self.agents.keys()))
        network_density = network_metrics.get('network_density', 0.0)
        
        # Collective intelligence combines individual performance with network effects
        self.system_metrics.collective_intelligence_score = (
            avg_performance * 0.7 + network_density * 0.3
        )
    
    async def _analyze_system_performance(self):
        """Analyze and record system performance"""
        
        performance_snapshot = {
            'timestamp': datetime.now(),
            'system_metrics': {
                'total_agents': self.system_metrics.total_agents,
                'total_tasks_completed': self.system_metrics.total_tasks_completed,
                'overall_success_rate': self.system_metrics.overall_success_rate,
                'resource_utilization_efficiency': self.system_metrics.resource_utilization_efficiency,
                'collaboration_frequency': self.system_metrics.collaboration_frequency,
                'emergent_behaviors_detected': self.system_metrics.emergent_behaviors_detected,
                'collective_intelligence_score': self.system_metrics.collective_intelligence_score
            },
            'agent_performance': {
                agent_id: {
                    'success_rate': agent.performance_metrics.success_rate,
                    'efficiency_score': agent.allocation.efficiency_score,
                    'utilization_rate': agent.allocation.utilization_rate,
                    'collaboration_count': len(agent.collaboration_protocol.collaboration_history)
                }
                for agent_id, agent in self.agents.items()
            },
            'network_metrics': self.network_analyzer.analyze_network_structure(list(self.agents.keys())),
            'resource_optimization_metrics': self.resource_optimizer.get_optimization_metrics()
        }
        
        self.performance_history.append(performance_snapshot)
        
        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        logger.info(f"System performance analysis completed")
        logger.info(f"  Success rate: {self.system_metrics.overall_success_rate:.3f}")
        logger.info(f"  Resource efficiency: {self.system_metrics.resource_utilization_efficiency:.3f}")
        logger.info(f"  Collective intelligence: {self.system_metrics.collective_intelligence_score:.3f}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        return {
            'system_id': self.system_id,
            'agents': {
                agent_id: agent.get_resource_status() 
                for agent_id, agent in self.agents.items()
            },
            'system_metrics': {
                'total_agents': self.system_metrics.total_agents,
                'total_tasks_completed': self.system_metrics.total_tasks_completed,
                'overall_success_rate': self.system_metrics.overall_success_rate,
                'resource_utilization_efficiency': self.system_metrics.resource_utilization_efficiency,
                'collaboration_frequency': self.system_metrics.collaboration_frequency,
                'emergent_behaviors_detected': self.system_metrics.emergent_behaviors_detected,
                'collective_intelligence_score': self.system_metrics.collective_intelligence_score
            },
            'task_status': {
                'queued': len(self.task_queue),
                'completed': len(self.completed_tasks),
                'failed': len(self.failed_tasks)
            },
            'emergent_behaviors': [
                {
                    'type': behavior.behavior_type.value,
                    'strength': behavior.pattern_strength,
                    'agents': behavior.involved_agents,
                    'description': behavior.description
                }
                for behavior in self.behavior_detector.behavior_history[-5:]  # Last 5 behaviors
            ],
            'network_analysis': self.network_analyzer.analyze_network_structure(list(self.agents.keys())),
            'resource_optimization': self.resource_optimizer.get_optimization_metrics()
        }