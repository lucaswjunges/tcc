# src/schemas/contracts.py (VERSÃO COMPLETA E CORRIGIDA)

from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

# =========================================================================
# ESTADOS E TIPOS
# =========================================================================

class ProjectState(str, Enum):
    """
    Enumeração dos possíveis estados de um projeto.
    """
    planning = "planning"
    executing = "executing"
    completed = "completed"
    failed = "failed"

class TaskType(str, Enum):
    """
    Enumeração dos possíveis tipos de tarefas.
    """
    create_file = "create_file"
    run_command = "run_command"
    unknown = "unknown"

# =========================================================================
# ESTRUTURAS DE DADOS
# =========================================================================

class Task(BaseModel):
    """
    Representa uma única tarefa a ser executada.
    """
    id: UUID = Field(default_factory=uuid4)
    description: str
    type: str  # Poderia ser TaskType, mas string dá mais flexibilidade para a IA
    dependencies: list[UUID] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)

class ProjectContext(BaseModel):
    """
    Mantém todo o estado e contexto de um projeto.
    """
    project_id: UUID = Field(default_factory=uuid4)
    project_goal: str = ""
    project_type: str = ""
    current_state: ProjectState = ProjectState.planning
    workspace_path: Path
    
    tasks: list[Task] = Field(default_factory=list)
    completed_tasks: list[Task] = Field(default_factory=list)
    
    class Config:
        # Permite que o Pydantic trabalhe com tipos como pathlib.Path
        arbitrary_types_allowed = True

# =========================================================================
# CONFIGURAÇÃO DO SISTEMA
# =========================================================================

class ModelMapping(BaseModel):
    """
    Mapeia os papéis dos agentes para modelos de IA específicos.
    """
    planner: str
    executor: str

class SystemConfig(BaseModel):
    """
    Carrega e valida a configuração geral do sistema a partir do config.yaml.
    """
    llm_provider: str
    model_mapping: ModelMapping
    openrouter_api_key: Optional[str] = None
