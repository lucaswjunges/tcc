import asyncio
import json
from typing import List, Dict, Any, Optional

from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext, Task, ArtifactState
from evolux_engine.schemas.contracts import (
    ExecutionResult,
    ValidationResult,
    SemanticValidationChecklistItem,
    LLMCallMetrics,
    TaskType
)
from evolux_engine.services.file_service import FileService

# Prompts do validator_prompts.py (ou poderiam estar em executor_prompts.py)
# No exemplo anterior, get_artifact_validation_prompt estava em executor_prompts
# Vamos assumir que será movido para um validator_prompts.py ou importado corretamente.
from .validator_prompts import (
    VALIDATION_SYSTEM_PROMPT,
    get_artifact_validation_prompt,
    get_command_output_validation_prompt,
    get_project_state_validation_prompt,
)


class SemanticValidatorAgent:
    """
    O SemanticValidatorAgent avalia se a execução de uma tarefa
    atendeu aos seus critérios semânticos e contribuiu para o objetivo do projeto.
    """

    def __init__(
        self,
        validator_llm_client: LLMClient,
        project_context: ProjectContext,
        file_service: FileService,
        agent_id: str,
    ):
        self.validator_llm = validator_llm_client
        self.project_context = project_context
        self.file_service = file_service
        self.agent_id = agent_id
        logger.info(
            f"SemanticValidatorAgent (ID: {self.agent_id}) inicializado para o projeto ID: {self.project_context.project_id}"
        )

    async def _invoke_llm_for_validation(
        self, messages: List[Dict[str, str]], task_id_for_log: str
    ) -> Optional[Dict[str, Any]]:
        """
        Invoca o LLM para realizar a validação semântica.
        Espera uma resposta JSON com os campos de ValidationResult.
        """
        try:
            start_time = asyncio.get_event_loop().time()
            model_to_use = self.project_context.engine_config.default_validator_model or \
                           self.validator_llm.model_name

            response_text = await self.validator_llm.generate_response(
                messages,
                model_override=model_to_use,
                timeout=240, # Validação pode precisar de mais tempo
                max_tokens=2048
            )
            latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # TODO: Registrar LLMCallMetrics no ProjectContext.iteration_history
            # Atualmente, este método retorna o dict parseado, o Orchestrator poderia construir o objeto LLMCallMetrics

            if not response_text:
                logger.error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): Nenhuma resposta da LLM de Validação.")
                return None

            logger.debug(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): Resposta bruta LLM Validação: {response_text[:500]}...")

            json_start_index = response_text.find("{")
            json_end_index = response_text.rfind("}") + 1

            if json_start_index != -1 and json_end_index != -1:
                json_str = response_text[json_start_index:json_end_index]
                try:
                    parsed_response = json.loads(json_str)
                    return parsed_response # Retorna o dict completo para ser parseado em ValidationResult
                except json.JSONDecodeError as e:
                    error_msg = f"Falha ao decodificar JSON da LLM de Validação. Erro: {e}. JSON Tentado: {json_str}"
                    logger.error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): {error_msg}")
                    # self.file_service.save_file(self.project_context.get_log_path(f"validator_error_json_decode_{task_id_for_log}_{uuid.uuid4()}.txt"), error_msg + "\n\nRAW_RESPONSE:\n" + response_text)
                    return None
            else:
                error_msg = f"Nenhum JSON válido encontrado na resposta da LLM de Validação. Resposta: {response_text[:500]}..."
                logger.error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): {error_msg}")
                # self.file_service.save_file(self.project_context.get_log_path(f"validator_error_no_json_{task_id_for_log}_{uuid.uuid4()}.txt"), error_msg + "\n\nRAW_RESPONSE:\n" + response_text)
                return None

        except asyncio.TimeoutError:
            logger.error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): Timeout ao consultar LLM de Validação.")
            return None
        except Exception as e:
            logger.opt(exception=True).error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task_id_for_log}): Erro inesperado ao consultar LLM de Validação.")
            return None


    async def validate_task_output(
        self, task: Task, execution_result: ExecutionResult
    ) -> ValidationResult:
        """
        Valida o resultado da execução de uma tarefa contra seus critérios de aceitação
        e o objetivo geral do projeto.
        """
        logger.info(
            f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Iniciando validação semântica."
        )

        if task.type in [TaskType.CREATE_FILE, TaskType.MODIFY_FILE, TaskType.DELETE_FILE]:
            # Validação focada em artefatos de arquivo
            # Pegar o artefato principal afetado pela tarefa. Para CREATE/MODIFY, é o arquivo em details.file_path.
            # Para DELETE, o artefato não existe mais, então a validação pode ser sobre o estado.
            
            artifact_path_to_validate: Optional[str] = None
            artifact_content: Optional[str] = None

            if task.type != TaskType.DELETE_FILE and task.details and hasattr(task.details, 'file_path'):
                artifact_path_to_validate = task.details.file_path #type: ignore
                full_artifact_path = self.project_context.get_artifact_path(artifact_path_to_validate)
                if os.path.exists(full_artifact_path):
                    try:
                        artifact_content = self.file_service.read_file(full_artifact_path)
                    except Exception as e:
                        logger.error(f"SemanticValidator: Erro ao ler artefato {full_artifact_path} para validação: {e}")
                        return ValidationResult(validation_passed=False, identified_issues=[f"Erro ao ler artefato para validação: {e}"])
                elif task.type == TaskType.CREATE_FILE: # Se era pra criar e não existe, falhou
                    logger.warning(f"SemanticValidator: Artefato {full_artifact_path} que deveria ter sido criado não existe.")
                    return ValidationResult(validation_passed=False, identified_issues=[f"Artefato {artifact_path_to_validate} não foi criado."])
            
            if artifact_path_to_validate and artifact_content is not None:
                user_prompt = get_artifact_validation_prompt(
                    artifact_path=artifact_path_to_validate,
                    artifact_content=artifact_content,
                    validation_criteria=task.acceptance_criteria,
                    project_goal=self.project_context.project_goal,
                    project_type=self.project_context.project_type
                )
            elif task.type == TaskType.DELETE_FILE and task.details and hasattr(task.details, 'file_path'):
                # Validação de que o arquivo foi deletado.
                # O prompt precisa ser adaptado para validar a ausência e o estado.
                artifact_path_deleted = task.details.file_path #type: ignore
                full_artifact_path_deleted = self.project_context.get_artifact_path(artifact_path_deleted)
                if not os.path.exists(full_artifact_path_deleted):
                    # Se o critério de aceitação for apenas 'arquivo deletado', pode ser True aqui.
                    # Mas uma LLM pode verificar se o delete teve efeitos colaterais ou se era esperado.
                    logger.info(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Arquivo {artifact_path_deleted} foi deletado. Critério de aceitação: '{task.acceptance_criteria}'")
                    # Para simplificar, se o arquivo foi deletado e o critério é simples, podemos assumir sucesso.
                    # Em casos mais complexos, a LLM ainda seria útil.
                    if "deletado" in task.acceptance_criteria.lower() or "removido" in task.acceptance_criteria.lower():
                         return ValidationResult(validation_passed=True, checklist=[SemanticValidationChecklistItem(item=f"Arquivo {artifact_path_deleted} deletado.", passed=True)])

                # Se chegou aqui, ou o arquivo ainda existe ou a validação é mais complexa.
                user_prompt = get_project_state_validation_prompt(
                    task_description=task.description,
                    acceptance_criteria=task.acceptance_criteria,
                    project_goal=self.project_context.project_goal,
                    project_artifacts_summary=self.project_context.get_artifacts_structure_summary(),
                    execution_stdout=execution_result.stdout,
                    execution_stderr=execution_result.stderr
                )
            else: # Caso genérico para validação baseada no estado, sem conteúdo de arquivo específico
                user_prompt = get_project_state_validation_prompt(
                    task_description=task.description,
                    acceptance_criteria=task.acceptance_criteria,
                    project_goal=self.project_context.project_goal,
                    project_artifacts_summary=self.project_context.get_artifacts_structure_summary(),
                    execution_stdout=execution_result.stdout,
                    execution_stderr=execution_result.stderr
                )

        elif task.type == TaskType.EXECUTE_COMMAND:
            user_prompt = get_command_output_validation_prompt(
                command_executed=execution_result.command_executed or task.description,
                stdout=execution_result.stdout or "",
                stderr=execution_result.stderr or "",
                exit_code=execution_result.exit_code,
                validation_criteria=task.acceptance_criteria,
                project_goal=self.project_context.project_goal,
                project_artifacts_summary=self.project_context.get_artifacts_structure_summary()
            )
        elif task.type == TaskType.VALIDATE_ARTIFACT: # Tarefa explicitamente de validação
            if task.details and hasattr(task.details, 'artifact_path') and task.details.artifact_path: #type: ignore
                target_artifact_path = task.details.artifact_path #type: ignore
                full_target_path = self.project_context.get_artifact_path(target_artifact_path)
                if os.path.exists(full_target_path):
                    content = self.file_service.read_file(full_target_path)
                    user_prompt = get_artifact_validation_prompt(
                        artifact_path=target_artifact_path,
                        artifact_content=content,
                        validation_criteria=task.acceptance_criteria, # Ou task.details.validation_criteria
                        project_goal=self.project_context.project_goal,
                        project_type=self.project_context.project_type
                    )
                else:
                    return ValidationResult(validation_passed=False, identified_issues=[f"Artefato {target_artifact_path} especificado para validação não foi encontrado."])
            else: # Validação de estado geral do projeto
                 user_prompt = get_project_state_validation_prompt(
                    task_description="Validação geral do estado do projeto.", # Ou task.description
                    acceptance_criteria=task.acceptance_criteria, # Ou task.details.validation_criteria
                    project_goal=self.project_context.project_goal,
                    project_artifacts_summary=self.project_context.get_artifacts_structure_summary()
                )
        else:
            logger.warning(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Tipo de tarefa {task.type.value} não possui lógica de validação semântica específica. Assumindo sucesso se a execução teve exit_code 0.")
            if execution_result.success:
                return ValidationResult(validation_passed=True, checklist=[SemanticValidationChecklistItem(item="Execução da tarefa bem-sucedida (exit code 0). Validação semântica não aplicável para este tipo.", passed=True)])
            else:
                return ValidationResult(validation_passed=False, identified_issues=[f"Execução da tarefa falhou (exit code {execution_result.exit_code}). Validação semântica não aplicável para este tipo."])

        messages = [{"role": "system", "content": VALIDATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]
        
        llm_validation_dict = await self._invoke_llm_for_validation(messages, task.task_id)

        if not llm_validation_dict:
            return ValidationResult(
                validation_passed=False,
                identified_issues=["Falha ao obter resposta da LLM de validação ou resposta malformada."]
            )

        try:
            # Parsear para o objeto Pydantic
            # Os prompts pedem chaves específicas, então esperamos que elas estejam lá
            validation_result = ValidationResult(**llm_validation_dict)
            logger.info(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Validação concluída. Passou: {validation_result.validation_passed}")
            return validation_result
        except Exception as e: # Pydantic ValidationError, etc.
            logger.opt(exception=True).error(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Erro ao parsear resultado da validação da LLM: {llm_validation_dict}. Erro: {e}")
            return ValidationResult(
                validation_passed=False,
                identified_issues=[f"Erro ao parsear resposta da LLM de validação: {e}. Resposta recebida: {str(llm_validation_dict)[:500]}..."]
            )


# Arquivo evolux_engine/src/agents/validator_prompts.py (ou pode ser parte do executor_prompts.py)
# ------------------------------------------------------------------------------------
# Prompts para Validação (a serem usados pelo SemanticValidatorAgent)
# ------------------------------------------------------------------------------------
VALIDATION_SYSTEM_PROMPT = """
Você é uma Inteligência Artificial especialista em análise e validação de artefatos de projeto (código, documentos, configurações, etc.) e resultados de comandos.
Sua tarefa é avaliar o item fornecido (conteúdo de arquivo, saída de comando, ou estado geral do projeto) contra os critérios de aceitação especificados e o objetivo geral do projeto.
Seja crítico e detalhado na sua análise.
Sua resposta DEVE ser um objeto JSON com as seguintes chaves obrigatórias:
  - `validation_passed`: (boolean) True se o item atende a todos os critérios principais, False caso contrário.
E as seguintes chaves opcionais, mas altamente recomendadas:
  - `confidence_score`: (float, 0.0 a 1.0) Sua confiança na avaliação.
  - `checklist`: (list of objects) Uma lista de itens verificados, cada um com {'item': 'descrição do critério', 'passed': boolean, 'reasoning': 'justificativa concisa (1-2 frases) para o status passed/failed do item'}.
  - `identified_issues`: (list of strings) Uma lista de problemas específicos encontrados, se `validation_passed` for False.
  - `suggested_improvements`: (list of strings) Sugestões concisas e acionáveis para corrigir os problemas ou melhorar o item.

NÃO adicione nenhum texto, explicação ou markdown fora da estrutura JSON.
"""

def get_artifact_validation_prompt(
    artifact_path: str,
    artifact_content: str,
    validation_criteria: str,
    project_goal: str,
    project_type: Optional[str] = None,
) -> str:
    prompt_lines = [
        f"CONTEXTO DO PROJETO:",
        f"- Objetivo Geral do Projeto: '{project_goal}'.",
    ]
    if project_type:
        prompt_lines.append(f"- Tipo do Projeto: '{project_type}'.")

    prompt_lines.append(f"\nTAREFA DE VALIDAÇÃO:")
    prompt_lines.append(f"Avalie o artefato '{artifact_path}' com base nos seguintes critérios de aceitação:")
    prompt_lines.append(f"Critérios de Aceitação: \"{validation_criteria}\"")

    prompt_lines.append(f"\nCONTEÚDO DO ARTEFATO '{artifact_path}' A SER VALIDADO (pode estar truncado se muito longo):")
    prompt_lines.append("```")
    # Truncar conteúdo se for excessivamente longo para caber no prompt, mas dar indicação
    max_content_len = 8000
    if len(artifact_content) > max_content_len:
        prompt_lines.append(artifact_content[:max_content_len] + "\n... (CONTEÚDO TRUNCADO)")
    else:
        prompt_lines.append(artifact_content)
    prompt_lines.append("```")

    prompt_lines.append(
        "\nAVALIAÇÃO REQUERIDA:\n"
        "Forneça sua avaliação APENAS como um objeto JSON no formato especificado no system prompt. "
        "Analise se o conteúdo do artefato satisfaz os critérios de aceitação E contribui para o objetivo do projeto. "
        "No campo 'checklist', detalhe cada sub-item implícito nos critérios de aceitação e seu status."
    )
    return "\n\n".join(prompt_lines)

def get_command_output_validation_prompt(
    command_executed: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    validation_criteria: str, # Originalmente os 'acceptance_criteria' da tarefa EXECUTE_COMMAND
    project_goal: str,
    project_artifacts_summary: Optional[str] = None
) -> str:
    prompt_lines = [
        f"CONTEXTO DO PROJETO:",
        f"- Objetivo Geral do Projeto: '{project_goal}'.",
    ]
    if project_artifacts_summary:
        prompt_lines.append(f"\n- Estrutura de Artefatos Atual (pode ter mudado após o comando):\n{project_artifacts_summary}")

    prompt_lines.append(f"\nTAREFA DE VALIDAÇÃO:")
    prompt_lines.append(f"Avalie o resultado da execução do comando '{command_executed}' com base nos seguintes critérios originais da tarefa:")
    prompt_lines.append(f"Critérios de Aceitação da Tarefa: \"{validation_criteria}\"")

    prompt_lines.append(f"\nRESULTADO DA EXECUÇÃO DO COMANDO:")
    prompt_lines.append(f"- Comando Executado: {command_executed}")
    prompt_lines.append(f"- Código de Saída (Exit Code): {exit_code}")
    prompt_lines.append(f"- Saída Padrão (stdout) (pode estar VAZIA ou truncada se longa):")
    prompt_lines.append("```stdout")
    prompt_lines.append(stdout[:2000] if stdout else "(vazio)") # Truncar
    if stdout and len(stdout) > 2000: prompt_lines.append("... (stdout truncado)")
    prompt_lines.append("```")
    prompt_lines.append(f"- Saída de Erro (stderr) (pode estar VAZIA ou truncada se longa):")
    prompt_lines.append("```stderr")
    prompt_lines.append(stderr[:2000] if stderr else "(vazio)") # Truncar
    if stderr and len(stderr) > 2000: prompt_lines.append("... (stderr truncado)")
    prompt_lines.append("```")

    prompt_lines.append(
        "\nAVALIAÇÃO REQUERIDA:\n"
        "Forneça sua avaliação APENAS como um objeto JSON no formato especificado no system prompt. "
        "Analise se a execução do comando (código de saída, stdout, stderr e o estado implícito dos artefatos) "
        "satisfaz os critérios de aceitação da tarefa E contribuiu para o objetivo do projeto. "
        "No campo 'checklist', detalhe cada sub-item implícito nos critérios de aceitação e seu status."
    )
    return "\n\n".join(prompt_lines)


def get_project_state_validation_prompt(
    task_description: str, # Descrição da tarefa que levou a este estado ou uma descrição geral da validação
    acceptance_criteria: str,
    project_goal: str,
    project_artifacts_summary: Optional[str] = None,
    execution_stdout: Optional[str] = None, # Saída de uma execução anterior, se relevante
    execution_stderr: Optional[str] = None, # Saída de erro de uma execução anterior, se relevante
) -> str:
    prompt_lines = [
        f"CONTEXTO DO PROJETO:",
        f"- Objetivo Geral do Projeto: '{project_goal}'.",
    ]
    if project_artifacts_summary:
        prompt_lines.append(f"\n- Estrutura de Artefatos Atual:\n{project_artifacts_summary}")

    prompt_lines.append(f"\nTAREFA DE VALIDAÇÃO DE ESTADO:")
    prompt_lines.append(f"Avalie o estado atual do projeto (considerando a última ação: '{task_description}') com base nos seguintes critérios:")
    prompt_lines.append(f"Critérios de Aceitação/Validação: \"{acceptance_criteria}\"")

    if execution_stdout or execution_stderr:
        prompt_lines.append(f"\nSaída da Execução Anterior (se aplicável):")
        if execution_stdout:
            prompt_lines.append(f"  - Stdout: {execution_stdout[:1000]}...")
        if execution_stderr:
            prompt_lines.append(f"  - Stderr: {execution_stderr[:1000]}...")

    prompt_lines.append(
        "\nAVALIAÇÃO REQUERIDA:\n"
        "Forneça sua avaliação APENAS como um objeto JSON no formato especificado no system prompt. "
        "Analise se o estado atual dos artefatos e os resultados da última ação satisfazem os critérios de validação. "
        "No campo 'checklist', detalhe cada sub-item implícito nos critérios e seu status."
    )
    return "\n\n".join(prompt_lines)
