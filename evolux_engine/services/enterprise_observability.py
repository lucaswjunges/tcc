import asyncio
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import psutil
import threading
from collections import defaultdict, deque
import functools

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.config.advanced_config import AdvancedSystemConfig

logger = get_structured_logger("enterprise_observability")

class MetricType(Enum):
    """Tipos de métricas suportadas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Níveis de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricValue:
    """Valor de uma métrica com timestamp"""
    value: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class PerformanceMetrics:
    """Métricas de performance do sistema"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    disk_usage_percent: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration_ms: float = 0.0
    llm_request_count: int = 0
    llm_success_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class HealthStatus:
    """Status de saúde de um componente"""
    component: str
    is_healthy: bool
    last_check: datetime
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class TraceSpan:
    """Span para distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "started"  # started, completed, error

@dataclass
class AlertRule:
    """Regra de alerta"""
    name: str
    metric_name: str
    condition: str  # >, <, ==, !=, >=, <=
    threshold: float
    level: AlertLevel
    cooldown_minutes: int = 5
    message_template: str = "Alert: {metric_name} {condition} {threshold}"

class EnterpriseObservabilityService:
    """
    Serviço de observabilidade enterprise-grade com:
    - Coleta de métricas customizadas
    - Monitoramento de performance e saúde
    - Distributed tracing
    - Sistema de alertas
    - Dashboards e relatórios
    - Integração com sistemas externos
    """
    
    def __init__(self, config: AdvancedSystemConfig):
        self.config = config
        self.is_running = False
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._traces: Dict[str, TraceSpan] = {}
        self._health_checks: Dict[str, HealthStatus] = {}
        self._alert_rules: List[AlertRule] = []
        self._alert_history: deque = deque(maxlen=100)
        self._last_alerts: Dict[str, datetime] = {}
        
        # Performance tracking
        self._task_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'task_durations': deque(maxlen=100),
            'llm_requests': 0,
            'llm_successes': 0
        }
        
        # Threading
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Configurar alertas padrão
        self._setup_default_alerts()
        
        logger.info("EnterpriseObservabilityService initialized",
                   metrics_enabled=config.enable_metrics_collection,
                   structured_logging=config.enable_structured_logging)
    
    def _setup_default_alerts(self):
        """Configura alertas padrão do sistema"""
        default_alerts = [
            AlertRule(
                name="high_cpu_usage",
                metric_name="system.cpu_percent",
                condition=">",
                threshold=80.0,
                level=AlertLevel.WARNING,
                message_template="High CPU usage: {value}%"
            ),
            AlertRule(
                name="high_memory_usage", 
                metric_name="system.memory_percent",
                condition=">",
                threshold=85.0,
                level=AlertLevel.WARNING,
                message_template="High memory usage: {value}%"
            ),
            AlertRule(
                name="low_llm_success_rate",
                metric_name="llm.success_rate",
                condition="<",
                threshold=0.8,
                level=AlertLevel.ERROR,
                message_template="Low LLM success rate: {value}%"
            ),
            AlertRule(
                name="high_task_failure_rate",
                metric_name="tasks.failure_rate",
                condition=">",
                threshold=0.3,
                level=AlertLevel.ERROR,
                message_template="High task failure rate: {value}%"
            )
        ]
        
        self._alert_rules.extend(default_alerts)
    
    def start_monitoring(self):
        """Inicia monitoramento em background"""
        if self.is_running:
            logger.warning("Monitoring already running")
            return
            
        self.is_running = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Background monitoring started")
    
    def stop_monitoring(self):
        """Para monitoramento em background"""
        self.is_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        logger.info("Background monitoring stopped")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.is_running:
            try:
                # Coletar métricas de sistema
                self._collect_system_metrics()
                
                # Verificar saúde dos componentes
                asyncio.run(self._check_health_status())
                
                # Verificar alertas
                self._check_alerts()
                
                # Limpeza de dados antigos
                self._cleanup_old_data()
                
                time.sleep(30)  # Coletar métricas a cada 30 segundos
                
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system.cpu_percent", cpu_percent, MetricType.GAUGE)
            
            # Memory
            memory = psutil.virtual_memory()
            self.record_metric("system.memory_percent", memory.percent, MetricType.GAUGE) 
            self.record_metric("system.memory_used_mb", memory.used / 1024 / 1024, MetricType.GAUGE)
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric("system.disk_usage_percent", disk_percent, MetricType.GAUGE)
            
            # Process info
            process = psutil.Process()
            self.record_metric("process.cpu_percent", process.cpu_percent(), MetricType.GAUGE)
            self.record_metric("process.memory_mb", process.memory_info().rss / 1024 / 1024, MetricType.GAUGE)
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
    
    async def _check_health_status(self):
        """Verifica status de saúde dos componentes"""
        # Health check para diretórios críticos
        await self._check_directories()
        
        # Health check para configuração
        await self._check_configuration()
        
        # Health check para LLM providers
        await self._check_llm_providers()
    
    async def _check_directories(self):
        """Verifica diretórios críticos"""
        critical_dirs = [
            self.config.project_base_directory,
            self.config.log_dir
        ]
        
        for dir_path in critical_dirs:
            try:
                path = Path(dir_path)
                is_healthy = path.exists() and path.is_dir() and os.access(path, os.W_OK)
                
                self._health_checks[f"directory.{path.name}"] = HealthStatus(
                    component=f"directory.{path.name}",
                    is_healthy=is_healthy,
                    last_check=datetime.now(),
                    error_message=None if is_healthy else f"Directory not accessible: {dir_path}"
                )
            except Exception as e:
                self._health_checks[f"directory.{Path(dir_path).name}"] = HealthStatus(
                    component=f"directory.{Path(dir_path).name}",
                    is_healthy=False,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
    
    async def _check_configuration(self):
        """Verifica configuração do sistema"""
        try:
            # Verificar se pelo menos uma API key está configurada
            api_keys_configured = any([
                self.config.get_api_key('openrouter'),
                self.config.get_api_key('openai'),
                self.config.get_api_key('google')
            ])
            
            self._health_checks["configuration.api_keys"] = HealthStatus(
                component="configuration.api_keys",
                is_healthy=api_keys_configured,
                last_check=datetime.now(),
                error_message=None if api_keys_configured else "No API keys configured"
            )
            
            # Verificar configurações críticas
            critical_config_ok = (
                self.config.max_concurrent_tasks > 0 and
                self.config.request_timeout > 0
            )
            
            self._health_checks["configuration.critical"] = HealthStatus(
                component="configuration.critical",
                is_healthy=critical_config_ok,
                last_check=datetime.now(),
                error_message=None if critical_config_ok else "Critical configuration values invalid"
            )
            
        except Exception as e:
            self._health_checks["configuration"] = HealthStatus(
                component="configuration",
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_llm_providers(self):
        """Verifica status dos provedores LLM"""
        providers = ['openrouter', 'openai', 'google']
        
        for provider in providers:
            try:
                api_key = self.config.get_api_key(provider)
                is_healthy = api_key is not None and len(api_key) > 8
                
                self._health_checks[f"llm.{provider}"] = HealthStatus(
                    component=f"llm.{provider}",
                    is_healthy=is_healthy,
                    last_check=datetime.now(),
                    error_message=None if is_healthy else f"No API key for {provider}"
                )
            except Exception as e:
                self._health_checks[f"llm.{provider}"] = HealthStatus(
                    component=f"llm.{provider}",
                    is_healthy=False,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
    
    def _check_alerts(self):
        """Verifica condições de alerta"""
        current_time = datetime.now()
        
        for rule in self._alert_rules:
            try:
                # Obter valor mais recente da métrica
                metric_values = self._metrics.get(rule.metric_name)
                if not metric_values:
                    continue
                
                current_value = metric_values[-1].value
                
                # Verificar condição
                if self._evaluate_alert_condition(current_value, rule.condition, rule.threshold):
                    # Verificar cooldown
                    last_alert_time = self._last_alerts.get(rule.name)
                    if last_alert_time:
                        time_since_alert = current_time - last_alert_time
                        if time_since_alert < timedelta(minutes=rule.cooldown_minutes):
                            continue
                    
                    # Disparar alerta
                    self._trigger_alert(rule, current_value)
                    self._last_alerts[rule.name] = current_time
                    
            except Exception as e:
                logger.error("Error checking alert rule", rule=rule.name, error=str(e))
    
    def _evaluate_alert_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Avalia condição de alerta"""
        conditions = {
            '>': value > threshold,
            '<': value < threshold,
            '>=': value >= threshold,
            '<=': value <= threshold,
            '==': abs(value - threshold) < 0.001,
            '!=': abs(value - threshold) >= 0.001
        }
        return conditions.get(condition, False)
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """Dispara um alerta"""
        message = rule.message_template.format(
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            value=value
        )
        
        alert_data = {
            'rule_name': rule.name,
            'metric_name': rule.metric_name,
            'level': rule.level.value,
            'message': message,
            'value': value,
            'threshold': rule.threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        self._alert_history.append(alert_data)
        
        # Log based on severity
        if rule.level == AlertLevel.CRITICAL:
            logger.critical("ALERT TRIGGERED", **alert_data)
        elif rule.level == AlertLevel.ERROR:
            logger.error("ALERT TRIGGERED", **alert_data)
        elif rule.level == AlertLevel.WARNING:
            logger.warning("ALERT TRIGGERED", **alert_data)
        else:
            logger.info("ALERT TRIGGERED", **alert_data)
    
    def _cleanup_old_data(self):
        """Limpa dados antigos"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Limpar traces antigos
        old_traces = [
            trace_id for trace_id, trace in self._traces.items()
            if trace.start_time < cutoff_time
        ]
        
        for trace_id in old_traces:
            del self._traces[trace_id]
    
    def record_metric(self, name: str, value: Union[int, float], 
                     metric_type: MetricType, tags: Optional[Dict[str, str]] = None):
        """Registra uma métrica"""
        with self._lock:
            metric_value = MetricValue(
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            
            self._metrics[name].append(metric_value)
            
            # Log para métricas importantes
            if metric_type in [MetricType.COUNTER, MetricType.TIMER]:
                logger.debug("Metric recorded", 
                           name=name, value=value, type=metric_type.value)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Incrementa um contador"""
        current_values = self._metrics.get(name)
        current_value = current_values[-1].value if current_values else 0
        self.record_metric(name, current_value + value, MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """Define valor de um gauge"""
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    @contextmanager
    def time_operation(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager para medir tempo de operação"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_metric(f"operation.{operation_name}.duration_ms", 
                             duration_ms, MetricType.TIMER, tags)
    
    def start_trace(self, operation_name: str, parent_span_id: Optional[str] = None) -> str:
        """Inicia um trace span"""
        import uuid
        
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now()
        )
        
        self._traces[span_id] = span
        
        logger.debug("Trace started", 
                    trace_id=trace_id, 
                    span_id=span_id,
                    operation=operation_name)
        
        return span_id
    
    def finish_trace(self, span_id: str, status: str = "completed", 
                    tags: Optional[Dict[str, Any]] = None):
        """Finaliza um trace span"""
        if span_id not in self._traces:
            logger.warning("Trace span not found", span_id=span_id)
            return
        
        span = self._traces[span_id]
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        
        if tags:
            span.tags.update(tags)
        
        logger.debug("Trace finished",
                    trace_id=span.trace_id,
                    span_id=span_id,
                    duration_ms=span.duration_ms,
                    status=status)
    
    def add_trace_log(self, span_id: str, message: str, level: str = "info", 
                     fields: Optional[Dict[str, Any]] = None):
        """Adiciona log a um trace span"""
        if span_id not in self._traces:
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'fields': fields or {}
        }
        
        self._traces[span_id].logs.append(log_entry)
    
    @asynccontextmanager
    async def async_trace(self, operation_name: str, parent_span_id: Optional[str] = None):
        """Async context manager para tracing"""
        span_id = self.start_trace(operation_name, parent_span_id)
        try:
            yield span_id
            self.finish_trace(span_id, "completed")
        except Exception as e:
            self.finish_trace(span_id, "error", {"error": str(e)})
            raise
    
    def record_task_completion(self, success: bool, duration_ms: float):
        """Registra conclusão de uma tarefa"""
        with self._lock:
            self._task_metrics['total_tasks'] += 1
            
            if success:
                self._task_metrics['completed_tasks'] += 1
            else:
                self._task_metrics['failed_tasks'] += 1
            
            self._task_metrics['task_durations'].append(duration_ms)
            
            # Atualizar métricas derivadas
            total = self._task_metrics['total_tasks']
            completed = self._task_metrics['completed_tasks']
            failed = self._task_metrics['failed_tasks']
            
            self.set_gauge("tasks.total", total)
            self.set_gauge("tasks.completed", completed)
            self.set_gauge("tasks.failed", failed)
            self.set_gauge("tasks.success_rate", completed / total if total > 0 else 0.0)
            self.set_gauge("tasks.failure_rate", failed / total if total > 0 else 0.0)
            
            # Média de duração
            if self._task_metrics['task_durations']:
                avg_duration = sum(self._task_metrics['task_durations']) / len(self._task_metrics['task_durations'])
                self.set_gauge("tasks.avg_duration_ms", avg_duration)
    
    def record_llm_request(self, success: bool, provider: str, model: str, duration_ms: float):
        """Registra requisição LLM"""
        with self._lock:
            self._task_metrics['llm_requests'] += 1
            
            if success:
                self._task_metrics['llm_successes'] += 1
            
            # Métricas por provider e modelo
            tags = {"provider": provider, "model": model}
            self.increment_counter("llm.requests", 1, tags)
            
            if success:
                self.increment_counter("llm.successes", 1, tags)
            else:
                self.increment_counter("llm.failures", 1, tags)
            
            self.record_metric("llm.duration_ms", duration_ms, MetricType.TIMER, tags)
            
            # Taxa de sucesso global
            total_requests = self._task_metrics['llm_requests']
            total_successes = self._task_metrics['llm_successes']
            success_rate = total_successes / total_requests if total_requests > 0 else 0.0
            
            self.set_gauge("llm.success_rate", success_rate)
            self.set_gauge("llm.total_requests", total_requests)
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Retorna métricas de performance atuais"""
        with self._lock:
            # Métricas de sistema mais recentes
            system_metrics = {}
            for metric_name in ["system.cpu_percent", "system.memory_percent", "system.memory_used_mb", "system.disk_usage_percent"]:
                values = self._metrics.get(metric_name)
                if values:
                    system_metrics[metric_name] = values[-1].value
            
            # Métricas de tarefas
            total_tasks = self._task_metrics['total_tasks']
            completed_tasks = self._task_metrics['completed_tasks']
            failed_tasks = self._task_metrics['failed_tasks']
            
            avg_duration = 0.0
            if self._task_metrics['task_durations']:
                avg_duration = sum(self._task_metrics['task_durations']) / len(self._task_metrics['task_durations'])
            
            # Taxa de sucesso LLM
            llm_success_rate = 0.0
            if self._task_metrics['llm_requests'] > 0:
                llm_success_rate = self._task_metrics['llm_successes'] / self._task_metrics['llm_requests']
            
            return PerformanceMetrics(
                cpu_percent=system_metrics.get("system.cpu_percent", 0.0),
                memory_percent=system_metrics.get("system.memory_percent", 0.0),
                memory_used_mb=system_metrics.get("system.memory_used_mb", 0.0),
                disk_usage_percent=system_metrics.get("system.disk_usage_percent", 0.0),
                active_tasks=0,  # TODO: Implementar tracking de tarefas ativas
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                avg_task_duration_ms=avg_duration,
                llm_request_count=self._task_metrics['llm_requests'],
                llm_success_rate=llm_success_rate,
                timestamp=datetime.now()
            )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Retorna resumo do status de saúde"""
        healthy_components = sum(1 for status in self._health_checks.values() if status.is_healthy)
        total_components = len(self._health_checks)
        
        return {
            'overall_healthy': healthy_components == total_components,
            'healthy_components': healthy_components,
            'total_components': total_components,
            'health_score': healthy_components / total_components if total_components > 0 else 1.0,
            'components': {
                name: {
                    'healthy': status.is_healthy,
                    'last_check': status.last_check.isoformat(),
                    'error_message': status.error_message
                }
                for name, status in self._health_checks.items()
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna alertas recentes"""
        return list(self._alert_history)[-limit:]
    
    def get_trace_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Retorna resumo de traces"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_traces = [
            trace for trace in self._traces.values()
            if trace.start_time >= cutoff_time
        ]
        
        completed_traces = [t for t in recent_traces if t.status == "completed"]
        error_traces = [t for t in recent_traces if t.status == "error"]
        
        avg_duration = 0.0
        if completed_traces:
            avg_duration = sum(t.duration_ms or 0 for t in completed_traces) / len(completed_traces)
        
        return {
            'total_traces': len(recent_traces),
            'completed_traces': len(completed_traces),
            'error_traces': len(error_traces),
            'success_rate': len(completed_traces) / len(recent_traces) if recent_traces else 0.0,
            'avg_duration_ms': avg_duration,
            'time_window_hours': hours
        }
    
    def export_metrics(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Exporta métricas em formato especificado"""
        metrics_data = {}
        
        with self._lock:
            for metric_name, values in self._metrics.items():
                if values:
                    latest_value = values[-1]
                    metrics_data[metric_name] = {
                        'value': latest_value.value,
                        'timestamp': latest_value.timestamp.isoformat(),
                        'tags': latest_value.tags
                    }
        
        if format.lower() == "json":
            return json.dumps(metrics_data, indent=2)
        else:
            return metrics_data
    
    def create_dashboard_data(self) -> Dict[str, Any]:
        """Cria dados para dashboard"""
        return {
            'performance_metrics': self.get_performance_metrics().__dict__,
            'health_summary': self.get_health_summary(),
            'recent_alerts': self.get_recent_alerts(5),
            'trace_summary': self.get_trace_summary(),
            'system_info': {
                'monitoring_active': self.is_running,
                'total_metrics': len(self._metrics),
                'total_traces': len(self._traces),
                'uptime_hours': (datetime.now() - datetime.now()).total_seconds() / 3600  # TODO: Track actual uptime
            }
        }
    
    def __enter__(self):
        """Context manager support"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop_monitoring()