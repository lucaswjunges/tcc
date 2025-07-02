#!/usr/bin/env python3
"""
EVOLUX Multi-Agent System Demonstration

This script demonstrates the advanced resource-constrained multi-agent system
capabilities, including emergent behavior detection, adaptive resource optimization,
and intelligent collaboration patterns.
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.core.mas_orchestrator import MultiAgentSystemOrchestrator
from evolux_engine.core.evolux_mas_integration import HybridOrchestrator, PerformanceMonitor
from evolux_engine.core.resource_optimizer import AllocationStrategy
from evolux_engine.core.specialized_agents import (
    ResourceAwarePlannerAgent,
    ResourceAwareExecutorAgent, 
    ResourceAwareCriticAgent
)

logger = get_structured_logger("evolux_mas_demo")


class DemoProjectContext:
    """Mock project context for demonstration"""
    
    def __init__(self, goal: str):
        self.project_id = f"demo_{int(time.time())}"
        self.project_goal = goal
        self.workspace_path = Path(f"/tmp/evolux_demo_{self.project_id}")


class DemoScenarios:
    """Collection of demonstration scenarios"""
    
    @staticmethod
    def get_simple_web_app_scenario() -> Dict[str, Any]:
        """Simple web application development scenario"""
        return {
            'name': 'Simple Web Application',
            'goal': 'Create a Flask web application with user authentication, dashboard, and basic CRUD operations',
            'complexity': 1.5,
            'expected_tasks': [
                {'type': 'planning', 'description': 'Design application architecture'},
                {'type': 'create_file', 'description': 'Create main Flask application'},
                {'type': 'create_file', 'description': 'Implement user authentication'},
                {'type': 'create_file', 'description': 'Create dashboard templates'},
                {'type': 'validate_artifact', 'description': 'Validate application structure'}
            ]
        }
    
    @staticmethod
    def get_ai_service_scenario() -> Dict[str, Any]:
        """AI microservice development scenario"""
        return {
            'name': 'AI Microservice',
            'goal': 'Develop a machine learning microservice with REST API, model training pipeline, and monitoring',
            'complexity': 2.5,
            'expected_tasks': [
                {'type': 'planning', 'description': 'Design ML pipeline architecture'},
                {'type': 'create_file', 'description': 'Implement model training module'},
                {'type': 'create_file', 'description': 'Create REST API endpoints'},
                {'type': 'create_file', 'description': 'Add monitoring and logging'},
                {'type': 'validate_artifact', 'description': 'Performance and quality validation'}
            ]
        }
    
    @staticmethod
    def get_resource_constrained_scenario() -> Dict[str, Any]:
        """Resource-constrained development scenario"""
        return {
            'name': 'Resource Constrained Development',
            'goal': 'Build a distributed system with microservices, database, caching, and monitoring under strict resource limits',
            'complexity': 3.0,
            'token_budget': 2000,  # Very limited budget
            'expected_tasks': [
                {'type': 'planning', 'description': 'Design distributed architecture'},
                {'type': 'create_file', 'description': 'Implement core microservices'},
                {'type': 'create_file', 'description': 'Setup database schemas'},
                {'type': 'create_file', 'description': 'Configure caching layer'},
                {'type': 'create_file', 'description': 'Add monitoring and alerts'},
                {'type': 'validate_artifact', 'description': 'System integration validation'}
            ]
        }


async def demonstrate_basic_mas_functionality():
    """Demonstrate basic MAS functionality with resource optimization"""
    
    print("\n" + "="*80)
    print("🤖 EVOLUX MAS BASIC FUNCTIONALITY DEMONSTRATION")
    print("="*80)
    
    # Mock configuration for demo
    class DemoConfig:
        def get_global_setting(self, key, default=None):
            return {"default_llm_provider": "demo", "token_budget_multiplier": 1.0}.get(key, default)
        
        def get_api_key(self, provider):
            return "demo_key"
        
        def get_default_model_for(self, role):
            return "demo-model"
    
    config = DemoConfig()
    
    # Initialize MAS with token budget
    print("🚀 Initializing Multi-Agent System...")
    mas = MultiAgentSystemOrchestrator(
        total_system_budget=5000,
        config_manager=config
    )
    
    # Initialize default agents
    print("👥 Creating specialized agents...")
    agent_ids = await mas.initialize_default_agents()
    print(f"   ✅ Created agents: {list(agent_ids.keys())}")
    
    # Display initial system status
    status = mas.get_system_status()
    print(f"   📊 System Status:")
    print(f"      - Total Agents: {status['system_metrics']['total_agents']}")
    print(f"      - Available Budget: {mas.resource_optimizer.available_budget} tokens")
    
    # Get scenario
    scenario = DemoScenarios.get_simple_web_app_scenario()
    print(f"\n🎯 Running Scenario: {scenario['name']}")
    print(f"   Goal: {scenario['goal']}")
    
    # Submit tasks based on scenario
    print("\n📝 Submitting tasks to the system...")
    task_ids = []
    for i, task_info in enumerate(scenario['expected_tasks']):
        task = {
            'description': task_info['description'],
            'type': task_info['type'],
            'complexity': scenario['complexity'] * (0.8 + i * 0.1)  # Varying complexity
        }
        
        priority = 0.9 - (i * 0.1)  # Decreasing priority
        task_id = await mas.submit_task(task, priority=priority)
        task_ids.append(task_id)
        print(f"   ✅ Submitted: {task['description']} (Priority: {priority:.1f})")
    
    # Process tasks
    print(f"\n⚙️  Processing {len(task_ids)} tasks...")
    start_time = time.time()
    
    processing_result = await mas.process_task_queue()
    
    processing_time = time.time() - start_time
    
    # Display results
    print(f"\n📈 Processing Results:")
    print(f"   ⏱️  Processing Time: {processing_time:.2f} seconds")
    print(f"   ✅ Successful Tasks: {processing_result.get('successful', 0)}")
    print(f"   ❌ Failed Tasks: {processing_result.get('failed', 0)}")
    print(f"   📊 Total Processed: {processing_result.get('processed', 0)}")
    
    # Get final system status
    final_status = mas.get_system_status()
    print(f"\n🎯 Final System Metrics:")
    metrics = final_status['system_metrics']
    print(f"   🎯 Overall Success Rate: {metrics['overall_success_rate']:.3f}")
    print(f"   ⚡ Resource Efficiency: {metrics['resource_utilization_efficiency']:.3f}")
    print(f"   🤝 Collaboration Frequency: {metrics['collaboration_frequency']:.3f}")
    print(f"   🧠 Collective Intelligence: {metrics['collective_intelligence_score']:.3f}")
    
    # Display emergent behaviors
    emergent_behaviors = final_status.get('emergent_behaviors', [])
    if emergent_behaviors:
        print(f"\n🌟 Emergent Behaviors Detected: {len(emergent_behaviors)}")
        for behavior in emergent_behaviors[-3:]:  # Show last 3
            print(f"   🔍 {behavior['type']}: {behavior['description']}")
            print(f"      Strength: {behavior['strength']:.3f}, Agents: {behavior['agents']}")
    else:
        print(f"\n🌟 No emergent behaviors detected in this run")
    
    return processing_result


async def demonstrate_resource_optimization_strategies():
    """Demonstrate different resource allocation strategies"""
    
    print("\n" + "="*80)
    print("💰 RESOURCE OPTIMIZATION STRATEGIES DEMONSTRATION")
    print("="*80)
    
    from evolux_engine.core.resource_optimizer import DynamicResourceOptimizer, ResourceDemand
    
    strategies = [
        AllocationStrategy.FAIR_SHARE,
        AllocationStrategy.PERFORMANCE_BASED,
        AllocationStrategy.UTILITY_MAXIMIZING,
        AllocationStrategy.RISK_ADJUSTED
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n🔧 Testing {strategy.value.replace('_', ' ').title()} Strategy...")
        
        # Create optimizer with strategy
        optimizer = DynamicResourceOptimizer(
            total_budget=3000,
            strategy=strategy
        )
        
        # Create mock agents with different characteristics
        from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier
        
        class MockAgent(ResourceAwareAgent):
            async def execute(self, task, context):
                return {'success': True, 'mock': True}
        
        agents = []
        for i in range(3):
            agent = MockAgent(
                agent_id=f"agent_{i}",
                role=f"role_{i}",
                initial_token_budget=800,
                model_tier=ModelTier.BALANCED
            )
            # Simulate different performance levels
            agent.performance_metrics.success_rate = 0.6 + (i * 0.15)
            agent.allocation.efficiency_score = 0.5 + (i * 0.2)
            agents.append(agent)
            optimizer.register_agent(agent)
        
        # Create resource demands
        demands = [
            ResourceDemand(
                agent_id="agent_0",
                requested_tokens=500,
                task_priority=0.8,
                expected_utility=1.5,
                risk_level=0.3
            ),
            ResourceDemand(
                agent_id="agent_1", 
                requested_tokens=600,
                task_priority=0.6,
                expected_utility=2.0,
                risk_level=0.5
            ),
            ResourceDemand(
                agent_id="agent_2",
                requested_tokens=400,
                task_priority=0.9,
                expected_utility=1.2,
                risk_level=0.2
            )
        ]
        
        # Execute allocation
        start_time = time.time()
        decisions = await optimizer.optimize_allocation(demands)
        allocation_time = time.time() - start_time
        
        # Analyze results
        total_allocated = sum(d.allocated_tokens for d in decisions)
        total_roi = sum(d.expected_roi for d in decisions)
        avg_ratio = sum(d.allocation_ratio for d in decisions) / len(decisions)
        
        results[strategy.value] = {
            'total_allocated': total_allocated,
            'total_roi': total_roi,
            'avg_allocation_ratio': avg_ratio,
            'allocation_time': allocation_time,
            'decisions': len(decisions)
        }
        
        print(f"   📊 Results:")
        print(f"      - Total Allocated: {total_allocated} tokens")
        print(f"      - Expected ROI: {total_roi:.2f}")
        print(f"      - Avg Allocation Ratio: {avg_ratio:.3f}")
        print(f"      - Allocation Time: {allocation_time:.4f}s")
    
    # Compare strategies
    print(f"\n📈 Strategy Comparison:")
    print(f"{'Strategy':<20} {'ROI':<8} {'Ratio':<8} {'Time':<8}")
    print("-" * 50)
    
    for strategy, result in results.items():
        strategy_name = strategy.replace('_', ' ').title()[:18]
        print(f"{strategy_name:<20} {result['total_roi']:<8.2f} "
              f"{result['avg_allocation_ratio']:<8.3f} {result['allocation_time']:<8.4f}")
    
    return results


async def demonstrate_emergent_behavior_detection():
    """Demonstrate emergent behavior detection capabilities"""
    
    print("\n" + "="*80)
    print("🌟 EMERGENT BEHAVIOR DETECTION DEMONSTRATION")
    print("="*80)
    
    from evolux_engine.core.mas_orchestrator import NetworkAnalyzer, EmergentBehaviorDetector
    from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier
    
    # Create network analyzer and behavior detector
    network_analyzer = NetworkAnalyzer()
    behavior_detector = EmergentBehaviorDetector()
    
    # Create mock agents with collaboration history
    class MockCollaborativeAgent(ResourceAwareAgent):
        async def execute(self, task, context):
            return {'success': True, 'collaborative': True}
    
    agents = {}
    for i in range(5):
        agent = MockCollaborativeAgent(
            agent_id=f"agent_{i}",
            role=f"specialist_{i % 3}",  # 3 different specializations
            initial_token_budget=1000,
            model_tier=ModelTier.BALANCED
        )
        
        # Simulate execution history showing specialization
        specialization_type = f"task_type_{i % 3}"
        for j in range(15):
            agent.execution_history.append({
                'timestamp': datetime.now(),
                'task_type': specialization_type if j > 5 else f"task_type_{j % 5}",  # Gradual specialization
                'success': True,
                'efficiency': 0.6 + (j * 0.02),
                'strategy': f"strategy_{j % 4 if j < 10 else i % 2}"  # Strategy adaptation
            })
        
        agents[agent.agent_id] = agent
    
    print("👥 Created 5 agents with simulated collaboration history")
    
    # Simulate network interactions
    print("🌐 Simulating agent interactions...")
    agent_ids = list(agents.keys())
    
    # Create collaboration clusters
    # Cluster 1: agents 0, 1, 2
    for i in range(3):
        for j in range(i+1, 3):
            network_analyzer.record_interaction(
                agent_ids[i], agent_ids[j], 'collaboration', 0.8
            )
    
    # Cluster 2: agents 2, 3, 4 (agent 2 bridges clusters)
    for i in range(2, 5):
        for j in range(i+1, 5):
            network_analyzer.record_interaction(
                agent_ids[i], agent_ids[j], 'collaboration', 0.7
            )
    
    # Some random interactions
    network_analyzer.record_interaction(agent_ids[0], agent_ids[4], 'collaboration', 0.3)
    network_analyzer.record_interaction(agent_ids[1], agent_ids[3], 'collaboration', 0.4)
    
    # Analyze network structure
    print("🔍 Analyzing network structure...")
    network_metrics = network_analyzer.analyze_network_structure(agent_ids)
    
    print(f"   📊 Network Metrics:")
    print(f"      - Network Density: {network_metrics['network_density']:.3f}")
    print(f"      - Clustering Coefficient: {network_metrics['clustering_coefficient']:.3f}")
    print(f"      - Connected Components: {network_metrics['num_connected_components']}")
    print(f"      - Average Path Length: {network_metrics['average_path_length']:.2f}")
    
    # Display centrality scores
    print(f"   🎯 Agent Centrality Scores:")
    for agent_id, score in network_metrics['centrality_scores'].items():
        print(f"      - {agent_id}: {score:.3f}")
    
    # Detect emergent behaviors
    print(f"\n🔍 Detecting emergent behaviors...")
    
    # Mock system metrics
    from evolux_engine.core.mas_orchestrator import SystemMetrics
    system_metrics = SystemMetrics(
        total_agents=5,
        total_tasks_completed=50,
        overall_success_rate=0.85,
        resource_utilization_efficiency=0.75,
        collaboration_frequency=0.6,
        emergent_behaviors_detected=0,
        system_adaptation_rate=0.4,
        collective_intelligence_score=0.8
    )
    
    behaviors = behavior_detector.detect_emergent_behaviors(
        agents, network_analyzer, system_metrics
    )
    
    if behaviors:
        print(f"🌟 Detected {len(behaviors)} emergent behaviors:")
        for behavior in behaviors:
            print(f"\n   🔍 {behavior.behavior_type.value.replace('_', ' ').title()}:")
            print(f"      - Strength: {behavior.pattern_strength:.3f}")
            print(f"      - Involved Agents: {behavior.involved_agents}")
            print(f"      - Description: {behavior.description}")
            print(f"      - Performance Impact: {behavior.performance_impact:+.3f}")
    else:
        print("🌟 No emergent behaviors detected with current thresholds")
    
    return behaviors


async def demonstrate_hybrid_integration():
    """Demonstrate hybrid integration with existing architecture"""
    
    print("\n" + "="*80)
    print("🔄 HYBRID INTEGRATION DEMONSTRATION")
    print("="*80)
    
    # Mock configuration
    class DemoConfig:
        def get_global_setting(self, key, default=None):
            settings = {
                "default_llm_provider": "demo",
                "token_budget_multiplier": 1.5
            }
            return settings.get(key, default)
        
        def get_api_key(self, provider):
            return "demo_key"
        
        def get_default_model_for(self, role):
            return "demo-model"
    
    config = DemoConfig()
    
    # Create project context
    scenario = DemoScenarios.get_ai_service_scenario()
    project_context = DemoProjectContext(scenario['goal'])
    
    print(f"🎯 Project: {scenario['name']}")
    print(f"   Goal: {scenario['goal']}")
    print(f"   Complexity: {scenario['complexity']}")
    
    # Initialize hybrid orchestrator in adaptive mode
    print(f"\n🤖 Initializing Hybrid Orchestrator (Adaptive Mode)...")
    hybrid = HybridOrchestrator(
        project_context=project_context,
        config_manager=config,
        mode="adaptive"
    )
    
    print(f"   💰 Token Budget: {hybrid.total_token_budget}")
    print(f"   🧠 Selected Mode: {hybrid.mode}")
    print(f"   📊 Complexity Assessment: {hybrid._assess_project_complexity():.3f}")
    print(f"   🔋 Resource Pressure: {hybrid._assess_resource_pressure():.3f}")
    
    # Show mode selection reasoning
    reasoning = hybrid._get_mode_selection_reason()
    print(f"   🤔 Mode Selection Reason: {reasoning}")
    
    # Demonstrate mode switching
    print(f"\n🔄 Demonstrating mode switching...")
    
    # Try switching to MAS mode
    switch_result = await hybrid.switch_mode("mas")
    if switch_result['success']:
        print(f"   ✅ Successfully switched from {switch_result['old_mode']} to {switch_result['new_mode']}")
    
    # Get system status
    status = await hybrid.get_system_status()
    print(f"\n📊 Hybrid System Status:")
    print(f"   🎯 Current Mode: {status['mode']}")
    print(f"   💰 Token Budget: {status['token_budget']}")
    
    if 'mas_orchestrator' in status and status['mas_orchestrator']['available']:
        mas_metrics = status['mas_orchestrator']['system_status']['system_metrics']
        print(f"   👥 MAS Agents: {mas_metrics['total_agents']}")
        print(f"   🎯 MAS Intelligence Score: {mas_metrics['collective_intelligence_score']:.3f}")
    
    # Run a project cycle
    print(f"\n⚙️  Running project cycle...")
    start_time = time.time()
    
    try:
        cycle_result = await hybrid.run_project_cycle()
        cycle_time = time.time() - start_time
        
        print(f"   ⏱️  Cycle Time: {cycle_time:.2f} seconds")
        print(f"   ✅ Success: {cycle_result.get('success', False)}")
        print(f"   🎯 Selected Mode: {cycle_result.get('selected_mode', 'unknown')}")
        
        if 'tasks_processed' in cycle_result:
            print(f"   📝 Tasks Processed: {cycle_result['tasks_processed']}")
            print(f"   ✅ Tasks Successful: {cycle_result['tasks_successful']}")
            print(f"   ❌ Tasks Failed: {cycle_result['tasks_failed']}")
        
        if 'collective_intelligence_score' in cycle_result:
            print(f"   🧠 Collective Intelligence: {cycle_result['collective_intelligence_score']:.3f}")
        
    except Exception as e:
        print(f"   ❌ Cycle failed: {str(e)}")
    
    return hybrid


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring and comparison"""
    
    print("\n" + "="*80)
    print("📈 PERFORMANCE MONITORING DEMONSTRATION")
    print("="*80)
    
    monitor = PerformanceMonitor()
    
    # Simulate performance data for different modes
    print("📊 Simulating performance data collection...")
    
    # Legacy mode performance (stable but slower)
    print("   🔧 Legacy Mode Performance...")
    for i in range(10):
        monitor.record_execution(
            mode='legacy',
            execution_time=2.5 + (i * 0.1),  # Gradually slower
            success=i < 8,  # 80% success rate
            tokens_used=400 + (i * 20),
            additional_metrics={'complexity': 1.0 + (i * 0.1)}
        )
    
    # MAS mode performance (more variable but better average)
    print("   🤖 MAS Mode Performance...")
    for i in range(10):
        monitor.record_execution(
            mode='mas',
            execution_time=2.0 + (i * 0.05),  # More stable time
            success=i < 9,  # 90% success rate
            tokens_used=350 + (i * 15),  # More efficient
            additional_metrics={'complexity': 1.0 + (i * 0.1), 'collaboration': True}
        )
    
    # Hybrid mode performance (best of both)
    print("   🔄 Hybrid Mode Performance...")
    for i in range(8):
        monitor.record_execution(
            mode='hybrid',
            execution_time=1.8 + (i * 0.03),  # Even better
            success=True,  # 100% success rate (small sample)
            tokens_used=330 + (i * 10),
            additional_metrics={'adaptive': True}
        )
    
    # Analyze performance
    print("\n📈 Performance Analysis Results:")
    analysis = monitor.analyze_performance()
    
    print(f"{'Mode':<10} {'Samples':<8} {'Success':<8} {'Avg Time':<10} {'Avg Tokens':<12} {'Efficiency':<10}")
    print("-" * 70)
    
    for mode, metrics in analysis.items():
        if mode == 'comparison':
            continue
        
        mode_name = mode.title()
        print(f"{mode_name:<10} {metrics['sample_size']:<8} "
              f"{metrics['success_rate']:<8.2f} {metrics['avg_execution_time']:<10.2f} "
              f"{metrics['avg_tokens_used']:<12.1f} {metrics['efficiency_score']:<10.3f}")
    
    # Show comparison if available
    if 'comparison' in analysis:
        comp = analysis['comparison']
        print(f"\n📊 Mode Comparison (MAS vs Legacy):")
        print(f"   ✅ Success Rate Improvement: {comp['success_rate_improvement']:+.2f}")
        print(f"   ⚡ Speed Improvement: {comp['speed_improvement']:+.2f}")
        print(f"   💰 Token Efficiency: {comp['token_efficiency']:+.2f}")
        print(f"   🎯 Overall Improvement: {comp['overall_improvement']:+.2f}")
    
    # Get recommendations
    recommendations = monitor.get_recommendations()
    print(f"\n💡 Performance Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    return analysis


async def main():
    """Main demonstration orchestrator"""
    
    print("🚀 EVOLUX: Autonomous Multi-Agent System with Resource-Constrained Optimization")
    print("=" * 80)
    print("🎯 Demonstrating state-of-the-art Multi-Agent System capabilities")
    print("💰 Treating tokens as finite commodities subject to economic principles")
    print("🌟 Featuring emergent intelligence through collaborative agent interactions")
    print("⚡ With optimal resource utilization efficiency")
    
    demos = [
        ("Basic MAS Functionality", demonstrate_basic_mas_functionality),
        ("Resource Optimization Strategies", demonstrate_resource_optimization_strategies),
        ("Emergent Behavior Detection", demonstrate_emergent_behavior_detection),
        ("Hybrid Integration", demonstrate_hybrid_integration),
        ("Performance Monitoring", demonstrate_performance_monitoring)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*20} Starting {demo_name} {'='*20}")
        
        try:
            start_time = time.time()
            result = await demo_func()
            demo_time = time.time() - start_time
            
            results[demo_name] = {
                'success': True,
                'result': result,
                'execution_time': demo_time
            }
            
            print(f"✅ {demo_name} completed successfully in {demo_time:.2f}s")
            
        except Exception as e:
            print(f"❌ {demo_name} failed: {str(e)}")
            results[demo_name] = {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
        
        # Small delay between demos
        await asyncio.sleep(1)
    
    # Final summary
    print(f"\n" + "="*80)
    print("📋 DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful_demos = [name for name, result in results.items() if result['success']]
    failed_demos = [name for name, result in results.items() if not result['success']]
    
    print(f"✅ Successful Demonstrations: {len(successful_demos)}/{len(demos)}")
    for demo in successful_demos:
        time_taken = results[demo]['execution_time']
        print(f"   ✅ {demo}: {time_taken:.2f}s")
    
    if failed_demos:
        print(f"\n❌ Failed Demonstrations: {len(failed_demos)}")
        for demo in failed_demos:
            error = results[demo]['error']
            print(f"   ❌ {demo}: {error}")
    
    total_time = sum(result['execution_time'] for result in results.values())
    print(f"\n⏱️  Total Demonstration Time: {total_time:.2f} seconds")
    
    print(f"\n🎉 EVOLUX MAS demonstration completed!")
    print(f"🌟 The system demonstrates advanced capabilities in:")
    print(f"   💰 Resource-constrained optimization")
    print(f"   🤝 Intelligent agent collaboration")  
    print(f"   🌟 Emergent behavior detection")
    print(f"   🧠 Adaptive decision making")
    print(f"   ⚡ Performance optimization")
    
    return results


if __name__ == "__main__":
    # Run the complete demonstration
    try:
        results = asyncio.run(main())
        
        # Save results to file
        results_file = Path("evolux_mas_demo_results.json")
        with open(results_file, 'w') as f:
            # Convert non-serializable objects to strings
            serializable_results = {}
            for demo_name, result in results.items():
                serializable_results[demo_name] = {
                    'success': result['success'],
                    'execution_time': result['execution_time'],
                    'error': result.get('error', None)
                }
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Demo results saved to: {results_file}")
        
        # Exit with appropriate code
        if all(result['success'] for result in results.values()):
            print("🎉 All demonstrations completed successfully!")
            sys.exit(0)
        else:
            print("⚠️  Some demonstrations failed. Check the output above for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Demonstration interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Demonstration failed with unexpected error: {str(e)}")
        sys.exit(1)