"""
Sistema de Métricas de Qualidade para o Evolux Engine

Este módulo coleta, analisa e reporta métricas de qualidade do sistema,
incluindo:
- Qualidade de respostas LLM
- Taxa de sucesso de tarefas  
- Eficiência de iterações
- Padrões de melhoria
- Benchmarks de performance
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics

from loguru import logger
from evolux_engine.schemas.contracts import Task, ExecutionResult, ValidationResult
from evolux_engine.core.iterative_refiner import RefinementResult


class QualityMetricType(Enum):
    """Tipos de métricas de qualidade"""
    TASK_SUCCESS_RATE = "task_success_rate"
    AVERAGE_QUALITY_SCORE = "average_quality_score" 
    ITERATION_EFFICIENCY = "iteration_efficiency"
    IMPROVEMENT_RATE = "improvement_rate"
    CONVERGENCE_RATE = "convergence_rate"
    LLM_RESPONSE_QUALITY = "llm_response_quality"
    ERROR_RECOVERY_RATE = "error_recovery_rate"


@dataclass
class QualityMetric:
    """Representa uma métrica de qualidade"""
    metric_type: QualityMetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskQualityReport:
    """Relatório de qualidade para uma tarefa específica"""
    task_id: str
    task_type: str
    task_description: str
    quality_score: float
    success: bool
    iterations_used: int
    improvement_trajectory: List[float]
    issues_identified: List[str]
    time_to_completion: float
    llm_calls_count: int
    convergence_achieved: bool


@dataclass
class ProjectQualityReport:
    """Relatório de qualidade consolidado para um projeto"""
    project_id: str
    report_period: Tuple[datetime, datetime]
    total_tasks: int
    successful_tasks: int
    average_quality_score: float
    average_iterations_per_task: float
    convergence_rate: float
    most_common_issues: List[Tuple[str, int]]
    quality_trends: Dict[str, List[float]]
    recommendations: List[str]


class QualityMetricsCollector:
    """
    Coletor e analisador de métricas de qualidade do sistema.
    """
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.metrics: List[QualityMetric] = []
        self.task_reports: List[TaskQualityReport] = []
        self.quality_thresholds = {
            QualityMetricType.TASK_SUCCESS_RATE: 0.85,
            QualityMetricType.AVERAGE_QUALITY_SCORE: 8.0,
            QualityMetricType.CONVERGENCE_RATE: 0.75,
            QualityMetricType.IMPROVEMENT_RATE: 0.20
        }
        
        logger.info("QualityMetricsCollector initialized")
    
    def record_task_completion(
        self,
        task: Task,
        execution_result: ExecutionResult,
        validation_result: ValidationResult,
        refinement_result: Optional[RefinementResult] = None,
        completion_time: float = 0.0,
        llm_calls: int = 1
    ):
        """Registra a conclusão de uma tarefa e suas métricas"""
        
        # Calcular pontuação de qualidade
        quality_score = self._calculate_task_quality_score(
            execution_result, validation_result, refinement_result
        )
        
        # Criar relatório da tarefa
        task_report = TaskQualityReport(
            task_id=task.task_id,
            task_type=task.type.value,
            task_description=task.description,
            quality_score=quality_score,
            success=execution_result.exit_code == 0,
            iterations_used=refinement_result.total_iterations if refinement_result else 1,
            improvement_trajectory=refinement_result.improvement_trajectory if refinement_result else [quality_score],
            issues_identified=validation_result.identified_issues,
            time_to_completion=completion_time,
            llm_calls_count=llm_calls,
            convergence_achieved=refinement_result.convergence_achieved if refinement_result else True
        )
        
        self.task_reports.append(task_report)
        
        # Registrar métricas individuais
        self._record_metric(QualityMetricType.AVERAGE_QUALITY_SCORE, quality_score)
        self._record_metric(QualityMetricType.TASK_SUCCESS_RATE, 1.0 if task_report.success else 0.0)
        
        if refinement_result:
            self._record_metric(QualityMetricType.ITERATION_EFFICIENCY, 
                              quality_score / max(refinement_result.total_iterations, 1))
            self._record_metric(QualityMetricType.CONVERGENCE_RATE, 
                              1.0 if refinement_result.convergence_achieved else 0.0)
            
            # Calcular taxa de melhoria
            if len(refinement_result.improvement_trajectory) > 1:
                initial_score = refinement_result.improvement_trajectory[0]
                final_score = refinement_result.improvement_trajectory[-1]
                improvement_rate = (final_score - initial_score) / max(initial_score, 1.0)
                self._record_metric(QualityMetricType.IMPROVEMENT_RATE, improvement_rate)
        
        logger.info(f"Task quality recorded: {task.task_id} - Score: {quality_score:.2f}")
    
    def _calculate_task_quality_score(
        self,
        execution_result: ExecutionResult,
        validation_result: ValidationResult,
        refinement_result: Optional[RefinementResult]
    ) -> float:
        """Calcula pontuação de qualidade para uma tarefa"""
        
        score = 0.0
        
        # Base score from execution
        if execution_result.exit_code == 0:
            score += 4.0
        
        # Validation confidence
        score += validation_result.confidence_score * 3.0
        
        # Penalty for issues
        issues_penalty = min(len(validation_result.identified_issues) * 0.5, 2.0)
        score -= issues_penalty
        
        # Bonus for convergence in refinement
        if refinement_result and refinement_result.convergence_achieved:
            score += 1.0
        
        # Bonus for improvement trajectory
        if refinement_result and len(refinement_result.improvement_trajectory) > 1:
            improvement = (refinement_result.improvement_trajectory[-1] - 
                          refinement_result.improvement_trajectory[0])
            score += min(improvement * 0.5, 2.0)
        
        return max(0.0, min(10.0, score))
    
    def _record_metric(self, metric_type: QualityMetricType, value: float, context: Dict[str, Any] = None):
        """Registra uma métrica individual"""
        metric = QualityMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )
        self.metrics.append(metric)
    
    def get_current_quality_metrics(self) -> Dict[str, float]:
        """Retorna métricas de qualidade atuais"""
        
        # Limpar métricas antigas
        self._cleanup_old_metrics()
        
        if not self.metrics:
            return {}
        
        # Calcular métricas agregadas para os últimos 7 dias
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_date]
        
        if not recent_metrics:
            return {}
        
        # Agrupar por tipo de métrica
        metrics_by_type = {}
        for metric in recent_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric.value)
        
        # Calcular estatísticas
        result = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                result[metric_type.value] = {
                    'current': statistics.mean(values),
                    'trend': self._calculate_trend(values),
                    'count': len(values)
                }
        
        return result
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendência dos valores"""
        if len(values) < 3:
            return "stable"
        
        # Comparar primeira e segunda metade
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])
        
        change = (second_half_avg - first_half_avg) / max(first_half_avg, 0.1)
        
        if change > 0.1:
            return "improving"
        elif change < -0.1:
            return "declining"
        else:
            return "stable"
    
    def generate_project_quality_report(self, project_id: str, days: int = 7) -> ProjectQualityReport:
        """Gera relatório de qualidade consolidado para um projeto"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_tasks = [t for t in self.task_reports if t.task_id.startswith(project_id)]
        
        if not recent_tasks:
            return ProjectQualityReport(
                project_id=project_id,
                report_period=(cutoff_date, datetime.now()),
                total_tasks=0,
                successful_tasks=0,
                average_quality_score=0.0,
                average_iterations_per_task=0.0,
                convergence_rate=0.0,
                most_common_issues=[],
                quality_trends={},
                recommendations=[]
            )
        
        # Calcular estatísticas
        total_tasks = len(recent_tasks)
        successful_tasks = sum(1 for t in recent_tasks if t.success)
        avg_quality = statistics.mean([t.quality_score for t in recent_tasks])
        avg_iterations = statistics.mean([t.iterations_used for t in recent_tasks])
        convergence_rate = sum(1 for t in recent_tasks if t.convergence_achieved) / total_tasks
        
        # Análise de issues
        all_issues = []
        for task in recent_tasks:
            all_issues.extend(task.issues_identified)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        most_common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Tendências de qualidade
        quality_trends = {
            'quality_scores': [t.quality_score for t in recent_tasks],
            'iteration_counts': [t.iterations_used for t in recent_tasks],
            'completion_times': [t.time_to_completion for t in recent_tasks]
        }
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(recent_tasks, avg_quality, convergence_rate)
        
        return ProjectQualityReport(
            project_id=project_id,
            report_period=(cutoff_date, datetime.now()),
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            average_quality_score=avg_quality,
            average_iterations_per_task=avg_iterations,
            convergence_rate=convergence_rate,
            most_common_issues=most_common_issues,
            quality_trends=quality_trends,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self, 
        tasks: List[TaskQualityReport], 
        avg_quality: float, 
        convergence_rate: float
    ) -> List[str]:
        """Gera recomendações baseadas nas métricas"""
        
        recommendations = []
        
        # Recomendações baseadas na qualidade média
        if avg_quality < self.quality_thresholds[QualityMetricType.AVERAGE_QUALITY_SCORE]:
            recommendations.append(
                f"Qualidade média ({avg_quality:.2f}) está abaixo do threshold "
                f"({self.quality_thresholds[QualityMetricType.AVERAGE_QUALITY_SCORE]}). "
                "Considere aumentar o número de iterações ou melhorar os prompts."
            )
        
        # Recomendações baseadas na taxa de convergência
        if convergence_rate < self.quality_thresholds[QualityMetricType.CONVERGENCE_RATE]:
            recommendations.append(
                f"Taxa de convergência ({convergence_rate:.2f}) está baixa. "
                "Considere ajustar critérios de parada ou melhorar estratégias de refinamento."
            )
        
        # Análise de padrões de falha
        failed_tasks = [t for t in tasks if not t.success]
        if len(failed_tasks) > len(tasks) * 0.2:  # Mais de 20% de falhas
            recommendations.append(
                "Alta taxa de falhas detectada. Revise validação de entrada e "
                "tratamento de erros nos prompts."
            )
        
        # Recomendações baseadas em iterações
        high_iteration_tasks = [t for t in tasks if t.iterations_used > 4]
        if len(high_iteration_tasks) > len(tasks) * 0.3:  # Mais de 30% precisam de muitas iterações
            recommendations.append(
                "Muitas tarefas precisam de múltiplas iterações. "
                "Considere melhorar a qualidade dos prompts iniciais."
            )
        
        # Análise de issues comuns
        all_issues = []
        for task in tasks:
            all_issues.extend(task.issues_identified)
        
        if len(all_issues) > len(tasks):  # Média de mais de 1 issue por tarefa
            recommendations.append(
                "Número elevado de issues identificadas. "
                "Foque em melhorar a validação preventiva e quality gates."
            )
        
        return recommendations
    
    def _cleanup_old_metrics(self):
        """Remove métricas antigas baseadas na política de retenção"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff_date]
        self.task_reports = [t for t in self.task_reports 
                           if datetime.now() - timedelta(seconds=t.time_to_completion) > cutoff_date]
    
    def export_metrics_to_json(self, filepath: str):
        """Exporta métricas para arquivo JSON"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics_summary': self.get_current_quality_metrics(),
                'recent_tasks': [
                    {
                        'task_id': t.task_id,
                        'task_type': t.task_type,
                        'quality_score': t.quality_score,
                        'success': t.success,
                        'iterations_used': t.iterations_used,
                        'convergence_achieved': t.convergence_achieved
                    }
                    for t in self.task_reports[-50:]  # Últimas 50 tarefas
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados formatados para dashboard de qualidade"""
        
        current_metrics = self.get_current_quality_metrics()
        recent_tasks = self.task_reports[-20:] if self.task_reports else []
        
        return {
            'current_metrics': current_metrics,
            'recent_task_quality': [
                {
                    'task_id': t.task_id[:8],  # Primeiros 8 chars
                    'type': t.task_type,
                    'score': round(t.quality_score, 2),
                    'iterations': t.iterations_used,
                    'success': t.success
                }
                for t in recent_tasks
            ],
            'quality_distribution': self._get_quality_distribution(),
            'improvement_patterns': self._analyze_improvement_patterns()
        }
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """Analisa distribuição de pontuações de qualidade"""
        if not self.task_reports:
            return {}
        
        scores = [t.quality_score for t in self.task_reports]
        
        return {
            'excellent': sum(1 for s in scores if s >= 9.0),
            'good': sum(1 for s in scores if 7.0 <= s < 9.0),
            'fair': sum(1 for s in scores if 5.0 <= s < 7.0),
            'poor': sum(1 for s in scores if s < 5.0)
        }
    
    def _analyze_improvement_patterns(self) -> Dict[str, Any]:
        """Analisa padrões de melhoria nas tarefas"""
        
        tasks_with_refinement = [t for t in self.task_reports if t.iterations_used > 1]
        
        if not tasks_with_refinement:
            return {'average_improvement': 0.0, 'improvement_rate': 0.0}
        
        improvements = []
        for task in tasks_with_refinement:
            if len(task.improvement_trajectory) > 1:
                initial = task.improvement_trajectory[0]
                final = task.improvement_trajectory[-1]
                improvement = final - initial
                improvements.append(improvement)
        
        if not improvements:
            return {'average_improvement': 0.0, 'improvement_rate': 0.0}
        
        return {
            'average_improvement': statistics.mean(improvements),
            'improvement_rate': sum(1 for i in improvements if i > 0) / len(improvements),
            'max_improvement': max(improvements),
            'consistent_improvers': sum(1 for i in improvements if i > 1.0)
        }