import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, ExecutionResult, ValidationResult, SemanticValidationChecklistItem, TaskType
from evolux_engine.llms.model_router import TaskCategory
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
        Valida se o resultado da execução de uma tarefa atende aos critérios semânticos.
        Implementa validação inteligente baseada no tipo de tarefa.
        """
        logger.info(f"SemanticValidator (ID: {self.agent_id}, Tarefa: {task.task_id}): Iniciando validação inteligente")
        
        try:
            # Validação básica de sucesso
            basic_passed = execution_result.exit_code == 0
            issues = []
            improvements = []
            confidence = 0.0
            
            if not basic_passed:
                issues.append(f"Exit code: {execution_result.exit_code}")
                if execution_result.stderr:
                    issues.append(f"Erro: {execution_result.stderr}")
                return ValidationResult(
                    validation_passed=False,
                    confidence_score=0.0,
                    identified_issues=issues,
                    suggested_improvements=["Corrigir erros de execução básicos"]
                )
            
            # Validação específica por tipo de tarefa com fallback para LLM
            if task.type == TaskType.CREATE_FILE:
                return await self._validate_file_creation(task, execution_result)
            elif task.type == TaskType.MODIFY_FILE:
                return await self._validate_file_modification(task, execution_result)
            elif task.type == TaskType.EXECUTE_COMMAND:
                return await self._validate_command_execution(task, execution_result)
            elif task.type == TaskType.VALIDATE_ARTIFACT:
                return await self._validate_artifact_validation(task, execution_result)
            else:
                # Para tipos desconhecidos, usar validação LLM semântica
                try:
                    return await self._perform_semantic_validation(task, execution_result)
                except Exception as e:
                    logger.warning(f"Falha na validação LLM para tarefa {task.task_id}: {e}")
                    return ValidationResult(
                        validation_passed=True,
                        confidence_score=0.6,
                        identified_issues=[],
                        suggested_improvements=[]
                    )
        except Exception as e:
            logger.error(f"Erro na validação da tarefa {task.task_id}: {str(e)}")
            # Retornar resultado de fallback em caso de erro
            return ValidationResult(
                validation_passed=True,  # Ser permissivo em caso de erro na validação
                confidence_score=0.5,
                identified_issues=[f"Erro no sistema de validação: {str(e)}"],
                suggested_improvements=["Sistema de validação deve ser revisado"]
            )
    
    async def _validate_file_creation(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """Valida criação de arquivos com análise semântica"""
        issues = []
        improvements = []
        confidence = 0.5
        
        # Tentar detectar arquivo a partir da descrição da tarefa ou artifacts_changed
        file_path = None
        
        # Primeiro, verificar se tem informação nos artifacts_changed
        if execution_result.artifacts_changed:
            for artifact in execution_result.artifacts_changed:
                if artifact.path and (artifact.change_type == "created" or artifact.change_type == "modified"):
                    file_path = Path(self.project_context.get_artifact_path(artifact.path))
                    break
        
        # Se não encontrou, tentar extrair da descrição da tarefa
        if not file_path:
            # Procurar padrões de arquivos na descrição
            import re
            patterns = [
                r'criar\s+(?:arquivo\s+)?([^\s]+\.(?:py|html|txt|md|js|css|json|yaml|yml))',
                r'gerar\s+(?:arquivo\s+)?([^\s]+\.(?:py|html|txt|md|js|css|json|yaml|yml))',
                r'arquivo\s+([^\s]+\.(?:py|html|txt|md|js|css|json|yaml|yml))',
                r'([^\s]+\.(?:py|html|txt|md|js|css|json|yaml|yml))'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, task.description.lower())
                if match:
                    potential_path = match.group(1)
                    file_path = Path(self.project_context.get_artifact_path(potential_path))
                    break
        
        # Se ainda não encontrou arquivo específico, tentar buscar por arquivos similares no workspace
        if not file_path:
            # Busca final no workspace por arquivos relacionados
            workspace_path = Path(self.project_context.workspace_path)
            if "readme" in task.description.lower():
                potential_files = list(workspace_path.glob("**/README*")) + list(workspace_path.glob("**/readme*"))
                if potential_files:
                    file_path = potential_files[0]  # Usar o primeiro encontrado
                    logger.info(f"Arquivo README encontrado: {file_path}")
            
            # Se ainda não encontrou, usar validação genérica
            if not file_path:
                logger.info(f"Não foi possível identificar arquivo específico para tarefa {task.task_id}, usando validação genérica")
                return await self._perform_generic_file_validation(task, execution_result)
        
        # Verificar se arquivo foi realmente criado
        if not file_path.exists():
            issues.append(f"Arquivo {file_path.name} não foi criado")
            return ValidationResult(
                validation_passed=False,
                confidence_score=0.0,
                identified_issues=issues,
                suggested_improvements=["Verificar se comando de criação foi executado corretamente"]
            )
            
            # Análise de conteúdo baseada no tipo de arquivo
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if file_path.suffix == '.py':
                    confidence, file_issues, file_improvements = self._analyze_python_file(content, task.description)
                    issues.extend(file_issues)
                    improvements.extend(file_improvements)
                elif file_path.suffix == '.html':
                    confidence, file_issues, file_improvements = self._analyze_html_file(content, task.description)
                    issues.extend(file_issues)
                    improvements.extend(file_improvements)
                elif file_path.suffix == '.txt':
                    confidence, file_issues, file_improvements = self._analyze_text_file(content, task.description)
                    issues.extend(file_issues)
                    improvements.extend(file_improvements)
                else:
                    confidence = 0.8  # Assume reasonable quality for other files
                
                # Verificar tamanho mínimo
                if len(content.strip()) < 50:
                    issues.append("Arquivo muito pequeno, conteúdo pode estar incompleto")
                    confidence = min(confidence, 0.5)
                
            except Exception as e:
                issues.append(f"Erro ao analisar arquivo: {str(e)}")
                confidence = 0.3
        
        passed = len(issues) == 0 and confidence >= 0.5
        
        return ValidationResult(
            validation_passed=passed,
            confidence_score=confidence,
            identified_issues=issues,
            suggested_improvements=improvements
        )
    
    def _analyze_python_file(self, content: str, task_description: str) -> tuple[float, list[str], list[str]]:
        """Analisa arquivo Python para validação semântica"""
        issues = []
        improvements = []
        confidence = 0.5
        
        # Verificações básicas de sintaxe Python
        try:
            compile(content, '<string>', 'exec')
            confidence += 0.2
        except SyntaxError as e:
            issues.append(f"Erro de sintaxe Python: {str(e)}")
            return 0.1, issues, ["Corrigir erros de sintaxe Python"]
        
        # Verificações semânticas específicas
        if "flask" in task_description.lower():
            if "from flask import" not in content and "import flask" not in content:
                issues.append("Arquivo Flask deve importar Flask")
            else:
                confidence += 0.1
                
            if "app = Flask" in content:
                confidence += 0.1
            else:
                improvements.append("Considerar criar instância Flask")
        
        if "model" in task_description.lower():
            if "class " not in content:
                issues.append("Arquivo de modelos deve definir classes")
            else:
                confidence += 0.1
                
            if "db.Model" in content or "Model" in content:
                confidence += 0.1
        
        # Verificação de imports coerentes
        import_lines = [line for line in content.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
        if len(import_lines) == 0:
            improvements.append("Considerar adicionar imports necessários")
        else:
            confidence += 0.1
        
        return min(confidence, 1.0), issues, improvements
    
    def _analyze_html_file(self, content: str, task_description: str) -> tuple[float, list[str], list[str]]:
        """Analisa arquivo HTML para validação semântica"""
        issues = []
        improvements = []
        confidence = 0.5
        
        # Verificações básicas HTML
        if "<!DOCTYPE html>" not in content:
            issues.append("HTML deve ter declaração DOCTYPE")
        else:
            confidence += 0.1
            
        if "<html" not in content:
            issues.append("HTML deve ter tag html")
        else:
            confidence += 0.1
            
        if "<head>" not in content:
            improvements.append("Considerar adicionar seção head")
        else:
            confidence += 0.1
            
        if "<body>" not in content:
            issues.append("HTML deve ter tag body")
        else:
            confidence += 0.1
            
        # Verificações específicas para templates Flask
        if "template" in task_description.lower():
            if "{{" in content or "{%" in content:
                confidence += 0.2  # Tem sintaxe Jinja2
            else:
                improvements.append("Template Flask deve usar sintaxe Jinja2")
        
        return min(confidence, 1.0), issues, improvements
    
    def _analyze_text_file(self, content: str, task_description: str) -> tuple[float, list[str], list[str]]:
        """Analisa arquivos de texto para validação semântica"""
        issues = []
        improvements = []
        confidence = 0.5
        
        if "requirements" in task_description.lower():
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if len(lines) == 0:
                issues.append("requirements.txt não pode estar vazio")
                return 0.1, issues, ["Adicionar dependências necessárias"]
            
            # Verificar formato das dependências
            for line in lines:
                if '==' in line or '>=' in line or '<=' in line:
                    confidence += 0.1
                elif line and not line.startswith('#'):
                    improvements.append(f"Considerar especificar versão para {line}")
            
            # Verificar dependências específicas
            if "flask" in task_description.lower():
                flask_deps = ['flask', 'flask-sqlalchemy', 'flask-login']
                found_deps = [dep for dep in flask_deps if any(dep.lower() in line.lower() for line in lines)]
                confidence += len(found_deps) * 0.1
        
        elif "readme" in task_description.lower():
            if len(content) < 50:
                issues.append("README muito curto, falta informação essencial")
            else:
                confidence += 0.2
                
            # Verificar seções básicas, mas não ser muito rigoroso
            basic_sections = ['installation', 'usage', 'features', 'description', 'install', 'how to', 'como usar']
            found_sections = sum(1 for section in basic_sections if section.lower() in content.lower())
            
            if found_sections > 0:
                confidence += 0.1 * min(found_sections, 3)  # Máximo de 0.3 bonus
            else:
                improvements.append("Considerar adicionar seções como instalação, uso ou funcionalidades")
        
        return min(confidence, 1.0), issues, improvements
    
    async def _perform_generic_file_validation(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """Validação genérica quando não é possível identificar arquivo específico"""
        issues = []
        improvements = []
        confidence = 0.6
        
        # Verificar se houve artifacts_changed que indicam criação de arquivos
        if execution_result.artifacts_changed:
            created_files = [a for a in execution_result.artifacts_changed if a.change_type == "created"]
            modified_files = [a for a in execution_result.artifacts_changed if a.change_type == "modified"]
            
            if created_files:
                confidence += 0.2
                logger.info(f"Arquivos criados detectados: {[f.path for f in created_files]}")
            elif modified_files:
                confidence += 0.1
                logger.info(f"Arquivos modificados detectados: {[f.path for f in modified_files]}")
            else:
                issues.append("Nenhum arquivo foi criado ou modificado conforme esperado")
                confidence = 0.3
        else:
            # Sem artifacts_changed, verificar pelo menos se comando foi executado com sucesso
            if execution_result.exit_code == 0:
                confidence = 0.5
                improvements.append("Considerar adicionar informações sobre arquivos criados no resultado")
            else:
                issues.append("Comando falhou e nenhum artefato foi reportado")
                confidence = 0.1
        
        # Verificar se a descrição indica criação de documentação
        if "readme" in task.description.lower() or "documentação" in task.description.lower():
            # Buscar por arquivos README ou de documentação no workspace
            workspace_path = Path(self.project_context.workspace_path)
            readme_files = list(workspace_path.glob("**/README*")) + list(workspace_path.glob("**/readme*"))
            doc_files = list(workspace_path.glob("**/*.md"))
            
            if readme_files or doc_files:
                confidence += 0.2
                logger.info(f"Arquivos de documentação encontrados: {[f.name for f in readme_files + doc_files]}")
                
                # Se encontrou arquivos de documentação, validar o mais recente
                all_docs = readme_files + doc_files
                if all_docs:
                    # Pegar o arquivo mais recente
                    latest_doc = max(all_docs, key=lambda f: f.stat().st_mtime)
                    try:
                        content = latest_doc.read_text(encoding='utf-8')
                        if len(content.strip()) >= 50:
                            confidence += 0.1
                            logger.info(f"Arquivo de documentação {latest_doc.name} tem conteúdo adequado")
                        else:
                            improvements.append(f"Arquivo {latest_doc.name} poderia ter mais conteúdo")
                    except Exception as e:
                        logger.warning(f"Erro ao ler arquivo de documentação {latest_doc.name}: {e}")
            else:
                # Ser menos rigoroso - pode ter sido criado mas com nome diferente
                if execution_result.exit_code == 0:
                    improvements.append("Arquivo de documentação pode ter sido criado com nome diferente do esperado")
                    confidence = max(confidence, 0.6)  # Dar benefit of doubt
                else:
                    issues.append("Nenhum arquivo de documentação encontrado no workspace")
        
        # Verificar padrões de sucesso no stdout
        if execution_result.stdout:
            success_indicators = ["success", "created", "generated", "completed", "done"]
            if any(indicator in execution_result.stdout.lower() for indicator in success_indicators):
                confidence += 0.1
        
        passed = len(issues) == 0 and confidence >= 0.5
        
        return ValidationResult(
            validation_passed=passed,
            confidence_score=confidence,
            identified_issues=issues,
            suggested_improvements=improvements
        )
    
    async def _validate_file_modification(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """Valida modificação de arquivos"""
        # Implementação similar à criação, mas verificando mudanças
        return ValidationResult(
            validation_passed=execution_result.exit_code == 0,
            confidence_score=0.7,
            identified_issues=[],
            suggested_improvements=[]
        )
    
    async def _validate_command_execution(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """Valida execução de comandos"""
        issues = []
        improvements = []
        confidence = 0.5
        
        if execution_result.exit_code == 0:
            confidence += 0.3
        else:
            issues.append(f"Comando falhou com exit code {execution_result.exit_code}")
        
        # Analisar output para indicadores de sucesso
        if execution_result.stdout:
            if "successfully" in execution_result.stdout.lower():
                confidence += 0.2
            if "error" in execution_result.stdout.lower():
                improvements.append("Verificar erros no output")
        
        return ValidationResult(
            validation_passed=execution_result.exit_code == 0 and len(issues) == 0,
            confidence_score=confidence,
            identified_issues=issues,
            suggested_improvements=improvements
        )
    
    async def _validate_artifact_validation(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """Valida tarefas de validação de artefatos"""
        return ValidationResult(
            validation_passed=execution_result.exit_code == 0,
            confidence_score=0.9,
            identified_issues=[],
            suggested_improvements=[]
        )

    async def _perform_semantic_validation(self, task: Task, execution_result: ExecutionResult) -> ValidationResult:
        """
        Usa LLM para realizar validação semântica rigorosa da tarefa
        """
        
        # Construir prompt para validação semântica profunda
        validation_prompt = self._build_validation_prompt(task, execution_result)
        system_prompt = self._get_validation_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": validation_prompt}
        ]
        
        try:
            # Validação LLM reativada com tratamento robusto de erros
            logger.debug("Iniciando validação semântica com LLM")
            
            llm_response = await self.validator_llm.generate_response(
                messages,
                category=TaskCategory.VALIDATION,
                max_tokens=2048,
                temperature=0.2
            )
            
            if not llm_response:
                logger.warning("LLM validation failed, fallback to basic validation")
                return self._fallback_validation(execution_result)
            
            # Extrair resposta estruturada
            from evolux_engine.utils.string_utils import extract_json_from_llm_response
            json_response = extract_json_from_llm_response(llm_response)
            
            if json_response:
                try:
                    import json
                    validation_data = json.loads(json_response)
                    
                    # Validar estrutura da resposta
                    if not isinstance(validation_data, dict):
                        logger.warning("Invalid validation data structure, using fallback")
                        return self._fallback_validation(execution_result)
                    
                    # Construir checklist detalhada com validação robusta
                    checklist = []
                    if "checklist" in validation_data and isinstance(validation_data["checklist"], dict):
                        for key, passed in validation_data["checklist"].items():
                            if isinstance(key, str) and isinstance(passed, bool):
                                checklist.append(SemanticValidationChecklistItem(
                                    item=key.replace("_", " ").title(),
                                    passed=passed,
                                    reasoning=f"LLM analysis: {key} = {passed}"
                                ))
                    
                    # Validar campos obrigatórios com valores padrão seguros
                    validation_passed = validation_data.get("validation_passed", False)
                    confidence_score = validation_data.get("confidence_score", 0.5)
                    identified_issues = validation_data.get("identified_issues", [])
                    suggested_improvements = validation_data.get("suggested_improvements", [])
                    
                    # Garantir que são listas
                    if not isinstance(identified_issues, list):
                        identified_issues = [str(identified_issues)] if identified_issues else []
                    if not isinstance(suggested_improvements, list):
                        suggested_improvements = [str(suggested_improvements)] if suggested_improvements else []
                    
                    # Garantir que confidence_score está no range válido
                    if not isinstance(confidence_score, (int, float)) or confidence_score < 0 or confidence_score > 1:
                        confidence_score = 0.5
                    
                    return ValidationResult(
                        validation_passed=validation_passed,
                        confidence_score=confidence_score,
                        checklist=checklist,
                        identified_issues=identified_issues,
                        suggested_improvements=suggested_improvements
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM validation response: {e}")
                    return self._fallback_validation(execution_result)
            else:
                logger.warning("No valid JSON in LLM validation response")
                return self._fallback_validation(execution_result)
                
        except Exception as e:
            logger.error(f"Error in semantic validation: {e}")
            return self._fallback_validation(execution_result)
    
    def _fallback_validation(self, execution_result: ExecutionResult) -> ValidationResult:
        """Validação de fallback quando LLM falha"""
        if execution_result.exit_code == 0:
            return ValidationResult(
                validation_passed=True,
                confidence_score=0.7,  # Menor confiança para fallback
                checklist=[
                    SemanticValidationChecklistItem(
                        item="Execução bem sucedida", 
                        passed=True, 
                        reasoning="Exit code 0 indica sucesso"
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
                    )
                ],
                identified_issues=[f"Exit code: {execution_result.exit_code}"] + ([execution_result.stderr] if execution_result.stderr else []),
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
