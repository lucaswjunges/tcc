# src/schemas/contracts.py (VERSÃO CORRIGIDA)

import uuid
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# =========================================================================
# AQUI ESTÁ A ADIÇÃO NECESSÁRIA:
# Usamos um Enum para definir os estados possíveis de um projeto.
# Isso torna o código mais seguro e legível.
class ProjectStatus(str, Enum):
    PLANNING = "planning"
    PENDING_EXECUTION = "pending_execution"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
# =========================================================================

# === Modelos de Configuração ===

class ProviderSettings(BaseModel):
    base_url: str
    api_key_env: str

class ApiSettings(BaseModel):
    default_provider: str
    provider: dict[str, ProviderSettings]

class ModelMapping(BaseModel):
    planner: str
    executor: str
    validator: str

class EngineSettings(BaseModel):
    max_iterations: int
    security_level: str

class SystemConfig(BaseModel):
    api_settings: ApiSettings
    model_mapping: ModelMapping
    engine_settings: EngineSettings


# === Modelos de Contexto do Projeto ===

class Task(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    description: str
    type: str
    dependencies: List[uuid.UUID] = []
    acceptance_criteria: List[str]
    status: str = "pending" # pending, in_progress, completed, failed
    result: Optional[str] = None

class ProjectContext(BaseModel):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_goal: Optional[str] = None
    # CORRIGIMOS AQUI TAMBÉM: o status agora usa nosso Enum
    current_status: ProjectStatus = Field(default=ProjectStatus.PLANNING)
    tasks: List[Task] = []
    history: List[str] = []

