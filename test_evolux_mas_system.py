#!/usr/bin/env python3
"""
Comprehensive Test Suite for EVOLUX Multi-Agent System

This test suite validates the resource-constrained optimization, agent collaboration,
emergent behavior detection, and system-wide performance of the EVOLUX MAS.
"""

import asyncio
import pytest
import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test imports
from evolux_engine.core.resource_aware_agent import (
    ResourceAwareAgent, ModelTier, TokenAllocation, AgentPerformanceMetrics
)
from evolux_engine.core.resource_optimizer import (
    DynamicResourceOptimizer, ResourceDemand, AllocationStrategy, GameTheoreticOptimizer
)
from evolux_engine.core.specialized_agents import (
    ResourceAwarePlannerAgent, ResourceAwareExecutorAgent, ResourceAwareCriticAgent
)
from evolux_engine.core.mas_orchestrator import (
    MultiAgentSystemOrchestrator, EmergentBehaviorDetector, NetworkAnalyzer
)
from evolux_engine.core.evolux_mas_integration import (
    HybridOrchestrator, ResourceAwareTaskConverter, PerformanceMonitor
)
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("test_evolux_mas")


class MockConfigManager:
    """Mock configuration manager for testing"""
    
    def __init__(self):
        self.settings = {
            "default_llm_provider": "mock",
            "token_budget_multiplier": 1.0,
            "logging_level": "INFO"
        }
        self.api_keys = {
            "mock": "mock_api_key"
        }
    
    def get_global_setting(self, key: str, default=None):
        return self.settings.get(key, default)
    
    def get_api_key(self, provider: str):
        return self.api_keys.get(provider, "mock_key")
    
    def get_default_model_for(self, role: str):
        return "mock-model"


class MockLLMClient:
    """Mock LLM client for testing"""
    
    def __init__(self, provider: str, api_key: str, model_name: str):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
    
    async def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        # Simulate response generation
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if "plan" in prompt.lower():
            return '''
            {
                "tasks": [
                    {
                        "id": "task_1",
                        "description": "Create main application file",
                        "type": "create_file",
                        "estimated_tokens": 200,
                        "priority": 0.8,
                        "dependencies": [],
                        "expected_value": 1.5
                    },
                    {
                        "id": "task_2", 
                        "description": "Implement authentication",
                        "type": "modify_file",
                        "estimated_tokens": 300,
                        "priority": 0.9,
                        "dependencies": ["task_1"],
                        "expected_value": 2.0
                    }
                ],
                "execution_strategy": "sequential",
                "risk_assessment": "medium",
                "total_estimated_cost": 500
            }
            '''
        elif "validate" in prompt.lower():
            return "The artifact meets the specified criteria. Validation passed with high confidence."
        elif "criticize" in prompt.lower() or "evaluate" in prompt.lower():
            return "Quality score: 0.8. Strengths: well-structured code. Issues: minor optimization opportunities. Recommendations: add error handling."
        else:
            return f"Mock response for: {prompt[:50]}..."


# Monkey patch LLMClient for testing
import evolux_engine.llms.llm_client
evolux_engine.llms.llm_client.LLMClient = MockLLMClient


class TestResourceAwareAgent:
    """Test suite for ResourceAwareAgent base class"""
    
    @pytest.fixture
    def mock_config(self):
        return MockConfigManager()
    
    @pytest.fixture
    def test_agent(self, mock_config):
        return TestableResourceAwareAgent(
            agent_id="test_agent_001",
            role="test_role",
            initial_token_budget=1000,
            model_tier=ModelTier.BALANCED
        )
    
    def test_token_allocation_initialization(self, test_agent):
        """Test token allocation initialization"""
        assert test_agent.allocation.initial_budget == 1000
        assert test_agent.allocation.consumed == 0
        assert test_agent.allocation.available == 1000
        assert test_agent.allocation.utilization_rate == 0.0
    
    def test_token_allocation_and_consumption(self, test_agent):
        """Test token allocation and consumption tracking"""
        # Allocate tokens
        success = test_agent.allocation.allocate_tokens(300, "test_task", 1.5)
        assert success
        assert test_agent.allocation.consumed == 300
        assert test_agent.allocation.available == 700
        assert test_agent.allocation.utilization_rate == 0.3
        
        # Try to allocate more than available
        success = test_agent.allocation.allocate_tokens(800, "large_task", 2.0)
        assert not success
        assert test_agent.allocation.consumed == 300  # Should remain unchanged
    
    def test_utility_computation(self, test_agent):
        """Test expected utility computation"""
        context = {'complexity': 1.5, 'importance': 0.8}
        utility = test_agent.compute_expected_utility("test_action", 200, context)
        
        assert isinstance(utility, float)
        assert utility > 0  # Should be positive for reasonable inputs
    
    def test_success_probability_estimation(self, test_agent):
        """Test success probability estimation"""
        context = {'complexity': 2.0}
        prob = test_agent._estimate_success_probability("test_action", context)
        
        assert 0.0 <= prob <= 1.0
        assert isinstance(prob, float)
    
    def test_model_tier_upgrade_decision(self, test_agent):
        """Test model tier upgrade decision logic"""
        # High complexity and importance should suggest upgrade
        should_upgrade = test_agent.should_upgrade_model_tier(2.0, 0.9)
        
        # Result depends on specific logic, but should be boolean
        assert isinstance(should_upgrade, bool)
    
    @pytest.mark.asyncio
    async def test_meta_cognitive_reflection(self, test_agent):
        """Test meta-cognitive reflection capabilities"""
        # Add some execution history
        for i in range(5):
            test_agent.execution_history.append({
                'timestamp': datetime.now(),
                'success': i % 2 == 0,  # Alternating success/failure
                'efficiency': 0.6 + (i * 0.1),
                'strategy': f'strategy_{i % 3}'
            })
        
        reflection = await test_agent.meta_cognitive_reflection()
        
        assert 'avg_success_rate' in reflection
        assert 'avg_efficiency' in reflection
        assert 'adaptations' in reflection
        assert isinstance(reflection['adaptations'], list)
    
    def test_resource_status_reporting(self, test_agent):
        """Test resource status reporting"""
        # Consume some tokens
        test_agent.allocation.allocate_tokens(250, "test_consumption", 1.0)
        
        status = test_agent.get_resource_status()
        
        assert 'agent_id' in status
        assert 'tokens' in status
        assert 'performance' in status
        assert status['tokens']['consumed'] == 250
        assert status['tokens']['available'] == 750


class TestableResourceAwareAgent(ResourceAwareAgent):
    """Testable concrete implementation of ResourceAwareAgent"""
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execute method for testing"""
        estimated_tokens = 100
        
        if not self.allocation.allocate_tokens(estimated_tokens, "test_execution", 1.0):
            return {'success': False, 'error': 'insufficient_tokens'}
        
        # Simulate execution
        await asyncio.sleep(0.05)
        
        success = context.get('force_success', True)
        return {
            'success': success,
            'tokens_used': estimated_tokens,
            'result': 'Mock execution result'
        }


class TestResourceOptimizer:
    """Test suite for DynamicResourceOptimizer"""
    
    @pytest.fixture
    def optimizer(self):
        return DynamicResourceOptimizer(total_budget=5000, strategy=AllocationStrategy.ADAPTIVE)
    
    @pytest.fixture
    def test_agents(self):
        agents = []
        for i in range(3):
            agent = TestableResourceAwareAgent(
                agent_id=f"agent_{i}",
                role=f"role_{i}",
                initial_token_budget=1000
            )
            agents.append(agent)
        return agents
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.total_budget == 5000
        assert optimizer.available_budget == 5000
        assert optimizer.current_strategy == AllocationStrategy.ADAPTIVE
        assert len(optimizer.agent_registry) == 0
    
    def test_agent_registration(self, optimizer, test_agents):
        """Test agent registration and unregistration"""
        # Register agents
        for agent in test_agents:
            optimizer.register_agent(agent)
        
        assert len(optimizer.agent_registry) == 3
        assert all(agent.agent_id in optimizer.agent_registry for agent in test_agents)
        
        # Unregister one agent
        optimizer.unregister_agent(test_agents[0].agent_id)
        assert len(optimizer.agent_registry) == 2
        assert test_agents[0].agent_id not in optimizer.agent_registry
    
    @pytest.mark.asyncio
    async def test_fair_share_allocation(self, optimizer, test_agents):
        """Test fair share allocation strategy"""
        # Register agents
        for agent in test_agents:
            optimizer.register_agent(agent)
        
        # Create resource demands
        demands = [
            ResourceDemand(
                agent_id=agent.agent_id,
                requested_tokens=500,
                task_priority=0.5,
                expected_utility=1.0
            )
            for agent in test_agents
        ]
        
        # Test allocation
        decisions = await optimizer._fair_share_allocation(demands, {})
        
        assert len(decisions) == 3
        assert all(decision.allocated_tokens > 0 for decision in decisions)
        assert sum(decision.allocated_tokens for decision in decisions) <= optimizer.available_budget
    
    @pytest.mark.asyncio
    async def test_utility_maximizing_allocation(self, optimizer, test_agents):
        """Test utility maximizing allocation strategy"""
        # Register agents
        for agent in test_agents:
            optimizer.register_agent(agent)
        
        # Create demands with different utilities
        demands = [
            ResourceDemand(
                agent_id=test_agents[0].agent_id,
                requested_tokens=300,
                task_priority=0.5,
                expected_utility=2.0  # High utility
            ),
            ResourceDemand(
                agent_id=test_agents[1].agent_id,
                requested_tokens=400,
                task_priority=0.5,
                expected_utility=0.5  # Low utility
            ),
            ResourceDemand(
                agent_id=test_agents[2].agent_id,
                requested_tokens=200,
                task_priority=0.5,
                expected_utility=1.5  # Medium utility
            )
        ]
        
        decisions = await optimizer._utility_maximizing_allocation(demands, {})
        
        # High utility agent should get full allocation first
        high_utility_decision = next(d for d in decisions if d.agent_id == test_agents[0].agent_id)
        assert high_utility_decision.allocated_tokens == 300
    
    @pytest.mark.asyncio
    async def test_adaptive_strategy_selection(self, optimizer, test_agents):
        """Test adaptive strategy selection"""
        # Register agents with different performance
        for i, agent in enumerate(test_agents):
            agent.performance_metrics.success_rate = 0.5 + (i * 0.2)  # Different success rates
            optimizer.register_agent(agent)
        
        demands = [
            ResourceDemand(
                agent_id=agent.agent_id,
                requested_tokens=300,
                task_priority=0.6,
                expected_utility=1.0
            )
            for agent in test_agents
        ]
        
        strategy = await optimizer._select_optimal_strategy(demands)
        assert isinstance(strategy, AllocationStrategy)
    
    @pytest.mark.asyncio
    async def test_resource_rebalancing(self, optimizer, test_agents):
        """Test resource rebalancing functionality"""
        # Register agents and simulate some usage
        for agent in test_agents:
            optimizer.register_agent(agent)
            # Simulate different utilization rates
            agent.allocation.consumed = 200 * (test_agents.index(agent) + 1)
            agent.performance_metrics.success_rate = 0.9 if agent == test_agents[0] else 0.5
        
        # Add some allocation history
        optimizer.allocation_history = [
            {'expected_total_roi': 100, 'total_allocated': 1000},
            {'expected_total_roi': 80, 'total_allocated': 1200},
            {'expected_total_roi': 60, 'total_allocated': 1100}
        ]
        
        result = await optimizer.rebalance_resources()
        assert 'rebalancing' in result


class TestGameTheoreticOptimizer:
    """Test suite for game-theoretic optimization"""
    
    def test_nash_equilibrium_computation(self):
        """Test Nash equilibrium computation"""
        optimizer = GameTheoreticOptimizer(3)
        
        agent_utilities = {
            'agent_1': 1.0,
            'agent_2': 1.5,
            'agent_3': 0.8
        }
        
        resource_pool = 1000
        
        allocation = optimizer.compute_nash_equilibrium(agent_utilities, resource_pool)
        
        assert len(allocation) == 3
        assert sum(allocation.values()) <= resource_pool
        assert all(tokens > 0 for tokens in allocation.values())
        
        # Agent with higher utility should get more resources
        assert allocation['agent_2'] >= allocation['agent_3']


class TestSpecializedAgents:
    """Test suite for specialized agent implementations"""
    
    @pytest.fixture
    def mock_config(self):
        return MockConfigManager()
    
    @pytest.fixture
    def planner_agent(self, mock_config):
        return ResourceAwarePlannerAgent("planner_test", 2000, mock_config)
    
    @pytest.fixture
    def executor_agent(self, mock_config):
        return ResourceAwareExecutorAgent("executor_test", 2000, mock_config)
    
    @pytest.fixture
    def critic_agent(self, mock_config):
        return ResourceAwareCriticAgent("critic_test", 2000, mock_config)
    
    @pytest.mark.asyncio
    async def test_planner_agent_execution(self, planner_agent):
        """Test planner agent execution"""
        task = {
            'description': 'Create a web application with user authentication',
            'type': 'planning'
        }
        context = {'complexity': 1.5, 'importance': 0.8}
        
        result = await planner_agent.execute(task, context)
        
        assert 'success' in result
        if result['success']:
            assert 'plan' in result
            assert 'confidence' in result
    
    @pytest.mark.asyncio
    async def test_executor_agent_execution(self, executor_agent):
        """Test executor agent execution"""
        task = {
            'type': 'create_file',
            'file_path': 'test.py',
            'description': 'Create a simple Python script'
        }
        context = {'complexity': 1.0, 'importance': 0.6}
        
        result = await executor_agent.execute(task, context)
        
        assert 'success' in result
        assert 'tokens_used' in result
    
    @pytest.mark.asyncio
    async def test_critic_agent_execution(self, critic_agent):
        """Test critic agent execution"""
        task = {
            'target_artifact': 'test.py',
            'criteria': 'Code quality and best practices',
            'evaluation_type': 'code_review'
        }
        context = {'complexity': 1.2, 'importance': 0.7}
        
        result = await critic_agent.execute(task, context)
        
        assert 'success' in result
        if result['success']:
            assert 'quality_score' in result
            assert 'issues_found' in result
            assert 'recommendations' in result
    
    def test_planner_cost_estimation(self, planner_agent):
        """Test planner token cost estimation"""
        task = {'description': 'Complex multi-component system'}
        context = {'complexity': 2.0}
        
        cost = planner_agent._estimate_planning_cost(task, context)
        
        assert isinstance(cost, int)
        assert cost > 0
    
    def test_executor_model_tier_selection(self, executor_agent):
        """Test executor model tier selection"""
        task = {'type': 'create_file', 'complexity': 2.0}
        context = {'complexity': 2.0, 'importance': 0.9}
        
        tier = executor_agent._select_optimal_model_tier(task, context)
        
        assert isinstance(tier, ModelTier)
    
    def test_critic_depth_level_selection(self, critic_agent):
        """Test critic depth level selection"""
        context = {'importance': 0.9, 'complexity': 1.5}
        
        depth = critic_agent._select_optimal_depth_level(context)
        
        assert depth in ['surface', 'moderate', 'deep']


class TestMultiAgentSystemOrchestrator:
    """Test suite for MAS orchestrator"""
    
    @pytest.fixture
    def mock_config(self):
        return MockConfigManager()
    
    @pytest.fixture
    def mas_orchestrator(self, mock_config):
        return MultiAgentSystemOrchestrator(
            total_system_budget=10000,
            config_manager=mock_config
        )
    
    @pytest.mark.asyncio
    async def test_mas_initialization(self, mas_orchestrator):
        """Test MAS orchestrator initialization"""
        assert mas_orchestrator.total_system_budget == 10000
        assert len(mas_orchestrator.agents) == 0
        assert mas_orchestrator.system_metrics.total_agents == 0
    
    @pytest.mark.asyncio
    async def test_default_agent_initialization(self, mas_orchestrator):
        """Test default agent initialization"""
        agent_ids = await mas_orchestrator.initialize_default_agents()
        
        assert len(agent_ids) == 3
        assert 'planner' in agent_ids
        assert 'executor' in agent_ids
        assert 'critic' in agent_ids
        assert len(mas_orchestrator.agents) == 3
    
    @pytest.mark.asyncio
    async def test_task_submission_and_processing(self, mas_orchestrator):
        """Test task submission and processing"""
        # Initialize agents
        await mas_orchestrator.initialize_default_agents()
        
        # Submit tasks
        task1_id = await mas_orchestrator.submit_task({
            'description': 'Create main application file',
            'type': 'create_file',
            'complexity': 1.0
        }, priority=0.8)
        
        task2_id = await mas_orchestrator.submit_task({
            'description': 'Implement user authentication',
            'type': 'planning',
            'complexity': 1.5
        }, priority=0.9)
        
        assert len(mas_orchestrator.task_queue) == 2
        
        # Process tasks
        result = await mas_orchestrator.process_task_queue()
        
        assert result['status'] == 'completed'
        assert result['processed'] == 2
        assert len(mas_orchestrator.task_queue) == 0
    
    def test_optimal_agent_selection(self, mas_orchestrator):
        """Test optimal agent selection logic"""
        # Add mock agents
        agents = {
            'planner': TestableResourceAwareAgent('planner', 'resource_aware_planner', 1000),
            'executor': TestableResourceAwareAgent('executor', 'resource_aware_executor', 1000),
            'critic': TestableResourceAwareAgent('critic', 'resource_aware_critic', 1000)
        }
        
        for agent in agents.values():
            mas_orchestrator.agents[agent.agent_id] = agent
            mas_orchestrator.agent_roles[agent.agent_id] = agent.role
        
        # Test selection for different task types
        planning_task = {'type': 'planning', 'complexity': 1.0}
        selected = asyncio.run(mas_orchestrator._select_optimal_agent(planning_task, 0.5))
        assert selected == 'planner'
        
        execution_task = {'type': 'create_file', 'complexity': 1.0}
        selected = asyncio.run(mas_orchestrator._select_optimal_agent(execution_task, 0.5))
        assert selected in ['executor', 'planner']  # Both could be valid
    
    def test_system_metrics_update(self, mas_orchestrator):
        """Test system metrics updating"""
        # Add mock completed tasks
        mas_orchestrator.completed_tasks = [
            {'task_id': 'task1', 'result': {'success': True}},
            {'task_id': 'task2', 'result': {'success': True}},
        ]
        mas_orchestrator.failed_tasks = [
            {'task_id': 'task3', 'result': {'success': False}},
        ]
        
        # Add mock agents
        for i in range(3):
            agent = TestableResourceAwareAgent(f'agent_{i}', f'role_{i}', 1000)
            agent.allocation.consumed = 300 + (i * 100)
            mas_orchestrator.agents[agent.agent_id] = agent
        
        asyncio.run(mas_orchestrator._update_system_metrics())
        
        assert mas_orchestrator.system_metrics.total_tasks_completed == 2
        assert mas_orchestrator.system_metrics.overall_success_rate == 2/3  # 2 success out of 3 total
        assert mas_orchestrator.system_metrics.resource_utilization_efficiency > 0


class TestEmergentBehaviorDetection:
    """Test suite for emergent behavior detection"""
    
    @pytest.fixture
    def behavior_detector(self):
        return EmergentBehaviorDetector()
    
    @pytest.fixture
    def network_analyzer(self):
        return NetworkAnalyzer()
    
    @pytest.fixture
    def mock_agents(self):
        agents = {}
        for i in range(4):
            agent = TestableResourceAwareAgent(f'agent_{i}', f'role_{i}', 1000)
            # Add mock execution history
            for j in range(10):
                agent.execution_history.append({
                    'timestamp': datetime.now(),
                    'task_type': f'type_{j % 3}',
                    'success': j % 2 == 0,
                    'efficiency': 0.5 + (j * 0.05),
                    'strategy': f'strategy_{j % 2}'
                })
            agents[agent.agent_id] = agent
        return agents
    
    def test_network_structure_analysis(self, network_analyzer):
        """Test network structure analysis"""
        # Record some interactions
        agents = ['agent_1', 'agent_2', 'agent_3', 'agent_4']
        
        # Create a network with some structure
        network_analyzer.record_interaction('agent_1', 'agent_2', 'collaboration', 0.8)
        network_analyzer.record_interaction('agent_1', 'agent_3', 'collaboration', 0.6)
        network_analyzer.record_interaction('agent_2', 'agent_3', 'collaboration', 0.7)
        network_analyzer.record_interaction('agent_3', 'agent_4', 'collaboration', 0.5)
        
        metrics = network_analyzer.analyze_network_structure(agents)
        
        assert 'network_density' in metrics
        assert 'clustering_coefficient' in metrics
        assert 'centrality_scores' in metrics
        assert 0.0 <= metrics['network_density'] <= 1.0
        assert 0.0 <= metrics['clustering_coefficient'] <= 1.0
    
    def test_collaborative_clustering_detection(self, behavior_detector, network_analyzer, mock_agents):
        """Test collaborative clustering detection"""
        # Set up network with high clustering
        agents_list = list(mock_agents.keys())
        for i in range(len(agents_list)):
            for j in range(i+1, len(agents_list)):
                if i < 2 and j < 3:  # Create a cluster
                    network_analyzer.record_interaction(agents_list[i], agents_list[j], 'collaboration', 0.9)
        
        behavior = behavior_detector._detect_collaborative_clustering(mock_agents, network_analyzer)
        
        # May or may not detect clustering depending on threshold
        if behavior:
            assert behavior.behavior_type.value == 'collaborative_clustering'
            assert behavior.pattern_strength > 0
    
    def test_specialization_drift_detection(self, behavior_detector, mock_agents):
        """Test specialization drift detection"""
        # Modify agent history to show specialization
        agent = list(mock_agents.values())[0]
        agent.execution_history = []
        
        # Add specialized task history (all same type)
        for i in range(10):
            agent.execution_history.append({
                'timestamp': datetime.now(),
                'task_type': 'specialized_type',  # All same type
                'success': True,
                'efficiency': 0.8
            })
        
        behavior = behavior_detector._detect_specialization_drift(mock_agents)
        
        if behavior:
            assert behavior.behavior_type.value == 'specialization_drift'
            assert len(behavior.involved_agents) > 0
    
    def test_adaptive_strategies_detection(self, behavior_detector, mock_agents):
        """Test adaptive strategies detection"""
        # Modify agent to show strategy adaptation
        agent = list(mock_agents.values())[0]
        agent.execution_history = []
        
        # Add diverse strategy history
        strategies = ['strategy_A', 'strategy_B', 'strategy_C', 'strategy_D']
        for i in range(12):
            agent.execution_history.append({
                'timestamp': datetime.now(),
                'task_type': 'generic',
                'success': True,
                'efficiency': 0.7,
                'strategy': strategies[i % len(strategies)]
            })
        
        behavior = behavior_detector._detect_adaptive_strategies(mock_agents)
        
        if behavior:
            assert behavior.behavior_type.value == 'adaptive_strategies'
            assert agent.agent_id in behavior.involved_agents


class TestHybridIntegration:
    """Test suite for hybrid integration with existing architecture"""
    
    @pytest.fixture
    def mock_config(self):
        return MockConfigManager()
    
    @pytest.fixture
    def mock_project_context(self):
        """Create a mock project context"""
        class MockProjectContext:
            def __init__(self):
                self.project_id = "test_project_123"
                self.project_goal = "Create a web application with user authentication and dashboard"
                self.workspace_path = Path("/tmp/test_workspace")
        
        return MockProjectContext()
    
    def test_hybrid_orchestrator_initialization(self, mock_project_context, mock_config):
        """Test hybrid orchestrator initialization"""
        hybrid = HybridOrchestrator(
            project_context=mock_project_context,
            config_manager=mock_config,
            mode="adaptive"
        )
        
        assert hybrid.mode == "adaptive"
        assert hybrid.total_token_budget > 0
    
    def test_project_complexity_assessment(self, mock_project_context, mock_config):
        """Test project complexity assessment"""
        hybrid = HybridOrchestrator(
            project_context=mock_project_context,
            config_manager=mock_config,
            mode="adaptive"
        )
        
        complexity = hybrid._assess_project_complexity()
        
        assert 0.0 <= complexity <= 1.0
        assert isinstance(complexity, float)
    
    def test_mode_selection_logic(self, mock_project_context, mock_config):
        """Test mode selection logic"""
        hybrid = HybridOrchestrator(
            project_context=mock_project_context,
            config_manager=mock_config,
            mode="adaptive"
        )
        
        # Mock both orchestrators as available
        hybrid.legacy_orchestrator = "mock_legacy"
        hybrid.mas_orchestrator = "mock_mas"
        
        selected_mode = hybrid._select_optimal_mode()
        
        assert selected_mode in ["legacy", "mas"]
    
    @pytest.mark.asyncio
    async def test_mode_switching(self, mock_project_context, mock_config):
        """Test runtime mode switching"""
        hybrid = HybridOrchestrator(
            project_context=mock_project_context,
            config_manager=mock_config,
            mode="legacy"
        )
        
        result = await hybrid.switch_mode("mas")
        
        assert result['success']
        assert result['old_mode'] == "legacy"
        assert result['new_mode'] == "mas"
        assert hybrid.mode == "mas"


class TestTaskConverter:
    """Test suite for task conversion between formats"""
    
    def test_resource_aware_to_legacy_conversion(self):
        """Test conversion from resource-aware to legacy format"""
        ra_task = {
            'id': 'test_task_001',
            'description': 'Test task description',
            'type': 'create_file',
            'priority': 0.8,
            'complexity': 1.5,
            'dependencies': ['dep1', 'dep2']
        }
        
        legacy_task = ResourceAwareTaskConverter.resource_aware_to_legacy(ra_task)
        
        assert legacy_task.task_id == 'test_task_001'
        assert legacy_task.description == 'Test task description'
        assert legacy_task.dependencies == ['dep1', 'dep2']
    
    def test_legacy_to_resource_aware_conversion(self):
        """Test conversion from legacy to resource-aware format"""
        from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus
        
        legacy_task = Task(
            task_id='legacy_001',
            task_type=TaskType.CREATE_FILE,
            description='Legacy task description',
            status=TaskStatus.PENDING,
            dependencies=['legacy_dep']
        )
        
        ra_task = ResourceAwareTaskConverter.legacy_to_resource_aware(legacy_task)
        
        assert ra_task['id'] == 'legacy_001'
        assert ra_task['description'] == 'Legacy task description'
        assert ra_task['type'] == 'CREATE_FILE'
        assert ra_task['dependencies'] == ['legacy_dep']


class TestPerformanceMonitoring:
    """Test suite for performance monitoring and comparison"""
    
    @pytest.fixture
    def performance_monitor(self):
        return PerformanceMonitor()
    
    def test_performance_recording(self, performance_monitor):
        """Test performance data recording"""
        performance_monitor.record_execution(
            mode='legacy',
            execution_time=2.5,
            success=True,
            tokens_used=300,
            additional_metrics={'complexity': 1.5}
        )
        
        assert len(performance_monitor.performance_data['legacy']) == 1
        record = performance_monitor.performance_data['legacy'][0]
        assert record['execution_time'] == 2.5
        assert record['success'] == True
        assert record['tokens_used'] == 300
    
    def test_performance_analysis(self, performance_monitor):
        """Test performance analysis"""
        # Record some legacy performance data
        for i in range(5):
            performance_monitor.record_execution(
                mode='legacy',
                execution_time=2.0 + (i * 0.1),
                success=i < 4,  # 4/5 success rate
                tokens_used=300 + (i * 10)
            )
        
        # Record some MAS performance data
        for i in range(5):
            performance_monitor.record_execution(
                mode='mas',
                execution_time=1.8 + (i * 0.1),
                success=i < 5,  # 5/5 success rate
                tokens_used=280 + (i * 15)
            )
        
        analysis = performance_monitor.analyze_performance()
        
        assert 'legacy' in analysis
        assert 'mas' in analysis
        assert 'comparison' in analysis
        
        assert analysis['legacy']['success_rate'] == 0.8
        assert analysis['mas']['success_rate'] == 1.0
        assert analysis['comparison']['success_rate_improvement'] == 0.2
    
    def test_recommendations_generation(self, performance_monitor):
        """Test performance-based recommendations"""
        # Add some contrasting performance data
        for i in range(3):
            performance_monitor.record_execution('legacy', 3.0, True, 400)
            performance_monitor.record_execution('mas', 2.0, True, 300)
        
        recommendations = performance_monitor.get_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)


# Integration and System Tests
class TestSystemIntegration:
    """End-to-end system integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_mas_workflow(self):
        """Test complete MAS workflow from initialization to task completion"""
        config = MockConfigManager()
        
        # Initialize MAS orchestrator
        mas = MultiAgentSystemOrchestrator(
            total_system_budget=5000,
            config_manager=config
        )
        
        # Initialize default agents
        agent_ids = await mas.initialize_default_agents()
        assert len(agent_ids) == 3
        
        # Submit various types of tasks
        tasks = [
            {
                'description': 'Plan application architecture',
                'type': 'planning',
                'complexity': 2.0
            },
            {
                'description': 'Create main.py file',
                'type': 'create_file',
                'complexity': 1.0
            },
            {
                'description': 'Validate code quality',
                'type': 'validate_artifact',
                'complexity': 1.5
            }
        ]
        
        task_ids = []
        for task in tasks:
            task_id = await mas.submit_task(task, priority=0.7)
            task_ids.append(task_id)
        
        # Process all tasks
        result = await mas.process_task_queue()
        
        assert result['status'] == 'completed'
        assert result['processed'] == 3
        
        # Check system status
        status = mas.get_system_status()
        assert status['system_metrics']['total_agents'] == 3
        assert status['system_metrics']['total_tasks_completed'] > 0
    
    @pytest.mark.asyncio
    async def test_resource_optimization_under_pressure(self):
        """Test system behavior under resource pressure"""
        config = MockConfigManager()
        
        # Create system with limited budget
        mas = MultiAgentSystemOrchestrator(
            total_system_budget=1000,  # Very limited
            config_manager=config
        )
        
        await mas.initialize_default_agents()
        
        # Submit many tasks to create resource pressure
        for i in range(10):
            await mas.submit_task({
                'description': f'Task {i}',
                'type': 'generic',
                'complexity': 1.5
            }, priority=0.5)
        
        # Process tasks
        result = await mas.process_task_queue()
        
        # System should handle resource constraints gracefully
        assert result['status'] == 'completed'
        assert result['processed'] <= 10  # May not complete all due to budget constraints
    
    @pytest.mark.asyncio
    async def test_emergent_behavior_emergence(self):
        """Test emergence of collaborative behaviors over time"""
        config = MockConfigManager()
        mas = MultiAgentSystemOrchestrator(
            total_system_budget=10000,
            config_manager=config
        )
        
        await mas.initialize_default_agents()
        
        # Submit multiple rounds of tasks to encourage collaboration
        for round_num in range(3):
            for i in range(5):
                await mas.submit_task({
                    'description': f'Round {round_num} Task {i}',
                    'type': 'planning' if i % 3 == 0 else 'execution',
                    'complexity': 1.0 + (i * 0.2)
                }, priority=0.6)
            
            # Process each round
            await mas.process_task_queue()
        
        # Check for emergent behaviors
        status = mas.get_system_status()
        emergent_behaviors = status.get('emergent_behaviors', [])
        
        # May or may not detect behaviors depending on implementation
        # This tests that the system can handle the analysis without errors
        assert isinstance(emergent_behaviors, list)


def run_performance_benchmark():
    """Run performance benchmark comparing different strategies"""
    
    async def benchmark_strategy(strategy: AllocationStrategy, num_tasks: int = 20):
        config = MockConfigManager()
        optimizer = DynamicResourceOptimizer(
            total_budget=10000,
            strategy=strategy
        )
        
        # Create test agents
        agents = []
        for i in range(3):
            agent = TestableResourceAwareAgent(f'agent_{i}', f'role_{i}', 2000)
            agent.performance_metrics.success_rate = 0.7 + (i * 0.1)
            agents.append(agent)
            optimizer.register_agent(agent)
        
        # Create demands
        demands = []
        for i in range(num_tasks):
            demand = ResourceDemand(
                agent_id=agents[i % len(agents)].agent_id,
                requested_tokens=200 + (i * 10),
                task_priority=0.5 + (i * 0.02),
                expected_utility=1.0 + (i * 0.05)
            )
            demands.append(demand)
        
        # Measure allocation time
        start_time = time.time()
        decisions = await optimizer.optimize_allocation(demands)
        allocation_time = time.time() - start_time
        
        # Calculate metrics
        total_allocated = sum(d.allocated_tokens for d in decisions)
        avg_allocation_ratio = sum(d.allocation_ratio for d in decisions) / len(decisions)
        total_expected_roi = sum(d.expected_roi for d in decisions)
        
        return {
            'strategy': strategy.value,
            'allocation_time': allocation_time,
            'total_allocated': total_allocated,
            'avg_allocation_ratio': avg_allocation_ratio,
            'total_expected_roi': total_expected_roi,
            'num_decisions': len(decisions)
        }
    
    async def run_benchmarks():
        strategies = [
            AllocationStrategy.FAIR_SHARE,
            AllocationStrategy.PERFORMANCE_BASED,
            AllocationStrategy.UTILITY_MAXIMIZING,
            AllocationStrategy.RISK_ADJUSTED
        ]
        
        results = []
        for strategy in strategies:
            result = await benchmark_strategy(strategy)
            results.append(result)
            logger.info(f"Strategy {strategy.value}: "
                       f"Time={result['allocation_time']:.3f}s, "
                       f"ROI={result['total_expected_roi']:.2f}")
        
        return results
    
    return asyncio.run(run_benchmarks())


def main():
    """Run all tests and benchmarks"""
    logger.info("Starting EVOLUX MAS comprehensive test suite")
    
    # Run pytest
    logger.info("Running unit tests...")
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        logger.info("All unit tests passed!")
        
        # Run performance benchmark
        logger.info("Running performance benchmarks...")
        try:
            benchmark_results = run_performance_benchmark()
            logger.info("Performance benchmark completed successfully")
            
            # Print benchmark summary
            print("\n" + "="*60)
            print("PERFORMANCE BENCHMARK RESULTS")
            print("="*60)
            for result in benchmark_results:
                print(f"Strategy: {result['strategy']}")
                print(f"  Allocation Time: {result['allocation_time']:.3f}s")
                print(f"  Total Expected ROI: {result['total_expected_roi']:.2f}")
                print(f"  Avg Allocation Ratio: {result['avg_allocation_ratio']:.3f}")
                print()
            
        except Exception as e:
            logger.error(f"Performance benchmark failed: {str(e)}")
            exit_code = 1
    
    else:
        logger.error("Some tests failed!")
    
    return exit_code


if __name__ == "__main__":
    exit(main())