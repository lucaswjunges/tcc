"""
Integration Layer for EVOLUX Multi-Agent System with Existing Architecture

This module provides seamless integration between the new resource-aware multi-agent
system and the existing Evolux Engine architecture, maintaining backward compatibility
while enabling advanced resource optimization and emergent behavior capabilities.
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime
import json

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import (
    Task, TaskType, TaskStatus, ProjectStatus, ExecutionResult, ValidationResult,
    ProjectContext, LLMCallMetrics
)
from evolux_engine.models.project_context import ProjectContext as LegacyProjectContext
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.services.advanced_context_manager import AdvancedContextManager

# New MAS components
from evolux_engine.core.mas_orchestrator import MultiAgentSystemOrchestrator
from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier
from evolux_engine.core.specialized_agents import (
    ResourceAwarePlannerAgent,
    ResourceAwareExecutorAgent, 
    ResourceAwareCriticAgent
)

# Legacy components
from evolux_engine.core.orchestrator import Orchestrator
from evolux_engine.core.planner import PlannerAgent
from evolux_engine.core.executor import TaskExecutorAgent
from evolux_engine.core.validator import SemanticValidatorAgent

logger = get_structured_logger("evolux_mas_integration")


class HybridOrchestrator:
    """
    Hybrid orchestrator that can operate in both legacy mode and advanced MAS mode,
    providing seamless transition and backward compatibility
    """
    
    def __init__(
        self, 
        project_context: Union[ProjectContext, LegacyProjectContext],
        config_manager: ConfigManager,
        mode: str = "adaptive"  # "legacy", "mas", "adaptive"
    ):
        self.project_context = project_context
        self.config_manager = config_manager
        self.mode = mode
        
        # Legacy orchestrator
        self.legacy_orchestrator: Optional[Orchestrator] = None
        
        # MAS orchestrator
        self.mas_orchestrator: Optional[MultiAgentSystemOrchestrator] = None
        
        # Hybrid state
        self.performance_tracker = {
            'legacy': {'tasks': 0, 'success_rate': 1.0, 'efficiency': 0.5},
            'mas': {'tasks': 0, 'success_rate': 1.0, 'efficiency': 0.5}
        }
        
        # Token budget management
        self.total_token_budget = self._calculate_token_budget()
        
        # Initialize based on mode
        self._initialize_orchestrators()
        
        logger.info(f"Initialized HybridOrchestrator in {mode} mode with {self.total_token_budget} token budget")
    
    def _calculate_token_budget(self) -> int:
        """Calculate token budget based on project requirements and configuration"""
        
        # Base budget calculation
        base_budget = 10000  # Default base budget
        
        # Adjust based on project complexity
        if hasattr(self.project_context, 'project_goal'):
            goal_complexity = len(self.project_context.project_goal.split()) / 10.0
            complexity_multiplier = 1.0 + min(2.0, goal_complexity)
            base_budget = int(base_budget * complexity_multiplier)
        
        # Adjust based on configuration
        budget_multiplier = self.config_manager.get_global_setting("token_budget_multiplier", 1.0)
        
        return int(base_budget * budget_multiplier)
    
    def _initialize_orchestrators(self):
        """Initialize orchestrators based on mode"""
        
        if self.mode in ["legacy", "adaptive"]:
            # Initialize legacy orchestrator
            try:
                self.legacy_orchestrator = Orchestrator(
                    project_context=self.project_context,
                    config_manager=self.config_manager
                )
                logger.info("Legacy orchestrator initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize legacy orchestrator: {str(e)}")
        
        if self.mode in ["mas", "adaptive"]:
            # Initialize MAS orchestrator
            try:
                self.mas_orchestrator = MultiAgentSystemOrchestrator(
                    total_system_budget=self.total_token_budget,
                    config_manager=self.config_manager
                )
                logger.info("MAS orchestrator initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize MAS orchestrator: {str(e)}")
    
    async def run_project_cycle(self) -> Dict[str, Any]:
        """Run project cycle using the most appropriate orchestrator"""
        
        if self.mode == "legacy":
            return await self._run_legacy_cycle()
        elif self.mode == "mas":
            return await self._run_mas_cycle()
        else:  # adaptive mode
            return await self._run_adaptive_cycle()
    
    async def _run_legacy_cycle(self) -> Dict[str, Any]:
        """Run project cycle using legacy orchestrator"""
        
        if not self.legacy_orchestrator:
            raise RuntimeError("Legacy orchestrator not available")
        
        try:
            logger.info("Running project cycle in legacy mode")
            result = await self.legacy_orchestrator.run_project_cycle()
            
            # Update performance tracking
            self.performance_tracker['legacy']['tasks'] += 1
            if result.get('success', False):
                self.performance_tracker['legacy']['success_rate'] = (
                    self.performance_tracker['legacy']['success_rate'] * 0.9 + 0.1
                )
            else:
                self.performance_tracker['legacy']['success_rate'] *= 0.9
            
            return result
            
        except Exception as e:
            logger.error(f"Legacy cycle failed: {str(e)}")
            return {'success': False, 'error': str(e), 'mode': 'legacy'}
    
    async def _run_mas_cycle(self) -> Dict[str, Any]:
        """Run project cycle using MAS orchestrator"""
        
        if not self.mas_orchestrator:
            raise RuntimeError("MAS orchestrator not available")
        
        try:
            logger.info("Running project cycle in MAS mode")
            
            # Initialize default agents if not already done
            if not self.mas_orchestrator.agents:
                agent_ids = await self.mas_orchestrator.initialize_default_agents()
                logger.info(f"Initialized MAS agents: {agent_ids}")
            
            # Convert project goal to tasks
            tasks = await self._convert_project_to_tasks()
            
            # Submit tasks to MAS
            task_ids = []
            for task in tasks:
                task_id = await self.mas_orchestrator.submit_task(
                    task=task,
                    priority=task.get('priority', 0.5)
                )
                task_ids.append(task_id)
            
            # Process task queue
            processing_result = await self.mas_orchestrator.process_task_queue()
            
            # Update performance tracking
            self.performance_tracker['mas']['tasks'] += len(task_ids)
            success_rate = processing_result.get('successful', 0) / max(processing_result.get('processed', 1), 1)
            self.performance_tracker['mas']['success_rate'] = (
                self.performance_tracker['mas']['success_rate'] * 0.9 + success_rate * 0.1
            )
            
            # Get system status
            system_status = self.mas_orchestrator.get_system_status()
            
            return {
                'success': processing_result.get('successful', 0) > 0,
                'mode': 'mas',
                'tasks_processed': processing_result.get('processed', 0),
                'tasks_successful': processing_result.get('successful', 0),
                'tasks_failed': processing_result.get('failed', 0),
                'system_status': system_status,
                'emergent_behaviors': system_status.get('emergent_behaviors', []),
                'collective_intelligence_score': system_status['system_metrics']['collective_intelligence_score']
            }
            
        except Exception as e:
            logger.error(f"MAS cycle failed: {str(e)}")
            return {'success': False, 'error': str(e), 'mode': 'mas'}
    
    async def _run_adaptive_cycle(self) -> Dict[str, Any]:
        """Run project cycle using adaptive mode selection"""
        
        # Determine which mode to use based on performance and context
        selected_mode = self._select_optimal_mode()
        
        if selected_mode == "legacy":
            result = await self._run_legacy_cycle()
        else:
            result = await self._run_mas_cycle()
        
        result['selected_mode'] = selected_mode
        result['mode_selection_reason'] = self._get_mode_selection_reason()
        
        return result
    
    def _select_optimal_mode(self) -> str:
        """Select optimal mode based on current context and performance"""
        
        # Default to MAS if both are available
        if self.mas_orchestrator and self.legacy_orchestrator:
            
            # Consider performance history
            legacy_perf = self.performance_tracker['legacy']['success_rate']
            mas_perf = self.performance_tracker['mas']['success_rate']
            
            # Consider project complexity
            project_complexity = self._assess_project_complexity()
            
            # Consider resource constraints
            resource_pressure = self._assess_resource_pressure()
            
            # Decision logic
            if project_complexity > 0.7 and resource_pressure > 0.5:
                # High complexity and resource pressure favor MAS
                return "mas"
            elif legacy_perf > mas_perf + 0.2:
                # Significantly better legacy performance
                return "legacy"
            elif mas_perf > legacy_perf + 0.1:
                # Better MAS performance
                return "mas"
            else:
                # Default to MAS for advanced capabilities
                return "mas"
        
        # Fallback based on availability
        if self.mas_orchestrator:
            return "mas"
        elif self.legacy_orchestrator:
            return "legacy"
        else:
            raise RuntimeError("No orchestrator available")
    
    def _assess_project_complexity(self) -> float:
        """Assess project complexity (0.0 to 1.0)"""
        
        complexity_score = 0.5  # Default
        
        if hasattr(self.project_context, 'project_goal'):
            goal = self.project_context.project_goal
            
            # Word count factor
            word_count = len(goal.split())
            word_complexity = min(1.0, word_count / 50.0)
            
            # Technical keywords factor
            technical_keywords = [
                'api', 'database', 'authentication', 'security', 'optimization',
                'algorithm', 'machine learning', 'ai', 'distributed', 'scalable',
                'microservices', 'kubernetes', 'docker', 'cloud'
            ]
            
            tech_count = sum(1 for keyword in technical_keywords if keyword in goal.lower())
            tech_complexity = min(1.0, tech_count / 5.0)
            
            complexity_score = (word_complexity * 0.6 + tech_complexity * 0.4)
        
        return complexity_score
    
    def _assess_resource_pressure(self) -> float:
        """Assess current resource pressure (0.0 to 1.0)"""
        
        # Simple heuristic based on token budget
        if self.mas_orchestrator:
            total_available = sum(
                agent.allocation.available 
                for agent in self.mas_orchestrator.agents.values()
            )
            total_budget = sum(
                agent.allocation.initial_budget 
                for agent in self.mas_orchestrator.agents.values()
            )
            
            if total_budget > 0:
                utilization = 1.0 - (total_available / total_budget)
                return utilization
        
        return 0.3  # Default moderate pressure
    
    def _get_mode_selection_reason(self) -> str:
        """Get reason for mode selection"""
        
        complexity = self._assess_project_complexity()
        pressure = self._assess_resource_pressure()
        
        if complexity > 0.7:
            return f"High project complexity ({complexity:.2f}) favors advanced MAS capabilities"
        elif pressure > 0.6:
            return f"High resource pressure ({pressure:.2f}) requires MAS optimization"
        else:
            return "Standard complexity project suitable for either mode"
    
    async def _convert_project_to_tasks(self) -> List[Dict[str, Any]]:
        """Convert project goal to executable tasks"""
        
        if not hasattr(self.project_context, 'project_goal'):
            return []
        
        goal = self.project_context.project_goal
        
        # Use MAS planner to decompose goal
        if self.mas_orchestrator and self.mas_orchestrator.agents:
            planner_agents = [
                agent for agent in self.mas_orchestrator.agents.values()
                if agent.role == "resource_aware_planner"
            ]
            
            if planner_agents:
                planner = planner_agents[0]
                
                planning_task = {
                    'description': goal,
                    'type': 'planning',
                    'complexity': self._assess_project_complexity(),
                    'importance': 1.0
                }
                
                planning_context = {
                    'complexity': self._assess_project_complexity(),
                    'importance': 1.0
                }
                
                try:
                    planning_result = await planner.execute(planning_task, planning_context)
                    
                    if planning_result.get('success', False) and 'plan' in planning_result:
                        plan = planning_result['plan']
                        tasks = plan.get('tasks', [])
                        
                        # Convert plan tasks to executable format
                        executable_tasks = []
                        for task in tasks:
                            executable_task = {
                                'id': task.get('id', 'unknown'),
                                'description': task.get('description', 'Unknown task'),
                                'type': task.get('type', 'generic'),
                                'priority': task.get('priority', 0.5),
                                'complexity': 1.0,  # Default complexity
                                'dependencies': task.get('dependencies', [])
                            }
                            executable_tasks.append(executable_task)
                        
                        return executable_tasks
                        
                except Exception as e:
                    logger.warning(f"Failed to use MAS planner for task decomposition: {str(e)}")
        
        # Fallback: simple task decomposition
        return [{
            'id': 'main_goal',
            'description': goal,
            'type': 'generic',
            'priority': 1.0,
            'complexity': self._assess_project_complexity()
        }]
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        status = {
            'mode': self.mode,
            'token_budget': self.total_token_budget,
            'performance_tracker': self.performance_tracker
        }
        
        if self.legacy_orchestrator:
            status['legacy_orchestrator'] = {
                'available': True,
                'agent_id': getattr(self.legacy_orchestrator, 'agent_id', 'unknown')
            }
        
        if self.mas_orchestrator:
            mas_status = self.mas_orchestrator.get_system_status()
            status['mas_orchestrator'] = {
                'available': True,
                'system_status': mas_status
            }
        
        return status
    
    async def switch_mode(self, new_mode: str) -> Dict[str, Any]:
        """Switch orchestrator mode"""
        
        if new_mode not in ["legacy", "mas", "adaptive"]:
            return {'success': False, 'error': 'Invalid mode'}
        
        old_mode = self.mode
        self.mode = new_mode
        
        # Reinitialize if needed
        if new_mode != old_mode:
            self._initialize_orchestrators()
        
        logger.info(f"Switched orchestrator mode from {old_mode} to {new_mode}")
        
        return {
            'success': True,
            'old_mode': old_mode,
            'new_mode': new_mode,
            'reason': f"Manual mode switch requested"
        }


class ResourceAwareTaskConverter:
    """
    Converts between legacy Task objects and resource-aware task formats,
    maintaining compatibility while enabling advanced resource optimization
    """
    
    @staticmethod
    def legacy_to_resource_aware(legacy_task: Task) -> Dict[str, Any]:
        """Convert legacy Task to resource-aware format"""
        
        return {
            'id': legacy_task.task_id,
            'description': legacy_task.description,
            'type': legacy_task.task_type.value if hasattr(legacy_task.task_type, 'value') else str(legacy_task.task_type),
            'priority': legacy_task.priority if hasattr(legacy_task, 'priority') else 0.5,
            'complexity': 1.0,  # Default complexity
            'dependencies': legacy_task.dependencies if hasattr(legacy_task, 'dependencies') else [],
            'details': legacy_task.task_details.dict() if hasattr(legacy_task, 'task_details') else {}
        }
    
    @staticmethod
    def resource_aware_to_legacy(ra_task: Dict[str, Any]) -> Task:
        """Convert resource-aware task to legacy Task format"""
        
        # This is a simplified conversion - in practice, you'd need to handle all Task fields
        task_type_mapping = {
            'create_file': TaskType.CREATE_FILE,
            'modify_file': TaskType.MODIFY_FILE,
            'execute_command': TaskType.EXECUTE_COMMAND,
            'validate_artifact': TaskType.VALIDATE_ARTIFACT,
            'generic': TaskType.GENERIC_LLM_QUERY
        }
        
        task_type = task_type_mapping.get(ra_task.get('type', 'generic'), TaskType.GENERIC_LLM_QUERY)
        
        return Task(
            task_id=ra_task.get('id', 'unknown'),
            task_type=task_type,
            description=ra_task.get('description', 'Unknown task'),
            status=TaskStatus.PENDING,
            dependencies=ra_task.get('dependencies', [])
        )


class PerformanceMonitor:
    """
    Monitors and compares performance between legacy and MAS modes,
    providing insights for optimization and mode selection
    """
    
    def __init__(self):
        self.performance_data = {
            'legacy': [],
            'mas': [],
            'hybrid': []
        }
        self.comparison_metrics = {}
    
    def record_execution(
        self, 
        mode: str, 
        execution_time: float, 
        success: bool, 
        tokens_used: int = 0,
        additional_metrics: Dict[str, Any] = None
    ):
        """Record execution performance data"""
        
        record = {
            'timestamp': datetime.now(),
            'execution_time': execution_time,
            'success': success,
            'tokens_used': tokens_used,
            'additional_metrics': additional_metrics or {}
        }
        
        if mode in self.performance_data:
            self.performance_data[mode].append(record)
            
            # Keep only recent data
            if len(self.performance_data[mode]) > 100:
                self.performance_data[mode] = self.performance_data[mode][-100:]
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance differences between modes"""
        
        analysis = {}
        
        for mode, data in self.performance_data.items():
            if not data:
                continue
            
            success_rate = sum(1 for record in data if record['success']) / len(data)
            avg_execution_time = sum(record['execution_time'] for record in data) / len(data)
            avg_tokens_used = sum(record['tokens_used'] for record in data) / len(data)
            
            analysis[mode] = {
                'sample_size': len(data),
                'success_rate': success_rate,
                'avg_execution_time': avg_execution_time,
                'avg_tokens_used': avg_tokens_used,
                'efficiency_score': success_rate / max(avg_execution_time, 0.1)  # Success per second
            }
        
        # Comparative analysis
        if 'legacy' in analysis and 'mas' in analysis:
            legacy = analysis['legacy']
            mas = analysis['mas']
            
            analysis['comparison'] = {
                'success_rate_improvement': mas['success_rate'] - legacy['success_rate'],
                'speed_improvement': legacy['avg_execution_time'] / mas['avg_execution_time'] - 1.0,
                'token_efficiency': legacy['avg_tokens_used'] / max(mas['avg_tokens_used'], 1) - 1.0,
                'overall_improvement': mas['efficiency_score'] / max(legacy['efficiency_score'], 0.1) - 1.0
            }
        
        return analysis
    
    def get_recommendations(self) -> List[str]:
        """Get performance-based recommendations"""
        
        analysis = self.analyze_performance()
        recommendations = []
        
        if 'comparison' in analysis:
            comp = analysis['comparison']
            
            if comp['success_rate_improvement'] > 0.1:
                recommendations.append("MAS mode shows significantly better success rate")
            elif comp['success_rate_improvement'] < -0.1:
                recommendations.append("Legacy mode shows better success rate")
            
            if comp['speed_improvement'] > 0.2:
                recommendations.append("Legacy mode is significantly faster")
            elif comp['speed_improvement'] < -0.2:
                recommendations.append("MAS mode is significantly faster")
            
            if comp['token_efficiency'] > 0.3:
                recommendations.append("Legacy mode is more token-efficient")
            elif comp['token_efficiency'] < -0.3:
                recommendations.append("MAS mode is more token-efficient")
            
            if comp['overall_improvement'] > 0.2:
                recommendations.append("Overall performance favors MAS mode")
            elif comp['overall_improvement'] < -0.2:
                recommendations.append("Overall performance favors legacy mode")
        
        if not recommendations:
            recommendations.append("Performance is similar between modes - use adaptive selection")
        
        return recommendations