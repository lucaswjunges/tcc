# src/schemas/contracts.py (VERSÃO CORRIGIDA)

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

# --- A CORREÇÃO CRÍTICA ESTÁ AQUI ---
# Colocamos o import dentro do bloco TYPE_CHECKING para quebrar
# o ciclo de importação em tempo de execução.
if TYPE_CHECKING:
    from src.models.project_context import ProjectContext

class ModelMapping(BaseModel):
    planner: str
    executor: str

class SystemConfig(BaseModel):
    llm_provider: str = "openrouter"
    model_mapping: ModelMapping = Field(default_factory=ModelMapping)
    openrouter_api_key: Optional[str] = None
