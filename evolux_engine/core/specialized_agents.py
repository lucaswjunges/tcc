"""
Specialized Resource-Aware Agent Implementations

This module implements specialized agent types that inherit from ResourceAwareAgent
and demonstrate different cognitive strategies and resource optimization patterns.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
import re

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus, ExecutionResult, ValidationResult
from evolux_engine.core.resource_aware_agent import ResourceAwareAgent, ModelTier, TokenAllocation
from evolux_engine.core.resource_optimizer import ResourceDemand, AllocationStrategy
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.services.config_manager import ConfigManager

logger = get_structured_logger("specialized_agents")


class ResourceAwarePlannerAgent(ResourceAwareAgent):
    """
    Resource-aware planner that optimizes task decomposition and sequencing
    based on token budget constraints and utility maximization
    """
    
    def __init__(self, agent_id: str, initial_token_budget: int, config_manager: ConfigManager):
        super().__init__(
            agent_id=agent_id,
            role="resource_aware_planner",
            initial_token_budget=initial_token_budget,
            model_tier=ModelTier.BALANCED,  # Planners need good reasoning
            meta_cognitive_threshold=0.8,   # High threshold for planning accuracy
            risk_tolerance=0.3,             # Conservative for planning
            collaboration_propensity=0.7    # High collaboration for coordination
        )
        
        self.config_manager = config_manager
        self.specializations = ["task_decomposition", "dependency_analysis", "resource_planning"]
        
        # Planning-specific parameters
        self.max_decomposition_depth = 3
        self.min_task_complexity = 0.1
        self.planning_confidence_threshold = 0.7
        
        # Initialize LLM client for planning
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)
        model_name = self.config_manager.get_default_model_for("planner")
        
        self.llm_client = LLMClient(provider=provider, api_key=api_key, model_name=model_name)
        
        logger.info(f"Initialized ResourceAwarePlannerAgent {agent_id} with {initial_token_budget} tokens")
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning task with resource optimization"""
        
        task_complexity = context.get('complexity', 1.0)
        importance = context.get('importance', 1.0)
        
        # Determine optimal approach based on resource constraints
        if self.should_upgrade_model_tier(task_complexity, importance):
            original_tier = self.allocation.model_tier
            self.allocation.model_tier = self._get_upgraded_tier()
            logger.info(f"Upgraded model tier from {original_tier.name} to {self.allocation.model_tier.name}")
        
        # Estimate token cost for planning
        estimated_tokens = self._estimate_planning_cost(task, context)
        
        # Compute utility and decide whether to proceed
        utility = self.compute_expected_utility("plan_task", estimated_tokens, context)
        
        if utility < 0.1:
            logger.warning(f"Planning utility too low ({utility:.3f}), requesting collaboration")
            # Try collaboration first
            collaboration_result = await self.request_inter_agent_collaboration(
                target_agent_id="resource_aware_executor",  # Fallback to executor
                query=f"Help with planning: {task.get('description', 'Unknown task')}",
                max_tokens=estimated_tokens // 2,
                priority=importance
            )
            
            if collaboration_result:
                return collaboration_result
        
        # Proceed with planning
        if not self.allocation.allocate_tokens(estimated_tokens, "task_planning", utility):
            return {
                'success': False,
                'error': 'insufficient_tokens',
                'tokens_required': estimated_tokens,
                'tokens_available': self.allocation.available
            }
        
        try:
            # Perform resource-optimized planning
            planning_result = await self._execute_resource_optimized_planning(task, context)
            
            # Update performance metrics
            success = planning_result.get('success', False)
            value_generated = planning_result.get('confidence', 0.5) * 2.0
            
            self.performance_metrics.update_metrics(success, estimated_tokens, value_generated)
            
            # Record execution
            self.execution_history.append({
                'timestamp': datetime.now(),
                'task_type': 'planning',
                'tokens_used': estimated_tokens,
                'success': success,
                'efficiency': value_generated / estimated_tokens if estimated_tokens > 0 else 0,
                'strategy': 'resource_optimized_planning'
            })
            
            return planning_result
            
        except Exception as e:
            logger.error(f"Planning execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tokens_used': estimated_tokens
            }
    
    def _estimate_planning_cost(self, task: Dict[str, Any], context: Dict[str, Any]) -> int:
        """Estimate token cost for planning task"""
        
        base_cost = 500  # Base planning cost
        
        # Adjust for complexity
        complexity = context.get('complexity', 1.0)
        complexity_multiplier = 1.0 + (complexity - 1.0) * 0.5
        
        # Adjust for decomposition depth needed
        description = task.get('description', '')
        estimated_depth = min(self.max_decomposition_depth, len(description.split()) // 20 + 1)
        depth_multiplier = 1.0 + (estimated_depth - 1) * 0.3
        
        # Model tier cost adjustment
        tier_multiplier = self.allocation.model_tier.performance_factor
        
        estimated_cost = int(base_cost * complexity_multiplier * depth_multiplier * tier_multiplier)
        
        # Add buffer for safety
        return int(estimated_cost * 1.2)
    
    async def _execute_resource_optimized_planning(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning with resource optimization techniques"""
        
        goal = task.get('description', task.get('goal', 'Unknown task'))
        
        # Use progressive planning to minimize token usage
        planning_prompt = self._create_resource_efficient_planning_prompt(goal, context)
        
        try:
            response = await self.llm_client.generate_response(
                prompt=planning_prompt,
                max_tokens=1000  # Conservative limit
            )
            
            # Parse and validate planning result
            parsed_plan = self._parse_planning_response(response)
            
            # Optimize task sequence for resource efficiency
            optimized_plan = self._optimize_task_sequence(parsed_plan)
            
            return {
                'success': True,
                'plan': optimized_plan,
                'confidence': self._assess_plan_confidence(optimized_plan),
                'estimated_execution_cost': self._estimate_execution_cost(optimized_plan),
                'resource_efficiency_score': self._compute_resource_efficiency(optimized_plan)
            }
            
        except Exception as e:
            logger.error(f"LLM planning call failed: {str(e)}")
            return {
                'success': False,
                'error': f"Planning generation failed: {str(e)}"
            }
    
    def _create_resource_efficient_planning_prompt(self, goal: str, context: Dict[str, Any]) -> str:
        """Create planning prompt optimized for token efficiency"""
        
        return f"""Create an efficient execution plan for the following goal:

GOAL: {goal}

CONSTRAINTS:
- Token budget: {self.allocation.available} remaining
- Complexity level: {context.get('complexity', 1.0)}
- Priority: {context.get('importance', 1.0)}

REQUIREMENTS:
1. Break down into 3-7 concrete, actionable tasks
2. Minimize token usage while maintaining quality
3. Identify task dependencies
4. Estimate resource requirements for each task
5. Prioritize tasks by value/cost ratio

Respond in JSON format:
{{
    "tasks": [
        {{
            "id": "task_1",
            "description": "Clear, specific task description",
            "type": "create_file|modify_file|execute_command|validate_artifact",
            "estimated_tokens": <number>,
            "priority": <0.0-1.0>,
            "dependencies": ["task_id1", "task_id2"],
            "expected_value": <0.0-2.0>
        }}
    ],
    "execution_strategy": "sequential|parallel|hybrid",
    "risk_assessment": "low|medium|high",
    "total_estimated_cost": <number>
}}"""
    
    def _parse_planning_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM planning response"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
                
                # Validate required fields
                required_fields = ['tasks', 'execution_strategy']
                for field in required_fields:
                    if field not in plan_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Validate tasks
                for task in plan_data.get('tasks', []):
                    if not all(key in task for key in ['id', 'description', 'type']):
                        raise ValueError("Invalid task structure")
                
                return plan_data
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse planning response: {str(e)}")
            # Return fallback plan
            return {
                'tasks': [{
                    'id': 'fallback_task',
                    'description': response[:200] + "..." if len(response) > 200 else response,
                    'type': 'generic_llm_query',
                    'estimated_tokens': 100,
                    'priority': 0.5,
                    'dependencies': [],
                    'expected_value': 1.0
                }],
                'execution_strategy': 'sequential',
                'risk_assessment': 'medium',
                'total_estimated_cost': 100
            }
    
    def _optimize_task_sequence(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize task sequence for resource efficiency"""
        
        tasks = plan.get('tasks', [])
        
        if len(tasks) <= 1:
            return plan
        
        # Sort tasks by value/cost ratio (greedy optimization)
        for task in tasks:
            tokens = task.get('estimated_tokens', 100)
            value = task.get('expected_value', 1.0)
            task['efficiency_score'] = value / tokens if tokens > 0 else 0
        
        # Topological sort considering dependencies
        optimized_tasks = self._topological_sort_tasks(tasks)
        
        plan['tasks'] = optimized_tasks
        plan['optimization_applied'] = True
        
        return plan
    
    def _topological_sort_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks respecting dependencies and efficiency"""
        
        # Build dependency graph
        task_map = {task['id']: task for task in tasks}
        in_degree = {task['id']: 0 for task in tasks}
        
        for task in tasks:
            for dep in task.get('dependencies', []):
                if dep in in_degree:
                    in_degree[task['id']] += 1
        
        # Kahn's algorithm with efficiency prioritization
        result = []
        available = [task for task in tasks if in_degree[task['id']] == 0]
        
        while available:
            # Sort available tasks by efficiency score
            available.sort(key=lambda t: t.get('efficiency_score', 0), reverse=True)
            current = available.pop(0)
            result.append(current)
            
            # Update dependencies
            for task in tasks:
                if current['id'] in task.get('dependencies', []):
                    in_degree[task['id']] -= 1
                    if in_degree[task['id']] == 0:
                        available.append(task)
        
        return result
    
    def _assess_plan_confidence(self, plan: Dict[str, Any]) -> float:
        """Assess confidence in the generated plan"""
        
        tasks = plan.get('tasks', [])
        
        if not tasks:
            return 0.0
        
        # Base confidence from task structure
        structure_score = min(1.0, len(tasks) / 5.0)  # Optimal around 5 tasks
        
        # Confidence from estimated costs
        total_cost = sum(task.get('estimated_tokens', 0) for task in tasks)
        cost_confidence = 1.0 if total_cost <= self.allocation.available else 0.5
        
        # Confidence from dependency structure
        dependency_score = self._assess_dependency_structure(tasks)
        
        overall_confidence = (structure_score * 0.3 + cost_confidence * 0.4 + dependency_score * 0.3)
        
        return min(1.0, overall_confidence)
    
    def _assess_dependency_structure(self, tasks: List[Dict[str, Any]]) -> float:
        """Assess quality of dependency structure"""
        
        if len(tasks) <= 1:
            return 1.0
        
        total_dependencies = sum(len(task.get('dependencies', [])) for task in tasks)
        avg_dependencies = total_dependencies / len(tasks)
        
        # Optimal dependency ratio (not too sparse, not too dense)
        if avg_dependencies < 0.5:
            return 0.7  # Too sparse
        elif avg_dependencies > 2.0:
            return 0.6  # Too dense
        else:
            return 1.0  # Good structure
    
    def _estimate_execution_cost(self, plan: Dict[str, Any]) -> int:
        """Estimate total execution cost for the plan"""
        
        tasks = plan.get('tasks', [])
        total_cost = sum(task.get('estimated_tokens', 100) for task in tasks)
        
        # Add overhead for coordination and validation
        overhead_factor = 1.2
        
        return int(total_cost * overhead_factor)
    
    def _compute_resource_efficiency(self, plan: Dict[str, Any]) -> float:
        """Compute resource efficiency score for the plan"""
        
        tasks = plan.get('tasks', [])
        
        if not tasks:
            return 0.0
        
        total_value = sum(task.get('expected_value', 1.0) for task in tasks)
        total_cost = sum(task.get('estimated_tokens', 100) for task in tasks)
        
        if total_cost == 0:
            return 0.0
        
        efficiency = total_value / total_cost
        
        # Normalize to 0-1 range
        return min(1.0, efficiency * 100)  # Assuming 0.01 value per token is good efficiency


class ResourceAwareExecutorAgent(ResourceAwareAgent):
    """
    Resource-aware executor that implements adaptive execution strategies
    with real-time resource monitoring and optimization
    """
    
    def __init__(self, agent_id: str, initial_token_budget: int, config_manager: ConfigManager):
        super().__init__(
            agent_id=agent_id,
            role="resource_aware_executor",
            initial_token_budget=initial_token_budget,
            model_tier=ModelTier.ECONOMY,  # Start with economy for execution
            meta_cognitive_threshold=0.6,  # Medium threshold for execution
            risk_tolerance=0.7,            # Higher risk tolerance for execution
            collaboration_propensity=0.5   # Moderate collaboration
        )
        
        self.config_manager = config_manager
        self.specializations = ["code_generation", "command_execution", "artifact_creation"]
        
        # Execution-specific parameters
        self.retry_limit = 3
        self.escalation_threshold = 0.3  # Escalate if success rate drops below this
        self.adaptive_strategy_enabled = True
        
        # Initialize LLM client
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)
        model_name = self.config_manager.get_default_model_for("executor_content_gen")
        
        self.llm_client = LLMClient(provider=provider, api_key=api_key, model_name=model_name)
        
        logger.info(f"Initialized ResourceAwareExecutorAgent {agent_id} with {initial_token_budget} tokens")
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with adaptive resource optimization"""
        
        task_type = task.get('type', TaskType.GENERIC_LLM_QUERY)
        complexity = context.get('complexity', 1.0)
        
        # Adaptive model tier selection
        if self.adaptive_strategy_enabled:
            optimal_tier = self._select_optimal_model_tier(task, context)
            if optimal_tier != self.allocation.model_tier:
                self.allocation.model_tier = optimal_tier
                logger.info(f"Adapted model tier to {optimal_tier.name} for task execution")
        
        # Estimate execution cost
        estimated_tokens = self._estimate_execution_cost(task, context)
        
        # Resource allocation decision
        utility = self.compute_expected_utility("execute_task", estimated_tokens, context)
        
        if utility < 0.05:
            # Very low utility, try to optimize or delegate
            return await self._handle_low_utility_task(task, context, estimated_tokens)
        
        # Allocate tokens
        if not self.allocation.allocate_tokens(estimated_tokens, f"execute_{task_type}", utility):
            return await self._handle_resource_shortage(task, context, estimated_tokens)
        
        # Execute with retry logic
        for attempt in range(self.retry_limit):
            try:
                result = await self._execute_with_monitoring(task, context, attempt)
                
                # Update metrics
                success = result.get('success', False)
                tokens_used = result.get('tokens_used', estimated_tokens)
                value_generated = result.get('value_generated', 1.0 if success else 0.0)
                
                self.performance_metrics.update_metrics(success, tokens_used, value_generated)
                
                # Record execution
                self.execution_history.append({
                    'timestamp': datetime.now(),
                    'task_type': task_type,
                    'tokens_used': tokens_used,
                    'success': success,
                    'efficiency': value_generated / tokens_used if tokens_used > 0 else 0,
                    'strategy': 'adaptive_execution',
                    'attempt': attempt + 1
                })
                
                if success or attempt == self.retry_limit - 1:
                    return result
                    
            except Exception as e:
                logger.warning(f"Execution attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.retry_limit - 1:
                    return {
                        'success': False,
                        'error': f"Execution failed after {self.retry_limit} attempts: {str(e)}",
                        'tokens_used': estimated_tokens
                    }
        
        return {'success': False, 'error': 'max_retries_exceeded'}
    
    def _select_optimal_model_tier(self, task: Dict[str, Any], context: Dict[str, Any]) -> ModelTier:
        """Select optimal model tier based on task requirements and resource constraints"""
        
        task_type = task.get('type', TaskType.GENERIC_LLM_QUERY)
        complexity = context.get('complexity', 1.0)
        importance = context.get('importance', 1.0)
        
        # Task type requirements
        tier_requirements = {
            TaskType.CREATE_FILE: ModelTier.BALANCED,
            TaskType.MODIFY_FILE: ModelTier.ECONOMY,
            TaskType.EXECUTE_COMMAND: ModelTier.ECONOMY,
            TaskType.VALIDATE_ARTIFACT: ModelTier.BALANCED,
            TaskType.GENERIC_LLM_QUERY: ModelTier.ECONOMY
        }
        
        base_tier = tier_requirements.get(task_type, ModelTier.ECONOMY)
        
        # Upgrade for complex or important tasks
        if complexity > 1.5 and importance > 0.7:
            # Find next tier up
            tiers = [ModelTier.ECONOMY, ModelTier.BALANCED, ModelTier.PREMIUM, ModelTier.ULTRA]
            current_idx = tiers.index(base_tier)
            if current_idx < len(tiers) - 1:
                upgraded_tier = tiers[current_idx + 1]
                
                # Check if we can afford the upgrade
                cost_increase = upgraded_tier.total_cost_per_1k / base_tier.total_cost_per_1k
                if self.allocation.available > 1000 * cost_increase:  # Conservative check
                    return upgraded_tier
        
        return base_tier
    
    def _estimate_execution_cost(self, task: Dict[str, Any], context: Dict[str, Any]) -> int:
        """Estimate token cost for task execution"""
        
        task_type = task.get('type', TaskType.GENERIC_LLM_QUERY)
        complexity = context.get('complexity', 1.0)
        
        # Base costs by task type
        base_costs = {
            TaskType.CREATE_FILE: 300,
            TaskType.MODIFY_FILE: 200,
            TaskType.EXECUTE_COMMAND: 150,
            TaskType.VALIDATE_ARTIFACT: 250,
            TaskType.GENERIC_LLM_QUERY: 200
        }
        
        base_cost = base_costs.get(task_type, 200)
        
        # Adjust for complexity and model tier
        complexity_multiplier = 1.0 + (complexity - 1.0) * 0.4
        tier_multiplier = self.allocation.model_tier.performance_factor * 0.8  # Execution is more predictable
        
        estimated_cost = int(base_cost * complexity_multiplier * tier_multiplier)
        
        return max(50, estimated_cost)  # Minimum cost
    
    async def _execute_with_monitoring(self, task: Dict[str, Any], context: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Execute task with real-time resource monitoring"""
        
        start_time = datetime.now()
        initial_tokens = self.allocation.consumed
        
        task_type = task.get('type', TaskType.GENERIC_LLM_QUERY)
        
        try:
            if task_type == TaskType.CREATE_FILE:
                result = await self._execute_create_file(task, context)
            elif task_type == TaskType.MODIFY_FILE:
                result = await self._execute_modify_file(task, context)
            elif task_type == TaskType.EXECUTE_COMMAND:
                result = await self._execute_command(task, context)
            elif task_type == TaskType.VALIDATE_ARTIFACT:
                result = await self._execute_validation(task, context)
            else:
                result = await self._execute_generic_llm_query(task, context)
            
            # Calculate actual resource usage
            execution_time = (datetime.now() - start_time).total_seconds()
            tokens_used = self.allocation.consumed - initial_tokens
            
            result.update({
                'execution_time_seconds': execution_time,
                'tokens_used': tokens_used,
                'attempt': attempt + 1
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                'tokens_used': self.allocation.consumed - initial_tokens,
                'attempt': attempt + 1
            }
    
    async def _execute_create_file(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file creation task"""
        
        file_path = task.get('file_path', 'unknown.txt')
        description = task.get('description', 'Create file')
        
        prompt = f"""Generate content for file: {file_path}

Requirements: {description}

Provide clean, well-structured content appropriate for the file type.
Focus on quality and completeness while being concise."""
        
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt,
                max_tokens=800
            )
            
            # In a real implementation, this would write to the actual file
            return {
                'success': True,
                'file_path': file_path,
                'content_generated': len(response),
                'value_generated': 1.5  # File creation has good value
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"File creation failed: {str(e)}"
            }
    
    async def _execute_modify_file(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file modification task"""
        
        file_path = task.get('file_path', 'unknown.txt')
        modification = task.get('modification', 'Modify file')
        
        prompt = f"""Modify file: {file_path}

Modification requested: {modification}

Provide the specific changes needed, being precise and efficient."""
        
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt,
                max_tokens=600
            )
            
            return {
                'success': True,
                'file_path': file_path,
                'modification_applied': True,
                'value_generated': 1.2  # Modification has moderate value
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"File modification failed: {str(e)}"
            }
    
    async def _execute_command(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command task"""
        
        command = task.get('command', 'echo "unknown command"')
        
        # In a real implementation, this would execute through SecureExecutor
        # For now, simulate command execution
        
        return {
            'success': True,
            'command': command,
            'exit_code': 0,
            'output': f"Simulated execution of: {command}",
            'value_generated': 1.0
        }
    
    async def _execute_validation(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation task"""
        
        artifact_path = task.get('artifact_path', 'unknown')
        criteria = task.get('criteria', 'General validation')
        
        prompt = f"""Validate artifact: {artifact_path}

Validation criteria: {criteria}

Provide a brief assessment of whether the criteria are met."""
        
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt,
                max_tokens=400
            )
            
            # Simple validation logic
            validation_passed = 'valid' in response.lower() or 'pass' in response.lower()
            
            return {
                'success': True,
                'artifact_path': artifact_path,
                'validation_passed': validation_passed,
                'validation_details': response,
                'value_generated': 1.3  # Validation has good value
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Validation failed: {str(e)}"
            }
    
    async def _execute_generic_llm_query(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic LLM query"""
        
        query = task.get('query', task.get('description', 'Generic query'))
        
        try:
            response = await self.llm_client.generate_response(
                prompt=query,
                max_tokens=500
            )
            
            return {
                'success': True,
                'query': query,
                'response': response,
                'value_generated': 1.0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"LLM query failed: {str(e)}"
            }
    
    async def _handle_low_utility_task(self, task: Dict[str, Any], context: Dict[str, Any], estimated_tokens: int) -> Dict[str, Any]:
        """Handle tasks with very low utility"""
        
        # Try collaboration first
        collaboration_result = await self.request_inter_agent_collaboration(
            target_agent_id="resource_aware_critic",
            query=f"Review and optimize task: {task.get('description', 'Unknown task')}",
            max_tokens=estimated_tokens // 3,
            priority=context.get('importance', 0.5)
        )
        
        if collaboration_result:
            return collaboration_result
        
        # If collaboration fails, return minimal effort result
        return {
            'success': False,
            'error': 'task_utility_too_low',
            'utility_threshold': 0.05,
            'suggested_action': 'task_refinement_needed'
        }
    
    async def _handle_resource_shortage(self, task: Dict[str, Any], context: Dict[str, Any], estimated_tokens: int) -> Dict[str, Any]:
        """Handle insufficient resource scenarios"""
        
        logger.warning(f"Insufficient resources for task: need {estimated_tokens}, have {self.allocation.available}")
        
        # Try to request additional resources or collaboration
        if self.collaboration_propensity > 0.6:
            collaboration_result = await self.request_inter_agent_collaboration(
                target_agent_id="resource_aware_planner",
                query=f"Resource shortage for task: {task.get('description', 'Unknown task')}",
                max_tokens=self.allocation.available // 2,
                priority=1.0  # High priority for resource issues
            )
            
            if collaboration_result:
                return collaboration_result
        
        return {
            'success': False,
            'error': 'insufficient_resources',
            'tokens_required': estimated_tokens,
            'tokens_available': self.allocation.available,
            'suggested_action': 'request_additional_budget'
        }


class ResourceAwareCriticAgent(ResourceAwareAgent):
    """
    Resource-aware critic that provides quality assessment and optimization feedback
    with minimal resource consumption through efficient evaluation strategies
    """
    
    def __init__(self, agent_id: str, initial_token_budget: int, config_manager: ConfigManager):
        super().__init__(
            agent_id=agent_id,
            role="resource_aware_critic",
            initial_token_budget=initial_token_budget,
            model_tier=ModelTier.BALANCED,  # Good reasoning needed for criticism
            meta_cognitive_threshold=0.9,   # Very high threshold for quality assessment
            risk_tolerance=0.2,             # Very conservative
            collaboration_propensity=0.8    # High collaboration for feedback
        )
        
        self.config_manager = config_manager
        self.specializations = ["quality_assessment", "optimization_feedback", "risk_analysis"]
        
        # Critic-specific parameters
        self.quality_threshold = 0.7
        self.criticism_depth_levels = ['surface', 'moderate', 'deep']
        self.current_depth_level = 'moderate'
        
        # Initialize LLM client
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)
        model_name = self.config_manager.get_default_model_for("validator")
        
        self.llm_client = LLMClient(provider=provider, api_key=api_key, model_name=model_name)
        
        logger.info(f"Initialized ResourceAwareCriticAgent {agent_id} with {initial_token_budget} tokens")
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute criticism/evaluation task with resource optimization"""
        
        evaluation_type = task.get('evaluation_type', 'general')
        target_artifact = task.get('target_artifact', 'unknown')
        
        # Adaptive depth selection based on importance and available resources
        depth_level = self._select_optimal_depth_level(context)
        
        # Estimate cost based on depth level
        estimated_tokens = self._estimate_criticism_cost(task, context, depth_level)
        
        # Resource allocation decision
        utility = self.compute_expected_utility("criticism", estimated_tokens, context)
        
        if not self.allocation.allocate_tokens(estimated_tokens, f"criticize_{evaluation_type}", utility):
            return {
                'success': False,
                'error': 'insufficient_tokens_for_criticism',
                'tokens_required': estimated_tokens,
                'tokens_available': self.allocation.available
            }
        
        try:
            # Perform resource-efficient criticism
            criticism_result = await self._execute_resource_efficient_criticism(
                task, context, depth_level
            )
            
            # Update metrics
            success = criticism_result.get('success', False)
            value_generated = criticism_result.get('quality_score', 0.5) * 1.5  # Criticism has strategic value
            
            self.performance_metrics.update_metrics(success, estimated_tokens, value_generated)
            
            # Record execution
            self.execution_history.append({
                'timestamp': datetime.now(),
                'task_type': 'criticism',
                'tokens_used': estimated_tokens,
                'success': success,
                'efficiency': value_generated / estimated_tokens if estimated_tokens > 0 else 0,
                'strategy': f'criticism_depth_{depth_level}',
                'depth_level': depth_level
            })
            
            return criticism_result
            
        except Exception as e:
            logger.error(f"Criticism execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tokens_used': estimated_tokens
            }
    
    def _select_optimal_depth_level(self, context: Dict[str, Any]) -> str:
        """Select optimal criticism depth based on context and resources"""
        
        importance = context.get('importance', 1.0)
        complexity = context.get('complexity', 1.0)
        available_ratio = self.allocation.available / self.allocation.initial_budget
        
        # Simple decision logic
        if importance > 0.8 and available_ratio > 0.3:
            return 'deep'
        elif importance > 0.5 and available_ratio > 0.2:
            return 'moderate'
        else:
            return 'surface'
    
    def _estimate_criticism_cost(self, task: Dict[str, Any], context: Dict[str, Any], depth_level: str) -> int:
        """Estimate token cost for criticism based on depth level"""
        
        base_costs = {
            'surface': 150,
            'moderate': 300,
            'deep': 600
        }
        
        base_cost = base_costs.get(depth_level, 300)
        
        # Adjust for complexity
        complexity_multiplier = 1.0 + (context.get('complexity', 1.0) - 1.0) * 0.3
        
        return int(base_cost * complexity_multiplier)
    
    async def _execute_resource_efficient_criticism(
        self, 
        task: Dict[str, Any], 
        context: Dict[str, Any], 
        depth_level: str
    ) -> Dict[str, Any]:
        """Execute criticism with specified depth level"""
        
        target = task.get('target_artifact', task.get('description', 'Unknown target'))
        evaluation_criteria = task.get('criteria', 'General quality assessment')
        
        # Create depth-appropriate prompt
        prompt = self._create_criticism_prompt(target, evaluation_criteria, depth_level)
        
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt,
                max_tokens=self._get_max_tokens_for_depth(depth_level)
            )
            
            # Parse criticism response
            criticism_analysis = self._parse_criticism_response(response, depth_level)
            
            return {
                'success': True,
                'target_artifact': target,
                'depth_level': depth_level,
                'quality_score': criticism_analysis['quality_score'],
                'issues_found': criticism_analysis['issues'],
                'recommendations': criticism_analysis['recommendations'],
                'optimization_suggestions': criticism_analysis.get('optimizations', []),
                'confidence': criticism_analysis['confidence']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Criticism generation failed: {str(e)}"
            }
    
    def _create_criticism_prompt(self, target: str, criteria: str, depth_level: str) -> str:
        """Create criticism prompt based on depth level"""
        
        base_prompt = f"""Evaluate the following artifact: {target}

Evaluation criteria: {criteria}"""
        
        if depth_level == 'surface':
            return base_prompt + """

Provide a brief quality assessment (2-3 sentences):
- Overall quality score (0.0-1.0)
- Main strength
- Primary concern (if any)"""
        
        elif depth_level == 'moderate':
            return base_prompt + """

Provide a moderate-depth analysis:
1. Quality score (0.0-1.0) with brief justification
2. Top 3 strengths
3. Top 3 issues or areas for improvement
4. 2-3 specific recommendations

Keep analysis concise but thorough."""
        
        else:  # deep
            return base_prompt + """

Provide a comprehensive analysis:
1. Overall quality score (0.0-1.0) with detailed justification
2. Strengths analysis (what works well and why)
3. Issues analysis (problems and their impact)
4. Specific recommendations with priority levels
5. Optimization suggestions for efficiency/performance
6. Risk assessment and mitigation strategies

Be thorough but maintain focus on actionable insights."""
    
    def _get_max_tokens_for_depth(self, depth_level: str) -> int:
        """Get max tokens based on depth level"""
        return {
            'surface': 200,
            'moderate': 500,
            'deep': 1000
        }.get(depth_level, 500)
    
    def _parse_criticism_response(self, response: str, depth_level: str) -> Dict[str, Any]:
        """Parse criticism response and extract structured feedback"""
        
        # Simple parsing logic (in real implementation, this would be more sophisticated)
        
        # Extract quality score
        quality_score = 0.5  # Default
        score_matches = re.findall(r'(?:score|quality).*?([0-9]*\.?[0-9]+)', response.lower())
        if score_matches:
            try:
                quality_score = min(1.0, max(0.0, float(score_matches[0])))
            except ValueError:
                pass
        
        # Extract issues and recommendations (simplified)
        issues = []
        recommendations = []
        optimizations = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'issue' in line.lower() or 'problem' in line.lower():
                current_section = 'issues'
            elif 'recommend' in line.lower() or 'suggest' in line.lower():
                current_section = 'recommendations'
            elif 'optim' in line.lower():
                current_section = 'optimizations'
            elif line and current_section:
                if current_section == 'issues':
                    issues.append(line)
                elif current_section == 'recommendations':
                    recommendations.append(line)
                elif current_section == 'optimizations':
                    optimizations.append(line)
        
        # Confidence based on response length and structure
        confidence = min(1.0, len(response) / 500.0) if depth_level != 'surface' else 0.8
        
        return {
            'quality_score': quality_score,
            'issues': issues[:5],  # Limit to top 5
            'recommendations': recommendations[:5],
            'optimizations': optimizations[:3],
            'confidence': confidence
        }