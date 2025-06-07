# src/services/context_manager.py (VERSÃO CORRIGIDA)

import json
from pathlib import Path
from src.services.observability_service import log

# --- A CORREÇÃO ESTÁ AQUI ---
# Nós agora importamos ProjectContext e ProjectState da sua fonte original e correta.
from src.models.project_context import ProjectContext, ProjectState

class ContextManager:
    """Gerencia a leitura e escrita do estado do projeto (context.json)."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.workspace_path = Path(f"project_workspaces/{self.project_id}")
        self.context_file = self.workspace_path / "context.json"
        log.info("ContextManager initialized.", project_id=self.project_id)

    def create_context(self, goal: str) -> ProjectContext:
        """Cria um novo contexto de projeto e o salva no disco."""
        log.info("Creating new project context.")
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        context = ProjectContext(
            project_id=self.project_id,
            project_goal=goal,
            workspace_path=self.workspace_path,
            current_state=ProjectState.PLANNING,
        )
        self.save_context(context)
        return context

    def get_context(self) -> ProjectContext:
        """Carrega o contexto do projeto do arquivo context.json."""
        if not self.context_file.exists():
            log.error("Context file not found.", path=str(self.context_file))
            raise FileNotFoundError(f"Context file not found at {self.context_file}")
        
        with open(self.context_file, 'r') as f:
            data = json.load(f)
        
        context = ProjectContext(**data)
        log.info("Project context loaded.", project_id=self.project_id, path=str(self.context_file))
        return context

    def save_context(self, context: ProjectContext):
        """Salva o objeto de contexto atual em context.json."""
        with open(self.context_file, 'w') as f:
            # Usamos o .model_dump_json() do Pydantic para serialização correta
            f.write(context.model_dump_json(indent=2))
        log.info("Project context saved.", path=str(self.context_file))
