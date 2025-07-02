"""
Sistema de Refinamento Iterativo para o Evolux Engine

Este módulo implementa um sistema de revisão e melhoria iterativa que:
- Executa múltiplas iterações de uma tarefa
- Usa diferentes LLMs para validação cruzada
- Implementa auto-crítica e refinamento
- Fornece feedback detalhado para melhorias contínuas
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import json

from loguru import logger
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.schemas.contracts import Task, ExecutionResult, ValidationResult
from evolux_engine.prompts.prompt_engine import PromptEngine, PromptContext
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.utils.string_utils import extract_json_from_llm_response

if TYPE_CHECKING:
    from evolux_engine.llms.llm_factory import LLMFactory
    from evolux_engine.services.config_manager import ConfigManager


class RefinementStrategy(Enum):
    """Estratégias de refinamento disponíveis"""
    SINGLE_PASS = "single_pass"  # Uma iteração apenas
    ITERATIVE_IMPROVEMENT = "iterative_improvement"  # Múltiplas iterações com melhorias
    CROSS_VALIDATION = "cross_validation"  # Validação cruzada com múltiplos LLMs
    ADVERSARIAL_REVIEW = "adversarial_review"  # Revisão adversarial crítica


@dataclass
class RefinementIteration:
    """Representa uma iteração do processo de refinamento"""
    iteration_number: int
    task_attempt: str
    execution_result: ExecutionResult
    validation_result: ValidationResult
    reviewer_feedback: Optional[str] = None
    quality_score: float = 0.0
    improvement_suggestions: List[str] = None


@dataclass 
class RefinementResult:
    """Resultado final do processo de refinamento"""
    final_result: ExecutionResult
    iterations: List[RefinementIteration]
    total_iterations: int
    final_quality_score: float
    convergence_achieved: bool
    improvement_trajectory: List[float]  # Pontuações de qualidade por iteração


class IterativeRefiner:
    """
    Sistema de refinamento iterativo que melhora continuamente os resultados
    através de múltiplas iterações, feedback e validação cruzada.
    """
    
    def __init__(
        self,
        llm_factory: "LLMFactory",
        config_manager: "ConfigManager",
        prompt_engine: PromptEngine,
        project_context: ProjectContext,
        file_service,
        shell_service,
        max_iterations: int = 5,
        quality_threshold: float = 8.5,
        convergence_threshold: float = 0.1
    ):
        from evolux_engine.schemas.contracts import LLMProvider
        self.llm_factory = llm_factory
        self.config_manager = config_manager
        self.prompt_engine = prompt_engine
        self.project_context = project_context
        self.file_service = file_service
        self.shell_service = shell_service
        
        # Ajusta o número de iterações com base no modo de execução
        execution_mode = self.config_manager.get_global_setting("execution_mode", "producao")
        if execution_mode == "teste":
            self.max_iterations = 1
            logger.info("Modo de teste ativado: O número máximo de iterações de refinamento foi definido como 1.")
        else:
            self.max_iterations = max_iterations

        self.quality_threshold = quality_threshold
        self.convergence_threshold = convergence_threshold

        # Get clients from factory
        from evolux_engine.llms.model_router import TaskCategory
        
        self.primary_llm = self.llm_factory.get_client(
            task_category=TaskCategory.CODE_GENERATION
        )
        self.reviewer_llm = self.llm_factory.get_client(
            task_category=TaskCategory.VALIDATION
        )
        self.validator_llm = self.reviewer_llm # Reuse the same client

        logger.info(f"IterativeRefiner initialized with {max_iterations} max iterations")
    
    async def refine_task_iteratively(
        self,
        task: Task,
        strategy: RefinementStrategy = RefinementStrategy.ITERATIVE_IMPROVEMENT
    ) -> RefinementResult:
        """
        Refina uma tarefa iterativamente até atingir qualidade satisfatória
        """
        logger.info(f"Starting iterative refinement for task {task.task_id} with strategy {strategy.value}")
        
        iterations = []
        current_attempt = None
        quality_scores = []
        
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"Refinement iteration {iteration}/{self.max_iterations}")
            
            # Executar iteração
            iteration_result = await self._execute_refinement_iteration(
                task, iteration, iterations, strategy
            )
            
            iterations.append(iteration_result)
            quality_scores.append(iteration_result.quality_score)
            
            # Verificar critérios de parada
            if self._should_stop_refinement(iteration_result, quality_scores):
                logger.info(f"Refinement completed after {iteration} iterations")
                break
            
            # Preparar próxima iteração baseada no feedback
            if iteration < self.max_iterations:
                await self._prepare_next_iteration(task, iteration_result)
        
        # Selecionar melhor resultado
        best_iteration = max(iterations, key=lambda x: x.quality_score)
        convergence_achieved = best_iteration.quality_score >= self.quality_threshold
        
        return RefinementResult(
            final_result=best_iteration.execution_result,
            iterations=iterations,
            total_iterations=len(iterations),
            final_quality_score=best_iteration.quality_score,
            convergence_achieved=convergence_achieved,
            improvement_trajectory=quality_scores
        )
    
    async def _execute_refinement_iteration(
        self,
        task: Task,
        iteration_number: int,
        previous_iterations: List[RefinementIteration],
        strategy: RefinementStrategy
    ) -> RefinementIteration:
        """Executa uma iteração específica do refinamento"""
        
        # Construir contexto iterativo
        context = self._build_iterative_context(task, previous_iterations)
        
        # Gerar prompt melhorado baseado no histórico
        prompt = self._build_iterative_prompt(task, context, previous_iterations, strategy)
        
        # Executar tarefa com LLM primário
        execution_result = await self._execute_with_primary_llm(task, prompt)
        if not execution_result or execution_result.exit_code != 0:
            # Se a execução primária falhou ou não retornou resultado, não há o que validar.
            return RefinementIteration(
                iteration_number=iteration_number,
                task_attempt=prompt,
                execution_result=execution_result or ExecutionResult(exit_code=1, stderr="Primary LLM execution failed to return a result."),
                validation_result=ValidationResult(validation_passed=False, identified_issues=["Primary LLM execution failed."]),
                quality_score=0.0
            )

        # Validar resultado
        validation_result = await self._validate_iteration_result(task, execution_result)
        
        # Obter feedback de revisor (se usando estratégia de revisão)
        reviewer_feedback = None
        if strategy in [RefinementStrategy.CROSS_VALIDATION, RefinementStrategy.ADVERSARIAL_REVIEW]:
            reviewer_feedback = await self._get_reviewer_feedback(
                task, execution_result, strategy
            )
        
        # Calcular pontuação de qualidade
        quality_score = self._calculate_quality_score(
            execution_result, validation_result, reviewer_feedback
        )
        
        return RefinementIteration(
            iteration_number=iteration_number,
            task_attempt=prompt,
            execution_result=execution_result,
            validation_result=validation_result,
            reviewer_feedback=reviewer_feedback,
            quality_score=quality_score,
            improvement_suggestions=validation_result.suggested_improvements
        )
    
    def _build_iterative_context(
        self,
        task: Task,
        previous_iterations: List[RefinementIteration]
    ) -> PromptContext:
        """Constrói contexto rico baseado em iterações anteriores"""
        
        error_history = []
        for iteration in previous_iterations:
            if iteration.validation_result.identified_issues:
                error_history.extend(iteration.validation_result.identified_issues)
        
        return PromptContext(
            project_goal=self.project_context.project_goal,
            project_type=self.project_context.project_type,
            task_description=task.description,
            current_artifacts=self.project_context.get_artifacts_structure_summary(),
            error_history=error_history,
            iteration_count=len(previous_iterations) + 1
        )
    
    def _build_iterative_prompt(
        self,
        task: Task,
        context: PromptContext,
        previous_iterations: List[RefinementIteration],
        strategy: RefinementStrategy
    ) -> str:
        """Constrói prompt específico para iteração"""
        
        # Extrair tentativas anteriores para aprendizado
        previous_attempts = []
        if previous_iterations:
            for iteration in previous_iterations[-3:]:  # Últimas 3 tentativas
                attempt_summary = {
                    "iteration": iteration.iteration_number,
                    "quality_score": iteration.quality_score,
                    "issues": iteration.validation_result.identified_issues,
                    "suggestions": iteration.improvement_suggestions
                }
                previous_attempts.append(json.dumps(attempt_summary, indent=2))
        
        # Usar template apropriado baseado no tipo de tarefa
        try:
            task_category = task.type.to_task_category() if hasattr(task.type, 'to_task_category') else None
        except:
            task_category = None
        
        template_name = self.prompt_engine.get_template_for_category(
            task_category
        ) if task_category else "code_generation"
        
        # Construir prompt iterativo
        return self.prompt_engine.build_iterative_prompt(
            template_name=template_name or "code_generation",
            context=context,
            previous_attempts=previous_attempts
        )
    
    async def _execute_with_primary_llm(self, task: Task, prompt: str) -> ExecutionResult:
        """Executa tarefa usando LLM primário"""
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert software engineer focused on producing high-quality, production-ready solutions."},
                {"role": "user", "content": prompt}
            ]
            
            from evolux_engine.llms.model_router import TaskCategory
            response = await self.primary_llm.generate_response(
                messages,
                category=TaskCategory.CODE_GENERATION,
                max_tokens=6000,
                temperature=0.2,
                max_prompt_tokens=4096
            )
            
            if not response:
                return ExecutionResult(
                    exit_code=1,
                    stderr="Failed to get response from primary LLM"
                )
            
            # Processar resposta baseada no tipo de tarefa
            from evolux_engine.schemas.contracts import TaskType, TaskDetailsCreateFile, ArtifactChange, ArtifactChangeType
            from evolux_engine.models.project_context import ArtifactState
            import os

            if task.type == TaskType.CREATE_FILE:
                details: TaskDetailsCreateFile = task.details
                relative_file_path = os.path.join("artifacts", details.file_path)
                self.file_service.save_file(relative_file_path, str(response))
                artifact_change = ArtifactChange(path=relative_file_path, change_type=ArtifactChangeType.CREATED)
                file_hash = self.file_service.get_file_hash(relative_file_path)
                self.project_context.update_artifact_state(
                    relative_file_path,
                    ArtifactState(path=relative_file_path, hash=file_hash, summary=f"Arquivo criado/sobrescrito: {details.file_path}")
                )
                await self.project_context.save_context()
                return ExecutionResult(exit_code=0, stdout=f"Arquivo {details.file_path} criado/atualizado.", artifacts_changed=[artifact_change])
            else:
                return ExecutionResult(
                    exit_code=0,
                    stdout=response[:1000],  # Truncar para logging
                    stderr=""
                )
            
        except Exception as e:
            logger.error(f"Error executing with primary LLM: {e}")
            return ExecutionResult(
                exit_code=1,
                stderr=f"Execution error: {str(e)}"
            )
    
    async def _validate_iteration_result(
        self,
        task: Task,
        execution_result: ExecutionResult
    ) -> ValidationResult:
        """Valida resultado da iteração usando LLM validador"""
        
        validation_prompt = f"""
Validate the following task execution with rigorous quality standards:

**Task:** {task.description}
**Acceptance Criteria:** {task.acceptance_criteria}

**Execution Result:**
- Exit Code: {execution_result.exit_code}
- Output: {execution_result.stdout[:500]}...
- Errors: {execution_result.stderr}

Rate the quality from 1-10 and provide detailed feedback.

Response format:
```json
{{
    "validation_passed": true/false,
    "confidence_score": 0.0-1.0,
    "quality_rating": 1-10,
    "checklist": {{
        "correctness": true/false,
        "completeness": true/false,
        "efficiency": true/false,
        "maintainability": true/false,
        "security": true/false
    }},
    "identified_issues": ["list of specific issues"],
    "suggested_improvements": ["list of specific improvements"],
    "critical_problems": ["list of critical problems that must be fixed"]
}}
```
"""
        
        try:
            messages = [
                {"role": "system", "content": "You are a rigorous code reviewer and quality assurance expert."},
                {"role": "user", "content": validation_prompt}
            ]
            
            from evolux_engine.llms.model_router import TaskCategory
            response = await self.validator_llm.generate_response(
                messages,
                category=TaskCategory.VALIDATION,
                max_tokens=3000,
                temperature=0.1,
                max_prompt_tokens=2048
            )

            if not response:
                logger.warning("Validation LLM returned no response. Returning default validation failure.")
                return ValidationResult(validation_passed=False, confidence_score=0.0, identified_issues=["Validation LLM failed to respond."])
            
            # Extrair dados estruturados
            json_str = extract_json_from_llm_response(response)
            if json_str:
                validation_data = json.loads(json_str)
                
                from evolux_engine.schemas.contracts import SemanticValidationChecklistItem
                checklist = []
                if "checklist" in validation_data:
                    for key, passed in validation_data["checklist"].items():
                        checklist.append(SemanticValidationChecklistItem(
                            item=key.replace("_", " ").title(),
                            passed=passed,
                            reasoning=f"Validation assessment: {passed}"
                        ))
                
                return ValidationResult(
                    validation_passed=validation_data.get("validation_passed", False),
                    confidence_score=validation_data.get("confidence_score", 0.5),
                    checklist=checklist,
                    identified_issues=validation_data.get("identified_issues", []),
                    suggested_improvements=validation_data.get("suggested_improvements", [])
                )
            
        except Exception as e:
            logger.error(f"Error in validation: {e}")
        
        # Fallback validation
        return ValidationResult(
            validation_passed=execution_result.exit_code == 0,
            confidence_score=0.5,
            checklist=[],
            identified_issues=[],
            suggested_improvements=[]
        )
    
    async def _get_reviewer_feedback(
        self,
        task: Task,
        execution_result: ExecutionResult,
        strategy: RefinementStrategy
    ) -> str:
        """Obtém feedback detalhado de um LLM revisor"""
        
        if strategy == RefinementStrategy.ADVERSARIAL_REVIEW:
            review_prompt = f"""
You are a critical code reviewer whose job is to find problems and areas for improvement. 
Be thorough and demanding in your review of this task execution:

**Task:** {task.description}
**Result:** {execution_result.stdout[:500]}...

Find every possible issue and suggest improvements. Be harsh but constructive.
Look for:
- Logic errors or bugs
- Security vulnerabilities  
- Performance issues
- Code quality problems
- Missing edge case handling
- Poor design decisions

Provide specific, actionable feedback.
"""
        else:
            review_prompt = f"""
You are an experienced technical reviewer. Provide constructive feedback on this task execution:

**Task:** {task.description}
**Result:** {execution_result.stdout[:500]}...

Provide balanced feedback covering:
- What was done well
- Areas for improvement
- Specific suggestions for enhancement
- Overall assessment

Be thorough but fair in your evaluation.
"""
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert technical reviewer focused on code quality and best practices."},
                {"role": "user", "content": review_prompt}
            ]
            
            from evolux_engine.llms.model_router import TaskCategory
            response = await self.reviewer_llm.generate_response(
                messages,
                category=TaskCategory.VALIDATION,
                max_tokens=2000,
                temperature=0.3,
                max_prompt_tokens=2048
            )
            
            return response or "No reviewer feedback available"
            
        except Exception as e:
            logger.error(f"Error getting reviewer feedback: {e}")
            return "Reviewer feedback unavailable due to error"
    
    def _calculate_quality_score(
        self,
        execution_result: ExecutionResult,
        validation_result: ValidationResult,
        reviewer_feedback: Optional[str]
    ) -> float:
        """Calcula pontuação de qualidade baseada em múltiplos fatores"""
        
        score = 0.0
        
        # Base score from execution success
        if execution_result.exit_code == 0:
            score += 3.0
        
        # Validation score
        score += validation_result.confidence_score * 4.0
        
        # Issues penalty
        issues_count = len(validation_result.identified_issues)
        score -= min(issues_count * 0.5, 2.0)
        
        # Reviewer feedback analysis (simplified)
        if reviewer_feedback:
            if "excellent" in reviewer_feedback.lower() or "great" in reviewer_feedback.lower():
                score += 1.0
            elif "poor" in reviewer_feedback.lower() or "bad" in reviewer_feedback.lower():
                score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _should_stop_refinement(
        self,
        current_iteration: RefinementIteration,
        quality_scores: List[float]
    ) -> bool:
        """Determina se deve parar o refinamento"""
        
        # Parar se atingiu qualidade desejada
        if current_iteration.quality_score >= self.quality_threshold:
            return True
        
        # Parar se não há melhoria significativa nas últimas iterações
        if len(quality_scores) >= 3:
            recent_scores = quality_scores[-3:]
            improvement = max(recent_scores) - min(recent_scores)
            if improvement < self.convergence_threshold:
                logger.info("Stopping due to convergence - no significant improvement")
                return True
        
        return False
    
    async def _prepare_next_iteration(
        self,
        task: Task,
        current_iteration: RefinementIteration
    ):
        """Prepara contexto para próxima iteração"""
        
        # Adicionar insights da iteração atual ao contexto global
        if current_iteration.improvement_suggestions:
            self.prompt_engine.set_global_context(
                f"iteration_{current_iteration.iteration_number}_insights",
                current_iteration.improvement_suggestions
            )
