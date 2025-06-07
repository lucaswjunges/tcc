# src/schemas/contracts.py (VERSÃO UNIFICADA E FINAL)

from pydantic import BaseModel, Field, SecretStr
from typing import List, Dict, Any

# --- Modelos de Configuração ---

class ModelMapping(BaseModel):
    """Mapeia os papéis dos agentes para modelos de LLM específicos."""
    planner: str
    executor: str

class SystemConfig(BaseModel):
    """A configuração principal do sistema, carregada do ambiente."""
    llm_provider: str = "openrouter"
    openrouter_api_key: SecretStr
    model_mapping: ModelMapping
    project_workspace_dir: str = "project_workspaces"

# --- Modelos de Plano e Tarefas ---

class Task(BaseModel):
    """Define a estrutura de uma única tarefa executável."""
    id: int = Field(..., description="Um ID numérico único para a tarefa.")
    description: str = Field(..., description="Uma descrição clara e concisa do que a tarefa deve fazer.")
    tool: str = Field(..., description="O nome da ferramenta a ser usada (ex: 'write_file', 'finish').")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Os parâmetros a serem passados para a ferramenta.")
    dependencies: List[int] = Field(default_factory=list, description="Uma lista de IDs de tarefas das quais esta tarefa depende.")

class Plan(BaseModel):
    """Representa o plano completo, que é uma lista de tarefas."""
    goal: str = Field(..., description="O objetivo original de alto nível que este plano visa alcançar.")
    tasks: List[Task] = Field(..., description="A sequência de tarefas a serem executadas.")
