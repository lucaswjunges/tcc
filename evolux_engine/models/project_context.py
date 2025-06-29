import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..schemas.contracts import Task, ProjectStatus

class EngineConfig(BaseModel):
    """Configurações do engine para o projeto"""
    max_project_iterations: int = 50
    max_iterations_per_task: int = 3
    default_executor_model: Optional[str] = None
    timeout_seconds: int = 300

class ProjectMetrics(BaseModel):
    """Métricas do projeto"""
    total_iterations: int = 0
    total_cost_usd: float = 0.0
    total_tokens: Dict[str, int] = Field(default_factory=lambda: {"prompt": 0, "completion": 0})
    error_count: int = 0
    last_updated: Optional[datetime] = None

class ArtifactState(BaseModel):
    """Estado de um artefato (arquivo) no projeto"""
    path: str
    hash: Optional[str] = None
    summary: Optional[str] = None
    last_modified: Optional[datetime] = None

class ProjectContext(BaseModel):
    """
    Mantém todo o estado de um projeto específico.
    """
    project_id: str
    project_name: str
    project_goal: str
    project_type: str = "general"
    status: ProjectStatus = ProjectStatus.INITIALIZING
    
    # Caminhos
    workspace_path: Path
    
    # Filas de tarefas
    task_queue: List[Task] = Field(default_factory=list)
    completed_tasks: List[Task] = Field(default_factory=list)
    
    # Estado dos artefatos
    artifacts_state: Dict[str, ArtifactState] = Field(default_factory=dict)
    
    # Métricas e configuração
    metrics: ProjectMetrics = Field(default_factory=ProjectMetrics)
    engine_config: EngineConfig = Field(default_factory=EngineConfig)
    
    # Histórico de iterações seria adicionado aqui
    # iteration_history: List[IterationLog] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def get_project_path(self, subdir: str = "") -> str:
        """Retorna caminho para subdiretório do projeto"""
        if subdir:
            return str(self.workspace_path / subdir)
        return str(self.workspace_path)
    
    def get_artifact_path(self, relative_path: str) -> str:
        """Retorna caminho completo para um artefato"""
        return str(self.workspace_path / "artifacts" / relative_path)
    
    def get_log_path(self, filename: str) -> str:
        """Retorna caminho para arquivo de log"""
        logs_dir = self.workspace_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        return str(logs_dir / filename)
    
    def update_artifact_state(self, path: str, state: ArtifactState):
        """Atualiza o estado de um artefato"""
        self.artifacts_state[path] = state
    
    def remove_artifact_state(self, path: str):
        """Remove o estado de um artefato"""
        if path in self.artifacts_state:
            del self.artifacts_state[path]
    
    def get_artifacts_structure_summary(self) -> str:
        """Retorna resumo da estrutura de artefatos"""
        if not self.artifacts_state:
            return "Nenhum artefato criado ainda."
        
        summary = "Artefatos atuais:\n"
        for path, state in self.artifacts_state.items():
            summary += f"- {path}"
            if state.summary:
                summary += f": {state.summary}"
            summary += "\n"
        return summary
    
    async def save_context(self):
        """Salva o contexto em arquivo JSON"""
        context_file = self.workspace_path / "context.json"
        # Converter Path para string para serialização JSON
        data = self.model_dump(mode='json')
        data['workspace_path'] = str(self.workspace_path)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def load_from_file(cls, context_file: Path) -> 'ProjectContext':
        """Carrega contexto de arquivo JSON"""
        with open(context_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Converter string de volta para Path
        if 'workspace_path' in data:
            data['workspace_path'] = Path(data['workspace_path'])
            
        return cls(**data)