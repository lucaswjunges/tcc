# src/models/project_context.py (VERSÃO FINAL E CORRIGIDA)

from __future__ import annotations
import uuid
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.contracts import SystemConfig

class ProjectState(str, Enum):
    STARTING = "starting"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str
    tool_name: str
    tool_args: dict
    status: str = "pending"
    result: Optional[str] = None

class ProjectContext(BaseModel):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_goal: str
    project_type: str = ""
    current_state: ProjectState = ProjectState.PLANNING
    workspace_path: Path
    tasks: list[Task] = []
    completed_tasks: list[Task] = []
    
    # --- A LINHA CORRIGIDA/ADICIONADA ESTÁ AQUI ---
    # Nós declaramos oficialmente que o ProjectContext PODE ter um campo 'config'.
    config: Optional["SystemConfig"] = None

    class Config:
        arbitrary_types_allowed = True
        defer_build = True

