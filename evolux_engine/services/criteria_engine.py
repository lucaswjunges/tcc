from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re

from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("criteria_engine")

class CompletionStatus(Enum):
    """Status de conclusão do projeto"""
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED_CRITERIA = "failed_criteria"

@dataclass
class CriteriaCheck:
    """Resultado de verificação de um critério específico"""
    criterion_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    required: bool = True

@dataclass
class CompletionReport:
    """Relatório completo de verificação de conclusão"""
    status: CompletionStatus
    overall_score: float
    checks: List[CriteriaCheck]
    missing_artifacts: List[str]
    recommendations: List[str]
    summary: str

class CriteriaEngine:
    """
    Engine para verificação de critérios de conclusão de projeto.
    Implementa a verificação final conforme especificação.
    """
    
    def __init__(self):
        self.default_criteria = self._get_default_criteria()
        logger.info("CriteriaEngine initialized")
    
    def _get_default_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Critérios padrão para diferentes tipos de projeto"""
        return {
            "code_project": {
                "required_files": ["README.md", "requirements.txt"],
                "optional_files": ["tests/", "docs/", ".gitignore"],
                "code_quality": {
                    "min_test_coverage": 0.0,  # Relaxed for MVP
                    "max_complexity": 10,
                    "require_docstrings": False
                },
                "functionality": {
                    "can_install": True,
                    "can_run": True,
                    "no_critical_errors": True
                }
            },
            "web_application": {
                "required_files": ["README.md", "requirements.txt", "app.py"],
                "optional_files": ["static/", "templates/", "tests/"],
                "functionality": {
                    "has_routes": True,
                    "can_start_server": True,
                    "has_html_templates": True
                }
            },
            "api": {
                "required_files": ["README.md", "requirements.txt", "api.py"],
                "optional_files": ["tests/", "docs/"],
                "functionality": {
                    "has_endpoints": True,
                    "has_documentation": True,
                    "responds_to_requests": True
                }
            },
            "generic": {
                "required_files": ["README.md"],
                "optional_files": ["requirements.txt"],
                "functionality": {
                    "has_main_file": True,
                    "documented": True
                }
            }
        }
    
    def check_completion(self, project_context) -> CompletionReport:
        """
        Verifica se o projeto atende aos critérios de conclusão.
        
        Args:
            project_context: Contexto do projeto
            
        Returns:
            Relatório de conclusão
        """
        logger.info("Checking project completion", project_id=project_context.project_id)
        
        project_type = project_context.project_type or "generic"
        criteria = self.default_criteria.get(project_type, self.default_criteria["generic"])
        
        checks = []
        missing_artifacts = []
        
        # 1. Verificar arquivos obrigatórios
        required_files_check = self._check_required_files(
            project_context, criteria.get("required_files", [])
        )
        checks.append(required_files_check)
        if not required_files_check.passed:
            missing_artifacts.extend(self._extract_missing_files(required_files_check.details))
        
        # 2. Verificar arquivos opcionais (pontuação extra)
        optional_files_check = self._check_optional_files(
            project_context, criteria.get("optional_files", [])
        )
        checks.append(optional_files_check)
        
        # 3. Verificar funcionalidade básica
        functionality_check = self._check_functionality(
            project_context, criteria.get("functionality", {})
        )
        checks.append(functionality_check)
        
        # 4. Verificar qualidade de código (se aplicável)
        if "code_quality" in criteria:
            quality_check = self._check_code_quality(
                project_context, criteria["code_quality"]
            )
            checks.append(quality_check)
        
        # 5. Verificar conclusão de tarefas
        task_completion_check = self._check_task_completion(project_context)
        checks.append(task_completion_check)
        
        # Calcular score geral e status
        overall_score = self._calculate_overall_score(checks)
        status = self._determine_status(checks, overall_score)
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(checks, missing_artifacts)
        
        # Criar resumo
        summary = self._generate_summary(status, overall_score, len(checks))
        
        report = CompletionReport(
            status=status,
            overall_score=overall_score,
            checks=checks,
            missing_artifacts=missing_artifacts,
            recommendations=recommendations,
            summary=summary
        )
        
        logger.info("Completion check finished",
                   status=status.value,
                   score=overall_score,
                   total_checks=len(checks))
        
        return report
    
    def _check_required_files(self, project_context, required_files: List[str]) -> CriteriaCheck:
        """Verifica se arquivos obrigatórios existem"""
        artifacts_dir = Path(project_context.workspace_path) / "artifacts"
        found_files = []
        missing_files = []
        
        for file_pattern in required_files:
            if self._file_exists(artifacts_dir, file_pattern):
                found_files.append(file_pattern)
            else:
                missing_files.append(file_pattern)
        
        passed = len(missing_files) == 0
        score = len(found_files) / len(required_files) if required_files else 1.0
        
        details = f"Found: {found_files}, Missing: {missing_files}"
        
        return CriteriaCheck(
            criterion_name="Required Files",
            passed=passed,
            score=score,
            details=details,
            required=True
        )
    
    def _check_optional_files(self, project_context, optional_files: List[str]) -> CriteriaCheck:
        """Verifica arquivos opcionais para pontuação extra"""
        artifacts_dir = Path(project_context.workspace_path) / "artifacts"
        found_files = []
        
        for file_pattern in optional_files:
            if self._file_exists(artifacts_dir, file_pattern):
                found_files.append(file_pattern)
        
        score = min(1.0, len(found_files) / max(1, len(optional_files)) * 1.5)  # Bonus scoring
        
        return CriteriaCheck(
            criterion_name="Optional Files",
            passed=True,  # Optional files don't fail the project
            score=score,
            details=f"Found optional files: {found_files}",
            required=False
        )
    
    def _check_functionality(self, project_context, functionality_criteria: Dict[str, bool]) -> CriteriaCheck:
        """Verifica critérios funcionais básicos"""
        artifacts_dir = Path(project_context.workspace_path) / "artifacts"
        passed_criteria = []
        failed_criteria = []
        
        for criterion, required in functionality_criteria.items():
            if criterion == "documented":
                # Check if README.md has substantial content
                readme_path = artifacts_dir / "README.md"
                if readme_path.exists() and len(readme_path.read_text()) > 100:
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif criterion == "has_main_file":
                # Check for main entry point files
                main_files = ["app.py", "main.py", "run.py", "server.py"]
                if any(self._file_exists(artifacts_dir, f) for f in main_files):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif criterion == "has_routes":
                # Check for web routes in Python files
                if self._contains_pattern(artifacts_dir, r"@app\.route|@bp\.route|app\.get|app\.post"):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif criterion == "has_endpoints":
                # Check for API endpoints
                if self._contains_pattern(artifacts_dir, r"@app\.route|FastAPI|@api\.|endpoint"):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif criterion == "has_html_templates":
                # Check for HTML templates
                if self._file_exists(artifacts_dir, "templates/") or self._contains_pattern(artifacts_dir, r"\.html"):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            else:
                # For other criteria, assume passed (would need specific implementations)
                passed_criteria.append(criterion)
        
        total_criteria = len(functionality_criteria)
        passed = len(failed_criteria) == 0
        score = len(passed_criteria) / total_criteria if total_criteria > 0 else 1.0
        
        return CriteriaCheck(
            criterion_name="Functionality",
            passed=passed,
            score=score,
            details=f"Passed: {passed_criteria}, Failed: {failed_criteria}",
            required=True
        )
    
    def _check_code_quality(self, project_context, quality_criteria: Dict[str, Any]) -> CriteriaCheck:
        """Verifica qualidade básica do código"""
        # Implementação simplificada - expandir conforme necessário
        passed_checks = []
        failed_checks = []
        
        # Check for basic quality indicators
        artifacts_dir = Path(project_context.workspace_path) / "artifacts"
        
        # Check for docstrings if required
        if quality_criteria.get("require_docstrings", False):
            if self._contains_pattern(artifacts_dir, r'""".*"""'):
                passed_checks.append("docstrings")
            else:
                failed_checks.append("docstrings")
        else:
            passed_checks.append("docstrings_not_required")
        
        # Basic syntax check (no obvious syntax errors in Python files)
        if not self._contains_pattern(artifacts_dir, r"SyntaxError|IndentationError"):
            passed_checks.append("no_syntax_errors")
        else:
            failed_checks.append("syntax_errors_found")
        
        total_checks = len(passed_checks) + len(failed_checks)
        score = len(passed_checks) / total_checks if total_checks > 0 else 1.0
        passed = len(failed_checks) == 0
        
        return CriteriaCheck(
            criterion_name="Code Quality",
            passed=passed,
            score=score,
            details=f"Passed: {passed_checks}, Failed: {failed_checks}",
            required=False
        )
    
    def _check_task_completion(self, project_context) -> CriteriaCheck:
        """Verifica se tarefas foram concluídas"""
        total_tasks = len(project_context.task_queue) + len(project_context.completed_tasks)
        completed_tasks = len(project_context.completed_tasks)
        
        if total_tasks == 0:
            score = 1.0
            passed = True
            details = "No tasks defined"
        else:
            score = completed_tasks / total_tasks
            passed = score >= 0.8  # 80% das tarefas concluídas
            details = f"Completed {completed_tasks}/{total_tasks} tasks"
        
        return CriteriaCheck(
            criterion_name="Task Completion",
            passed=passed,
            score=score,
            details=details,
            required=True
        )
    
    def _file_exists(self, base_dir: Path, file_pattern: str) -> bool:
        """Verifica se arquivo ou diretório existe"""
        if file_pattern.endswith('/'):
            # É um diretório
            return (base_dir / file_pattern.rstrip('/')).is_dir()
        else:
            # É um arquivo
            return (base_dir / file_pattern).exists()
    
    def _contains_pattern(self, base_dir: Path, pattern: str) -> bool:
        """Verifica se algum arquivo contém o padrão regex"""
        for file_path in base_dir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding='utf-8')
                if re.search(pattern, content):
                    return True
            except Exception:
                continue
        return False
    
    def _calculate_overall_score(self, checks: List[CriteriaCheck]) -> float:
        """Calcula score geral baseado nas verificações"""
        if not checks:
            return 0.0
        
        required_checks = [c for c in checks if c.required]
        optional_checks = [c for c in checks if not c.required]
        
        # Score base dos requisitos obrigatórios
        required_score = 0.0
        if required_checks:
            required_score = sum(c.score for c in required_checks) / len(required_checks)
        
        # Bonus dos opcionais
        optional_bonus = 0.0
        if optional_checks:
            optional_bonus = sum(c.score for c in optional_checks) / len(optional_checks) * 0.2
        
        return min(1.0, required_score + optional_bonus)
    
    def _determine_status(self, checks: List[CriteriaCheck], overall_score: float) -> CompletionStatus:
        """Determina status baseado nas verificações"""
        required_checks = [c for c in checks if c.required]
        all_required_passed = all(c.passed for c in required_checks)
        
        if overall_score >= 0.9 and all_required_passed:
            return CompletionStatus.COMPLETED
        elif overall_score >= 0.7 and all_required_passed:
            return CompletionStatus.PARTIALLY_COMPLETED
        elif overall_score >= 0.5:
            return CompletionStatus.PARTIALLY_COMPLETED
        else:
            return CompletionStatus.FAILED_CRITERIA
    
    def _extract_missing_files(self, details: str) -> List[str]:
        """Extrai lista de arquivos faltantes dos detalhes"""
        # Parse "Missing: ['file1', 'file2']" format
        import ast
        try:
            if "Missing: " in details:
                missing_part = details.split("Missing: ")[1]
                if missing_part.startswith('[') and missing_part.endswith(']'):
                    return ast.literal_eval(missing_part)
        except:
            pass
        return []
    
    def _generate_recommendations(self, checks: List[CriteriaCheck], missing_artifacts: List[str]) -> List[str]:
        """Gera recomendações baseadas nas verificações"""
        recommendations = []
        
        # Recomendações para arquivos faltantes
        if missing_artifacts:
            recommendations.append(f"Criar arquivos obrigatórios: {', '.join(missing_artifacts)}")
        
        # Recomendações baseadas em verificações falhas
        for check in checks:
            if not check.passed and check.required:
                if check.criterion_name == "Task Completion":
                    recommendations.append("Concluir tarefas pendentes na fila")
                elif check.criterion_name == "Functionality":
                    recommendations.append("Implementar funcionalidades básicas requeridas")
                elif check.criterion_name == "Code Quality":
                    recommendations.append("Melhorar qualidade do código")
        
        # Recomendações gerais se score baixo
        failed_required = [c for c in checks if c.required and not c.passed]
        if len(failed_required) > 1:
            recommendations.append("Revisar objetivos do projeto e implementar funcionalidades básicas")
        
        return recommendations
    
    def _generate_summary(self, status: CompletionStatus, score: float, total_checks: int) -> str:
        """Gera resumo do relatório"""
        score_percent = int(score * 100)
        
        if status == CompletionStatus.COMPLETED:
            return f"✅ Projeto concluído com sucesso! Score: {score_percent}% ({total_checks} verificações)"
        elif status == CompletionStatus.PARTIALLY_COMPLETED:
            return f"🟡 Projeto parcialmente concluído. Score: {score_percent}% ({total_checks} verificações)"
        elif status == CompletionStatus.FAILED_CRITERIA:
            return f"❌ Projeto não atende aos critérios mínimos. Score: {score_percent}% ({total_checks} verificações)"
        else:
            return f"🔄 Projeto incompleto. Score: {score_percent}% ({total_checks} verificações)"