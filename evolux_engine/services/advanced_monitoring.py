# Sistema de Monitoramento Avançado para Evolux Engine

import asyncio
import time
import json
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path

from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("advanced_monitoring")

@dataclass
class MetricPoint:
    """Ponto de métrica com timestamp"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    open_files: int
    threads_count: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class LLMMetrics:
    """Métricas específicas de LLM"""
    provider: str
    model: str
    requests_per_minute: float
    avg_latency_ms: float
    success_rate: float
    tokens_per_second: float
    cost_per_hour: float
    circuit_breaker_state: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class TaskMetrics:
    """Métricas de execução de tarefas"""
    task_type: str
    execution_time_ms: float
    success: bool
    parallel_count: int
    dependency_cache_hit: bool
    resource_usage: Dict[str, float]
    timestamp: float = field(default_factory=time.time)

class MetricsCollector:
    """Coletor de métricas em tempo real"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        
        # Armazenamento de métricas
        self.system_metrics: deque = deque(maxlen=max_points)
        self.llm_metrics: deque = deque(maxlen=max_points)
        self.task_metrics: deque = deque(maxlen=max_points)
        
        # Métricas agregadas
        self.aggregated_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Alertas
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'llm_latency_ms': 10000.0,
            'llm_success_rate': 0.95,
            'task_failure_rate': 0.1
        }
        
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Thread para coleta contínua
        self._running = False
        self._collection_thread: Optional[threading.Thread] = None
        
    def start_collection(self, interval: float = 10.0):
        """Inicia coleta contínua de métricas"""
        if self._running:
            return
            
        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            args=(interval,),
            daemon=True
        )
        self._collection_thread.start()
        logger.info("Metrics collection started", interval=interval)
        
    def stop_collection(self):
        """Para coleta de métricas"""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)
        logger.info("Metrics collection stopped")
        
    def _collection_loop(self, interval: float):
        """Loop principal de coleta"""
        while self._running:
            try:
                # Coletar métricas do sistema
                system_metrics = self._collect_system_metrics()
                self.system_metrics.append(system_metrics)
                
                # Verificar alertas
                self._check_system_alerts(system_metrics)
                
                # Agregar métricas
                self._update_aggregated_metrics()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error("Error in metrics collection", error=str(e))
                time.sleep(interval)
                
    def _collect_system_metrics(self) -> SystemMetrics:
        """Coleta métricas do sistema operacional"""
        try:
            # CPU e memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Rede
            network = psutil.net_io_counters()
            
            # Processo atual
            process = psutil.Process()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                open_files=len(process.open_files()),
                threads_count=process.num_threads()
            )
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0, 0)
            
    def record_llm_metrics(self, metrics: LLMMetrics):
        """Registra métricas de LLM"""
        self.llm_metrics.append(metrics)
        self._check_llm_alerts(metrics)
        
    def record_task_metrics(self, metrics: TaskMetrics):
        """Registra métricas de tarefa"""
        self.task_metrics.append(metrics)
        self._check_task_alerts(metrics)
        
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Verifica alertas do sistema"""
        alerts_to_check = [
            ('cpu_percent', metrics.cpu_percent, 'High CPU Usage'),
            ('memory_percent', metrics.memory_percent, 'High Memory Usage'),
            ('disk_usage_percent', metrics.disk_usage_percent, 'High Disk Usage'),
        ]
        
        for metric_name, value, description in alerts_to_check:
            threshold = self.alert_thresholds.get(metric_name, float('inf'))
            
            if value >= threshold:
                self._trigger_alert(metric_name, {
                    'type': 'system',
                    'description': description,
                    'value': value,
                    'threshold': threshold,
                    'timestamp': time.time()
                })
            else:
                self._clear_alert(metric_name)
                
    def _check_llm_alerts(self, metrics: LLMMetrics):
        """Verifica alertas de LLM"""
        # Latência alta
        if metrics.avg_latency_ms >= self.alert_thresholds.get('llm_latency_ms', 10000):
            self._trigger_alert(f'llm_latency_{metrics.provider}_{metrics.model}', {
                'type': 'llm',
                'description': f'High latency for {metrics.provider} {metrics.model}',
                'value': metrics.avg_latency_ms,
                'threshold': self.alert_thresholds['llm_latency_ms'],
                'timestamp': time.time()
            })
            
        # Taxa de sucesso baixa
        if metrics.success_rate <= self.alert_thresholds.get('llm_success_rate', 0.95):
            self._trigger_alert(f'llm_success_rate_{metrics.provider}_{metrics.model}', {
                'type': 'llm',
                'description': f'Low success rate for {metrics.provider} {metrics.model}',
                'value': metrics.success_rate,
                'threshold': self.alert_thresholds['llm_success_rate'],
                'timestamp': time.time()
            })
            
    def _check_task_alerts(self, metrics: TaskMetrics):
        """Verifica alertas de tarefas"""
        # Calcular taxa de falha recente
        recent_tasks = [m for m in self.task_metrics 
                       if m.timestamp > time.time() - 300]  # Últimos 5 minutos
        
        if recent_tasks:
            failure_rate = sum(1 for m in recent_tasks if not m.success) / len(recent_tasks)
            
            if failure_rate >= self.alert_thresholds.get('task_failure_rate', 0.1):
                self._trigger_alert('task_failure_rate', {
                    'type': 'task',
                    'description': 'High task failure rate',
                    'value': failure_rate,
                    'threshold': self.alert_thresholds['task_failure_rate'],
                    'timestamp': time.time()
                })
                
    def _trigger_alert(self, alert_id: str, alert_data: Dict[str, Any]):
        """Dispara um alerta"""
        if alert_id not in self.active_alerts:
            self.active_alerts[alert_id] = alert_data
            logger.warning("Alert triggered", alert_id=alert_id, **alert_data)
            
            # Chamar callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert_id, alert_data)
                except Exception as e:
                    logger.error("Alert callback failed", error=str(e))
                    
    def _clear_alert(self, alert_id: str):
        """Limpa um alerta"""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            logger.info("Alert cleared", alert_id=alert_id)
            
    def _update_aggregated_metrics(self):
        """Atualiza métricas agregadas"""
        current_time = time.time()
        
        # Métricas do sistema (última hora)
        recent_system = [m for m in self.system_metrics 
                        if m.timestamp > current_time - 3600]
        
        if recent_system:
            self.aggregated_metrics['system'] = {
                'avg_cpu_percent': sum(m.cpu_percent for m in recent_system) / len(recent_system),
                'max_cpu_percent': max(m.cpu_percent for m in recent_system),
                'avg_memory_percent': sum(m.memory_percent for m in recent_system) / len(recent_system),
                'max_memory_percent': max(m.memory_percent for m in recent_system),
                'avg_memory_used_mb': sum(m.memory_used_mb for m in recent_system) / len(recent_system),
                'sample_count': len(recent_system)
            }
            
        # Métricas de LLM (última hora)
        recent_llm = [m for m in self.llm_metrics 
                     if m.timestamp > current_time - 3600]
        
        if recent_llm:
            by_provider = defaultdict(list)
            for m in recent_llm:
                by_provider[f"{m.provider}_{m.model}"].append(m)
                
            for provider_model, metrics in by_provider.items():
                self.aggregated_metrics[f'llm_{provider_model}'] = {
                    'avg_latency_ms': sum(m.avg_latency_ms for m in metrics) / len(metrics),
                    'avg_success_rate': sum(m.success_rate for m in metrics) / len(metrics),
                    'total_requests': sum(m.requests_per_minute for m in metrics),
                    'avg_tokens_per_second': sum(m.tokens_per_second for m in metrics) / len(metrics),
                    'total_cost': sum(m.cost_per_hour for m in metrics),
                    'sample_count': len(metrics)
                }
                
        # Métricas de tarefas (última hora)
        recent_tasks = [m for m in self.task_metrics 
                       if m.timestamp > current_time - 3600]
        
        if recent_tasks:
            by_type = defaultdict(list)
            for m in recent_tasks:
                by_type[m.task_type].append(m)
                
            for task_type, metrics in by_type.items():
                successful = [m for m in metrics if m.success]
                
                self.aggregated_metrics[f'task_{task_type}'] = {
                    'total_count': len(metrics),
                    'success_count': len(successful),
                    'success_rate': len(successful) / len(metrics) if metrics else 0,
                    'avg_execution_time_ms': sum(m.execution_time_ms for m in successful) / len(successful) if successful else 0,
                    'avg_parallel_count': sum(m.parallel_count for m in metrics) / len(metrics),
                    'cache_hit_rate': sum(1 for m in metrics if m.dependency_cache_hit) / len(metrics) if metrics else 0
                }
                
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Adiciona callback para alertas"""
        self.alert_callbacks.append(callback)
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados para dashboard"""
        current_time = time.time()
        
        # Últimas métricas
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        latest_llm = list(self.llm_metrics)[-10:] if self.llm_metrics else []
        latest_tasks = list(self.task_metrics)[-10:] if self.task_metrics else []
        
        # Alertas ativos
        active_alerts_count = len(self.active_alerts)
        critical_alerts = [alert for alert in self.active_alerts.values() 
                          if alert.get('value', 0) > alert.get('threshold', 0) * 1.2]
        
        return {
            'timestamp': current_time,
            'system': {
                'latest': latest_system.__dict__ if latest_system else None,
                'aggregated': self.aggregated_metrics.get('system', {}),
                'status': 'critical' if any('system' in alert.get('type', '') for alert in self.active_alerts.values()) else 'healthy'
            },
            'llm': {
                'latest': [m.__dict__ for m in latest_llm],
                'aggregated': {k: v for k, v in self.aggregated_metrics.items() if k.startswith('llm_')},
                'status': 'degraded' if any('llm' in alert.get('type', '') for alert in self.active_alerts.values()) else 'healthy'
            },
            'tasks': {
                'latest': [m.__dict__ for m in latest_tasks],
                'aggregated': {k: v for k, v in self.aggregated_metrics.items() if k.startswith('task_')},
                'status': 'failing' if any('task' in alert.get('type', '') for alert in self.active_alerts.values()) else 'healthy'
            },
            'alerts': {
                'count': active_alerts_count,
                'critical_count': len(critical_alerts),
                'active': list(self.active_alerts.values()),
                'thresholds': self.alert_thresholds
            },
            'health': {
                'overall': 'critical' if critical_alerts else 'warning' if active_alerts_count > 0 else 'healthy',
                'uptime_hours': (current_time - getattr(self, '_start_time', current_time)) / 3600
            }
        }
        
    def export_metrics(self, filepath: str, format: str = 'json'):
        """Exporta métricas para arquivo"""
        dashboard_data = self.get_dashboard_data()
        
        if format == 'json':
            with open(filepath, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
        elif format == 'csv':
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # System metrics
                writer.writerow(['Type', 'Metric', 'Value', 'Timestamp'])
                if dashboard_data['system']['latest']:
                    for key, value in dashboard_data['system']['latest'].items():
                        writer.writerow(['system', key, value, dashboard_data['timestamp']])
                        
        logger.info("Metrics exported", filepath=filepath, format=format)

# Instância global
_global_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Obtém a instância global do coletor de métricas"""
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
        _global_metrics_collector._start_time = time.time()
        
    return _global_metrics_collector

def start_monitoring(interval: float = 10.0):
    """Inicia monitoramento global"""
    collector = get_metrics_collector()
    collector.start_collection(interval)
    
def stop_monitoring():
    """Para monitoramento global"""
    global _global_metrics_collector
    
    if _global_metrics_collector:
        _global_metrics_collector.stop_collection()
        _global_metrics_collector = None