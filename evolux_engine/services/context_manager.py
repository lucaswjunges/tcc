# src/services/context_manager.py

import json
from pathlib import Path
from datetime import datetime
import hashlib
from ..models import ProjectContext
from .observability_service import log

class ContextManager:
    """Gerencia o ciclo de vida dos contextos de projeto (criar, carregar, salvar)."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        log.info("ContextManager initialized.", base_dir=str(self.base_dir))

    def create_new_project_context(self, goal: str) -> ProjectContext:
        """
        Cria um novo contexto para um novo projeto, com um ID único.
        """
        log.info("Creating a new project context.", goal=goal)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        goal_hash = hashlib.sha1(goal.encode()).hexdigest()[:6]
        project_id = f"proj_{timestamp}_{goal_hash}"
        
        # Criar o contexto com os campos obrigatórios
        workspace_path = self.base_dir / project_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        context = ProjectContext(
            project_id=project_id,
            project_name=f"Projeto {goal[:50]}...",
            project_goal=goal,
            workspace_path=workspace_path
        )

        # Criar os diretórios fisicamente
        (workspace_path / "artifacts").mkdir(parents=True, exist_ok=True)
        (workspace_path / "logs").mkdir(parents=True, exist_ok=True)
        
        # Salva o contexto inicial para persistência
        self.save_project_context(context)
        log.info(f"New project '{project_id}' created successfully.")
        return context

    def load_project_context(self, project_id: str) -> ProjectContext:
        """
        Carrega um contexto de projeto existente a partir de seu arquivo JSON.
        """
        log.info(f"Loading project context for '{project_id}'.")
        context_path = self.base_dir / project_id / "context.json"
        
        if not context_path.exists():
            log.error("Project context file not found.", path=str(context_path))
            raise FileNotFoundError(f"No project found with ID '{project_id}'.")
            
        try:
            data = json.loads(context_path.read_text(encoding='utf-8'))
            context = ProjectContext(**data)
            log.info("Project context loaded successfully.")
            return context
        except Exception as e:
            log.error("Failed to load or parse project context.", error=str(e), exc_info=True)
            raise

    def save_project_context(self, context: ProjectContext):
        """
        Salva o estado atual do contexto do projeto em seu arquivo JSON.
        """
        project_path = self.base_dir / context.project_id
        project_path.mkdir(parents=True, exist_ok=True)
        context_path = project_path / "context.json"
        
        try:
            context_path.write_text(context.model_dump_json(indent=2), encoding='utf-8')
            log.info(f"Project context for '{context.project_id}' saved.", path=str(context_path))
        except Exception as e:
            log.error("Failed to save project context.", error=str(e), exc_info=True)
            raise
