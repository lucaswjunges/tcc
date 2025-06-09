# src/models/project_context.py

from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..schemas.contracts import Plan

# Para armazenar o resultado de cada ação
class ActionHistory(BaseModel):
    task_id: int
    status: str  # 'success' ou 'error'
    result: str

class ProjectContext(BaseModel):
    """
    Mantém todo o estado de um projeto específico.
    """
    # CORREÇÃO: project_id agora é uma string simples, não um UUID.
    project_id: str

    # CORREÇÃO: O nome do campo é 'goal', não 'project_goal'.
    goal: str

    # CORREÇÃO: O nome do campo é 'workspace_dir', não 'workspace_path'.
    workspace_dir: str

    # Campos opcionais para logs e planos
    logs_dir: Optional[str] = None
    plan: Optional[Plan] = None

    # Histórico de ações
    history: List[ActionHistory] = Field(default_factory=list)

    def get_workspace_path(self) -> Path:
        """Retorna o caminho completo para o diretório de trabalho do projeto."""
        return Path(self.workspace_dir) / self.project_id / "workspace"

    def get_logs_path(self) -> Path:
        """Retorna o caminho para o arquivo de log do projeto."""
        log_dir = Path(self.workspace_dir) / self.project_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "execution.log"

    def add_plan(self, plan: Plan):
        self.plan = plan

    def add_action_result(self, task_id: int, status: str, result: str):
        self.history.append(ActionHistory(task_id=task_id, status=status, result=result))

    def get_full_context_for_llm(self) -> Dict[str, Any]:
        """Retorna um dicionário com todo o contexto para ser usado em prompts."""
        return {
            "project_id": self.project_id,
            "goal": self.goal,
            "plan": self.plan.model_dump() if self.plan else None,
            "history": [h.model_dump() for h in self.history]
        }
