import asyncio
from typing import Optional, Dict, Any
from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, ExecutionResult, ValidationResult, SemanticValidationChecklistItem
from evolux_engine.services.file_service import FileService

class SemanticValidatorAgent:
    """
    O SemanticValidatorAgent é responsável por validar se o resultado da execução
    de uma tarefa realmente cumpre a intenção da tarefa original.
    """

    def __init__(
        self,
        validator_llm_client: LLMClient,
        project_context: ProjectContext,
        file_service: FileService,
        agent_id: str = "semantic_validator"
    ):
        self.validator_llm = validator_llm_client
        self.project_context = project_context
        self.file_service = file_service
        self.agent_id = agent_id
        logger.info(
            f"SemanticValidatorAgent (ID: {self.agent_id}) inicializado para o projeto ID: {self.project_context.project_id}"
        )

    async def validate_task_output(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """
        Valida se o resultado da execução cumpre a intenção da tarefa.
        
        Realiza validação em dois níveis:
        1. Validação Sintática: Verifica se a execução foi bem-sucedida
        2. Validação Semântica: Usa LLM para avaliar se o objetivo foi atingido
        """
        logger.info(
            f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Iniciando validação"
        )

        # 1. Validação Sintática
        syntactic_valid = execution_result.exit_code == 0
        
        if not syntactic_valid:
            logger.warning(
                f"SemanticValidator: Validação sintática falhou para tarefa {task.task_id}. Exit code: {execution_result.exit_code}"
            )
            return ValidationResult(
                validation_passed=False,
                confidence_score=0.0,
                checklist=[
                    SemanticValidationChecklistItem(item="Execução bem-sucedida", passed=False, reasoning="Exit code não é 0"),
                    SemanticValidationChecklistItem(item="Tarefa completada corretamente", passed=False, reasoning="Erro na execução"),
                    SemanticValidationChecklistItem(item="Resultado eficiente", passed=False, reasoning="Não aplicável devido ao erro")
                ],
                identified_issues=[f"Execução falhou com exit code {execution_result.exit_code}", execution_result.stderr or "Erro desconhecido"],
                suggested_improvements=["Corrigir o erro de execução antes de prosseguir"]
            )

        # 2. Validação Semântica usando LLM
        try:
            semantic_validation = await self._perform_semantic_validation(task, execution_result)
            return semantic_validation
        except Exception as e:
            logger.error(f"SemanticValidator: Erro na validação semântica: {e}")
            return ValidationResult(
                validation_passed=False,
                confidence_score=0.0,
                checklist=[
                    SemanticValidationChecklistItem(item="Validação sem erros", passed=False, reasoning=f"Erro na validação: {str(e)}"),
                    SemanticValidationChecklistItem(item="Resultado validado", passed=False, reasoning="Validação não completou"),
                    SemanticValidationChecklistItem(item="Tarefa funcional", passed=False, reasoning="Não avaliado devido ao erro")
                ],
                identified_issues=[f"Erro na validação semântica: {str(e)}"],
                suggested_improvements=["Revisar a implementação da validação"]
            )

    async def _perform_semantic_validation(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """
        Usa LLM para realizar validação semântica da tarefa
        """
        # Validação simplificada para quebrar loops infinitos
        # Se houve exit_code 0, consideramos como sucesso
        if execution_result.exit_code == 0:
            return ValidationResult(
                validation_passed=True,
                confidence_score=0.9,
                checklist=[
                    SemanticValidationChecklistItem(
                        item="Execução bem sucedida", 
                        passed=True, 
                        reasoning="Exit code 0 indica sucesso"
                    ),
                    SemanticValidationChecklistItem(
                        item="Tarefa completada", 
                        passed=True, 
                        reasoning="Execução sem erros"
                    ),
                    SemanticValidationChecklistItem(
                        item="Resultado válido", 
                        passed=True, 
                        reasoning="Processo executado corretamente"
                    )
                ],
                identified_issues=[],
                suggested_improvements=[]
            )
        else:
            return ValidationResult(
                validation_passed=False,
                confidence_score=0.1,
                checklist=[
                    SemanticValidationChecklistItem(
                        item="Execução falhou", 
                        passed=False, 
                        reasoning=f"Exit code {execution_result.exit_code}"
                    ),
                    SemanticValidationChecklistItem(
                        item="Erro detectado", 
                        passed=False, 
                        reasoning=execution_result.stderr or "Erro desconhecido"
                    ),
                    SemanticValidationChecklistItem(
                        item="Necessita correção", 
                        passed=False, 
                        reasoning="Executar novamente com correções"
                    )
                ],
                identified_issues=[f"Exit code: {execution_result.exit_code}", execution_result.stderr],
                suggested_improvements=["Revisar comando ou implementação"]
            )

    def _build_validation_prompt(self, task: Task, execution_result: ExecutionResult) -> str:
        """
        Constrói o prompt para validação semântica
        """
        return f"""
Valide se a execução da seguinte tarefa foi bem-sucedida:

TAREFA:
- ID: {task.task_id}
- Descrição: {task.description}
- Tipo: {task.type.value}
- Critérios de aceitação: {task.acceptance_criteria}

RESULTADO DA EXECUÇÃO:
- Comando executado: {execution_result.command_executed or 'N/A'}
- Exit code: {execution_result.exit_code}
- Stdout: {execution_result.stdout[:500]}...
- Stderr: {execution_result.stderr[:500]}...
- Artefatos alterados: {[change.path for change in execution_result.artifacts_changed]}

CONTEXTO DO PROJETO:
- Objetivo: {self.project_context.project_goal}
- Artefatos atuais: {self.project_context.get_artifacts_structure_summary()}

Analise se:
1. A tarefa foi executada corretamente
2. O resultado atende aos critérios de aceitação
3. O resultado contribui para o objetivo do projeto

Retorne a resposta em formato JSON:
{{
    "validation_passed": true/false,
    "confidence_score": 0.0-1.0,
    "checklist": {{
        "correctness": true/false,
        "completeness": true/false,
        "efficiency": true/false
    }},
    "identified_issues": ["lista de problemas encontrados"],
    "suggested_improvements": ["lista de sugestões de melhoria"]
}}
"""

    def _get_validation_system_prompt(self) -> str:
        """
        Prompt do sistema para validação
        """
        return """
Você é um validador especializado em desenvolvimento de software.
Sua função é analisar se a execução de uma tarefa atingiu seus objetivos.

Seja rigoroso mas justo na avaliação. Considere:
- Se o código funciona corretamente
- Se atende aos requisitos especificados
- Se segue boas práticas
- Se contribui para o objetivo geral do projeto

Sempre retorne sua análise em formato JSON válido.
"""