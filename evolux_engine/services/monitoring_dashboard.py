# Dashboard de Monitoramento para Evolux Engine

import json
import time
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from evolux_engine.services.advanced_monitoring import get_metrics_collector
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("monitoring_dashboard")

class MonitoringDashboard:
    """Gerador de dashboard HTML para monitoramento"""
    
    def __init__(self, output_dir: str = "monitoring_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics_collector = get_metrics_collector()
        
    def generate_html_dashboard(self) -> str:
        """Gera dashboard HTML completo"""
        dashboard_data = self.metrics_collector.get_dashboard_data()
        
        html_content = self._generate_html_template(dashboard_data)
        
        # Salvar HTML
        html_path = self.output_dir / "dashboard.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Salvar dados JSON para JavaScript
        json_path = self.output_dir / "dashboard_data.json"
        with open(json_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
            
        logger.info("Dashboard generated", html_path=str(html_path))
        return str(html_path)
        
    def _generate_html_template(self, data: Dict[str, Any]) -> str:
        """Gera template HTML do dashboard"""
        
        # Status colors
        status_colors = {
            'healthy': '#22c55e',
            'warning': '#f59e0b', 
            'degraded': '#f59e0b',
            'failing': '#ef4444',
            'critical': '#dc2626'
        }
        
        system_status = data['system']['status']
        llm_status = data['llm']['status']
        task_status = data['tasks']['status']
        overall_status = data['health']['overall']
        
        system_latest = data['system']['latest'] or {}
        
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evolux Engine - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #334155;
        }}
        
        .header h1 {{
            color: #f8fafc;
            font-size: 2rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: {status_colors.get(overall_status, '#6b7280')};
            box-shadow: 0 0 10px {status_colors.get(overall_status, '#6b7280')}60;
        }}
        
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .card h2 {{
            color: #f8fafc;
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
        }}
        
        .metric {{
            text-align: center;
            padding: 1rem;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #f8fafc;
            display: block;
        }}
        
        .metric-label {{
            font-size: 0.875rem;
            color: #94a3b8;
            margin-top: 0.25rem;
        }}
        
        .alert {{
            background: #fef2f2;
            color: #991b1b;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border-left: 4px solid #dc2626;
            margin-bottom: 0.75rem;
        }}
        
        .alert-critical {{
            background: #450a0a;
            color: #fca5a5;
            border-left-color: #dc2626;
        }}
        
        .alert-warning {{
            background: #451a03;
            color: #fed7aa;
            border-left-color: #f59e0b;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #374151;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        
        .progress-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
        }}
        
        .status-healthy {{
            background: #22c55e20;
            color: #22c55e;
        }}
        
        .status-warning {{
            background: #f59e0b20;
            color: #f59e0b;
        }}
        
        .status-critical {{
            background: #ef444420;
            color: #ef4444;
        }}
        
        .refresh-info {{
            text-align: center;
            color: #64748b;
            font-size: 0.875rem;
            margin-top: 2rem;
        }}
        
        .chart-container {{
            height: 300px;
            margin-top: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
                padding: 1rem;
            }}
            
            .header {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <div class="status-indicator"></div>
            Evolux Engine Monitoring
            <span class="status-badge status-{overall_status}">
                {overall_status.upper()}
            </span>
        </h1>
    </div>
    
    <div class="dashboard">
        <!-- System Metrics -->
        <div class="card">
            <h2>🖥️ System Metrics</h2>
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{system_latest.get('cpu_percent', 0):.1f}%</span>
                    <div class="metric-label">CPU Usage</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {system_latest.get('cpu_percent', 0)}%; background: {'#ef4444' if system_latest.get('cpu_percent', 0) > 80 else '#22c55e'};"></div>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-value">{system_latest.get('memory_percent', 0):.1f}%</span>
                    <div class="metric-label">Memory Usage</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {system_latest.get('memory_percent', 0)}%; background: {'#ef4444' if system_latest.get('memory_percent', 0) > 85 else '#22c55e'};"></div>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-value">{system_latest.get('memory_used_mb', 0):.0f}</span>
                    <div class="metric-label">Memory (MB)</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{system_latest.get('threads_count', 0)}</span>
                    <div class="metric-label">Threads</div>
                </div>
            </div>
        </div>
        
        <!-- LLM Performance -->
        <div class="card">
            <h2>🤖 LLM Performance</h2>
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{len(data['llm']['latest'])}</span>
                    <div class="metric-label">Active Models</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(m.get('requests_per_minute', 0) for m in data['llm']['latest']):.1f}</span>
                    <div class="metric-label">Requests/min</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(m.get('avg_latency_ms', 0) for m in data['llm']['latest']) / max(1, len(data['llm']['latest'])):.0f}ms</span>
                    <div class="metric-label">Avg Latency</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(m.get('success_rate', 0) for m in data['llm']['latest']) / max(1, len(data['llm']['latest'])):.2%}</span>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
        </div>
        
        <!-- Task Execution -->
        <div class="card">
            <h2>⚡ Task Execution</h2>
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{len(data['tasks']['latest'])}</span>
                    <div class="metric-label">Recent Tasks</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(1 for t in data['tasks']['latest'] if t.get('success', False))}</span>
                    <div class="metric-label">Successful</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(t.get('execution_time_ms', 0) for t in data['tasks']['latest']) / max(1, len(data['tasks']['latest'])):.0f}ms</span>
                    <div class="metric-label">Avg Time</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(1 for t in data['tasks']['latest'] if t.get('dependency_cache_hit', False))} / {len(data['tasks']['latest'])}</span>
                    <div class="metric-label">Cache Hits</div>
                </div>
            </div>
        </div>
        
        <!-- Alerts -->
        <div class="card">
            <h2>🚨 Active Alerts</h2>
            {self._generate_alerts_html(data['alerts'])}
        </div>
        
        <!-- Health Status -->
        <div class="card">
            <h2>💚 Health Status</h2>
            <div class="metric-grid">
                <div class="metric">
                    <span class="status-badge status-{system_status}">{system_status.upper()}</span>
                    <div class="metric-label">System</div>
                </div>
                <div class="metric">
                    <span class="status-badge status-{llm_status}">{llm_status.upper()}</span>
                    <div class="metric-label">LLM</div>
                </div>
                <div class="metric">
                    <span class="status-badge status-{task_status}">{task_status.upper()}</span>
                    <div class="metric-label">Tasks</div>
                </div>
                <div class="metric">
                    <span class="metric-value">{data['health']['uptime_hours']:.1f}h</span>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="refresh-info">
        Last updated: {datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
        <br>
        Auto-refresh every 30 seconds
    </div>
    
    <script>
        // Auto refresh every 30 seconds
        setTimeout(() => {{
            window.location.reload();
        }}, 30000);
        
        // Load dashboard data
        fetch('./dashboard_data.json')
            .then(response => response.json())
            .then(data => {{
                console.log('Dashboard data loaded:', data);
            }})
            .catch(error => {{
                console.error('Failed to load dashboard data:', error);
            }});
    </script>
</body>
</html>
"""
    
    def _generate_alerts_html(self, alerts_data: Dict[str, Any]) -> str:
        """Gera HTML para seção de alertas"""
        if alerts_data['count'] == 0:
            return '<div style="text-align: center; color: #22c55e; padding: 2rem;">✅ No active alerts</div>'
        
        alerts_html = ""
        for alert in alerts_data['active']:
            alert_type = 'critical' if alert.get('value', 0) > alert.get('threshold', 0) * 1.2 else 'warning'
            alerts_html += f"""
            <div class="alert alert-{alert_type}">
                <strong>{alert.get('description', 'Unknown Alert')}</strong><br>
                Value: {alert.get('value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}<br>
                <small>Type: {alert.get('type', 'unknown')} | {datetime.fromtimestamp(alert.get('timestamp', 0)).strftime('%H:%M:%S')}</small>
            </div>
            """
        
        return alerts_html
        
    def generate_json_report(self) -> str:
        """Gera relatório em JSON"""
        dashboard_data = self.metrics_collector.get_dashboard_data()
        
        json_path = self.output_dir / f"report_{int(time.time())}.json"
        with open(json_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
            
        logger.info("JSON report generated", json_path=str(json_path))
        return str(json_path)
        
    def start_auto_generation(self, interval: int = 30):
        """Inicia geração automática de dashboard"""
        import threading
        import time
        
        def generate_loop():
            while True:
                try:
                    self.generate_html_dashboard()
                    time.sleep(interval)
                except Exception as e:
                    logger.error("Dashboard generation failed", error=str(e))
                    time.sleep(interval)
                    
        thread = threading.Thread(target=generate_loop, daemon=True)
        thread.start()
        logger.info("Auto dashboard generation started", interval=interval)

# Função utilitária
def create_dashboard(output_dir: str = "monitoring_output") -> MonitoringDashboard:
    """Cria instância do dashboard"""
    return MonitoringDashboard(output_dir)