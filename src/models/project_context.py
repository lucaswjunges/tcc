# src/models/project_context.py

from __future__ import annotations
import uuid
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

# Importação condicional para evitar dependência circular
if TYPE_CHECKING:
    from src.schemas.contracts import SystemConfig

class ProjectState(str, Enum):
    """Enum para os possíveis estados de um projeto."""
    STARTING = "starting"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    """Representa uma única tarefa a ser executada."""
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str
    tool_name: str
    tool_args: dict
    status: str = "pending"  # pending, completed, failed
    result: Optional[str] = None

class ProjectContext(BaseModel):
    """
    O cérebro do projeto. Armazena todo o estado atual,
    objetivos e plano de execução.
    """
    # Meta
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_goal: str
    project_type: str = ""

    # State
    current_state: ProjectState = ProjectState.PLANNING
    workspace_path: Path
    tasks: list[Task] = []
    completed_tasks: list[Task] = []
    
    # Adicionando o campo de configuração que faltava
    config: Optional["SystemConfig"] = None

    class Config:
        # Permite que o Pydantic lide com tipos como Path e UUID
        arbitrary_types_allowed = True
        # Necessário para referenciar SystemConfig como string
        defer_build = True
