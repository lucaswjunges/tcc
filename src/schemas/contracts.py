# src/schemas/contracts.py (VERSÃO FINAL-FINAL)

from __future__ import annotations
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings  # <-- IMPORTAMOS ISSO
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.project_context import ProjectContext

class ModelMapping(BaseModel):
    planner: str = 'anthropic/claude-3-haiku'
    executor: str = 'anthropic/claude-3-haiku'

# --- A CORREÇÃO ESTÁ AQUI ---
# A SystemConfig agora herda de BaseSettings, tornando-se a nossa classe
# principal de configuração.
class SystemConfig(BaseSettings):
    llm_provider: str = "openrouter"
    model_mapping: ModelMapping = Field(default_factory=ModelMapping)
    openrouter_api_key: Optional[str] = None

    class Config:
        # Ela agora sabe como ler do arquivo .env
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # Isso faz com que OPENROUTER_API_KEY no .env mapeie para o campo
        env_prefix = '' 
