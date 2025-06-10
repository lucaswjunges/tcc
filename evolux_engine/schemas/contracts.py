from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pydantic_settings import SettingsConfigDict
from pydantic.v1 import BaseSettings  # Se estiver usando Pydantic v2



class Task(BaseModel):
    id: int
    description: str
    tool: str
    parameters: Dict[str, Any]
    dependencies: List[int] = Field(default_factory=list)

class Plan(BaseModel):
    goal: str
    tasks: List[Task]

class ActionResult(BaseModel):
    task_id: int
    status: str
    result: str


# Definições de configuração
class ModelMapping(BaseModel):
    planner: str
    executor: str


class SystemConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', env_prefix='EVOLUX_')
    llm_provider: str = "openrouter"
    openrouter_api_key: str
    model_mapping: Dict[str, Any] = {
        "default": "anthropic/claude-3-haiku",
        "planner": "anthropic/claude-3-haiku",  # Adicionado
        "executor": "anthropic/claude-3-haiku",  # Adicionado
        "code_generation": "deepseek-coder-33b",
        "validation": "claude-3-opus"
    }

    project_base_dir: str = "project_workspaces"



