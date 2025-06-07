# src/services/context_manager.py (VERSÃO CORRIGIDA)

import uuid
import json
from pathlib import Path

from src.schemas.contracts import ProjectContext, ProjectState
from src.services.observability_service import log

# Constante para o diretório base dos workspaces
WORKSPACE_DIR = Path("project_workspaces")

class ContextManager:
    """
    Gerencia o ciclo de vida do contexto do projeto (leitura, escrita, criação).
    """

    def __init__(self, project_id: uuid.UUID | None = None):
        if project_id is None:
            log.warning("Creating a new context without a goal/type. This should be set later.")
            project_id = uuid.uuid4()
            
        self.project_id = project_id
        # Define o caminho do workspace e do arquivo de contexto
        self.workspace_path = WORKSPACE_DIR / str(self.project_id)
        self.context_file = self.workspace_path / "context.json"
        
        self.context = self._load_or_create_context()
        log.info("ContextManager initialized.", project_id=str(self.project_id))
    
    def _load_or_create_context(self) -> ProjectContext:
        """
        Carrega o contexto de um arquivo JSON se ele existir,
        caso contrário, cria um novo objeto de contexto.
        """
        if self.context_file.exists():
            log.info("Loading existing project context.", path=str(self.context_file))
            with open(self.context_file, 'r') as f:
                data = json.load(f)
                return ProjectContext(**data)
        else:
            log.info("Creating new project context.")
            self._create_workspace()
            
            # ---------- A CORREÇÃO ESTÁ AQUI ----------
            # Agora estamos passando o workspace_path obrigatório ao criar o contexto.
            context = ProjectContext(
                project_id=self.project_id,
                workspace_path=self.workspace_path
            )
            # ----------------------------------------
            
            # Salva o contexto inicial para garantir que o arquivo exista para futuras operações
            self.save_context(context)
            return context

    def _create_workspace(self):
        """Cria o diretório de workspace para o projeto."""
        log.info("Creating project workspace.", path=str(self.workspace_path))
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        # Também cria a pasta de logs dentro do workspace
        (self.workspace_path / "logs").mkdir(exist_ok=True)

    def get_context(self) -> ProjectContext:
        """Retorna o objeto de contexto atual."""
        return self.context

    def save_context(self, context: ProjectContext | None = None):
        """Salva o objeto de contexto atual em um arquivo JSON."""
        if context is None:
            context = self.context
            
        # Garante que o estado seja atualizado no objeto que está sendo salvo
        self.context = context
        
        # O Pydantic não consegue serializar Path diretamente para JSON, então usamos um truque.
        context_dict = context.model_dump(mode='json')
        
        with open(self.context_file, 'w') as f:
            json.dump(context_dict, f, indent=4)
        log.info("Project context saved.", path=str(self.context_file))
