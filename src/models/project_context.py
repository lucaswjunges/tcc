import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path # Usar pathlib para manipulação de caminhos mais robusta

from loguru import logger
from pydantic import BaseModel, Field, validator # Importar diretamente de Pydantic

# Reutilizar os Schemas definidos em contracts.py
from evolux_engine.schemas.contracts import (
    ProjectStatus,
    Task,
    IterationLog,
    ArtifactState,
    ProjectMetrics,
    EngineConfig,
    # Não é necessário importar 'ProjectContext' daqui pois estamos definindo
    # a classe que implementa a lógica para esse schema.
)


class ProjectContext(BaseModel):
    """
    Representa o estado completo e a configuração de um projeto Evolux.
    Esta classe encapsula os dados definidos no schema ProjectContext de contracts.py
    e adiciona lógica para persistência e manipulação de caminhos.

    A persistência é feita em um arquivo 'context.json' no diretório raiz do projeto.
    """

    project_id: str
    project_name: Optional[str] = None
    project_goal: str
    project_type: Optional[str] = None
    final_artifacts_description: Optional[str] = None
    
    status: ProjectStatus = Field(default=ProjectStatus.INITIALIZING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    task_queue: List[Task] = Field(default_factory=list)
    completed_tasks: List[Task] = Field(default_factory=list)
    
    iteration_history: List[IterationLog] = Field(default_factory=list)
    
    artifacts_state: Dict[str, ArtifactState] = Field(default_factory=dict)
    
    metrics: ProjectMetrics = Field(default_factory=ProjectMetrics)
    engine_config: EngineConfig = Field(default_factory=EngineConfig)
    
    current_error_feedback_for_planner: Optional[str] = None

    # --- Campos Não Persistidos (gerenciados em tempo de execução) ---
    # O workspace_path é crucial e deve ser definido ao carregar ou criar o contexto.
    # Usaremos `exclude=True` para Pydantic não tentar serializá-lo/desserializá-lo do JSON.
    workspace_path: Path = Field(default=None, exclude=True) # type: ignore [assignment]

    class Config:
        # Para permitir que Path seja usado como tipo de campo
        arbitrary_types_allowed = True
        # Garante que os validadores sejam chamados na atribuição
        validate_assignment = True


    @validator("last_updated", pre=True, always=True)
    def set_last_updated(cls, v, values):
        # Sempre atualiza last_updated. Se 'created_at' já existe, não sobrescreve.
        # Este validador é mais para garantir que `last_updated` seja sempre o tempo atual
        # quando o modelo é validado (ex: ao carregar ou salvar).
        return datetime.utcnow()

    @validator("workspace_path", always=True)
    def check_workspace_path(cls, v, values):
        if v is None:
            # Isso pode acontecer se o contexto for criado sem o ContextManager
            # Uma solução é o ContextManager sempre definir isso.
            project_id = values.get("project_id")
            # logger.warning(f"ProjectContext (ID: {project_id}): workspace_path não foi definido na inicialização. Funcionalidades de arquivo podem falhar.")
            # Não levantar erro aqui pois ele pode ser definido logo após a criação
        elif not isinstance(v, Path):
            raise ValueError("workspace_path deve ser um objeto Path.")
        return v

    @property
    def context_file_path(self) -> Path:
        if not self.workspace_path:
            raise ValueError("workspace_path não está definido. Não é possível determinar o caminho do context.json.")
        return self.workspace_path / "context.json"

    async def save_context(self) -> None:
        """Salva o estado atual do ProjectContext no arquivo context.json."""
        if not self.workspace_path:
            logger.error(f"ProjectContext (ID: {self.project_id}): workspace_path não definido. Não é possível salvar o contexto.")
            raise ValueError("workspace_path não definido, não é possível salvar.")

        self.last_updated = datetime.utcnow() # Garante que está atualizado antes de salvar
        
        # Cria o diretório do workspace se não existir
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Excluir o campo 'workspace_path' do dicionário antes de serializar
            # Usar Pydantic model_dump para serialização correta de datetimes, enums, etc.
            # `exclude_none=True` pode ser útil para manter o JSON mais limpo
            context_data = self.model_dump(exclude={'workspace_path'}, mode='json')

            with open(self.context_file_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
            logger.info(f"ProjectContext (ID: {self.project_id}) salvo em {self.context_file_path}")
        except Exception as e:
            logger.opt(exception=True).error(
                f"ProjectContext (ID: {self.project_id}): Falha ao salvar contexto: {e}"
            )
            # Considerar uma estratégia de backup ou retry aqui? Por enquanto, apenas loga.

    @classmethod
    def load_from_file(cls, project_id: str, base_project_dir: Path) -> Optional["ProjectContext"]:
        """
        Carrega o ProjectContext de um arquivo context.json.
        Retorna None se o arquivo não for encontrado.
        """
        workspace_p = Path(base_project_dir) / project_id
        context_file = workspace_p / "context.json"

        if not context_file.exists():
            logger.warning(f"ProjectContext (ID: {project_id}): Arquivo de contexto {context_file} não encontrado.")
            return None
        
        try:
            with open(context_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Criar instância e depois definir o workspace_path
            instance = cls(**data) 
            instance.workspace_path = workspace_p # Definir após carregar os dados do JSON
            logger.info(f"ProjectContext (ID: {project_id}) carregado de {context_file}")
            return instance
        except json.JSONDecodeError as e:
            logger.opt(exception=True).error(f"ProjectContext (ID: {project_id}): Erro ao decodificar JSON de {context_file}: {e}")
            # Poderia tentar carregar de um backup se existir
        except Exception as e: # Ex: Pydantic ValidationError
            logger.opt(exception=True).error(f"ProjectContext (ID: {project_id}): Erro ao carregar ou validar contexto de {context_file}: {e}")
        return None
    
    # --- Métodos Utilitários para Caminhos ---

    def get_project_path(self, relative_path: Optional[str] = None) -> Path:
        """Retorna o caminho absoluto para um arquivo/diretório dentro do workspace do projeto."""
        if not self.workspace_path:
            raise ValueError("workspace_path não definido.")
        if relative_path:
            # Prevenir travessia de diretório para cima do workspace_path
            # Normalizar o caminho e garantir que ele não saia do workspace
            # os.path.abspath resolve .., mas Path.resolve() é mais moderno.
            # No entanto, joinpath e depois verificar se está dentro do workspace é mais seguro.
            abs_path = (self.workspace_path / relative_path).resolve()
            if self.workspace_path not in abs_path.parents and abs_path != self.workspace_path:
                 logger.error(f"ProjectContext (ID: {self.project_id}): Tentativa de acesso a caminho fora do workspace: {relative_path} resolvido para {abs_path}")
                 raisePermissionError(f"Acesso negado: Tentativa de acessar fora do workspace: {relative_path}")
            return abs_path
        return self.workspace_path

    def get_artifact_path(self, artifact_relative_path: str) -> Path:
        """Retorna o caminho absoluto para um artefato dentro da pasta 'artifacts' do projeto."""
        return self.get_project_path(Path("artifacts") / artifact_relative_path)

    def get_log_path(self, log_file_name: str) -> Path:
        """Retorna o caminho absoluto para um arquivo de log dentro da pasta 'logs' do projeto."""
        log_dir = self.get_project_path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / log_file_name

    # --- Métodos para Gerenciar o Estado Interno ---

    def update_artifact_state(self, artifact_path_relative: str, state: ArtifactState):
        """Adiciona ou atualiza o estado de um artefato."""
        self.artifacts_state[artifact_path_relative] = state
        logger.debug(f"ProjectContext (ID: {self.project_id}): Estado do artefato '{artifact_path_relative}' atualizado/adicionado.")
        # O salvamento do contexto deve ser explícito (chamada a save_context)

    def remove_artifact_state(self, artifact_path_relative: str):
        """Remove o estado de um artefato."""
        if artifact_path_relative in self.artifacts_state:
            del self.artifacts_state[artifact_path_relative]
            logger.debug(f"ProjectContext (ID: {self.project_id}): Estado do artefato '{artifact_path_relative}' removido.")

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Encontra uma tarefa na task_queue ou completed_tasks pelo ID."""
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        logger.warning(f"ProjectContext (ID: {self.project_id}): Tarefa com ID '{task_id}' não encontrada.")
        return None

    def update_task(self, updated_task: Task):
        """Atualiza uma tarefa existente na task_queue ou completed_tasks."""
        for i, task in enumerate(self.task_queue):
            if task.task_id == updated_task.task_id:
                self.task_queue[i] = updated_task
                return
        for i, task in enumerate(self.completed_tasks):
            if task.task_id == updated_task.task_id:
                self.completed_tasks[i] = updated_task
                return
        logger.warning(f"ProjectContext (ID: {self.project_id}): Tarefa com ID '{updated_task.task_id}' não encontrada para atualização.")

    def add_iteration_log(self, log_entry: IterationLog):
        """Adiciona uma entrada ao histórico de iterações."""
        self.iteration_history.append(log_entry)
        logger.debug(f"ProjectContext (ID: {self.project_id}): Log de iteração adicionado para tarefa {log_entry.task_id}, iteração {log_entry.iteration_id}.")

    def get_artifacts_structure_summary(self, max_depth: int = 3, max_files_per_dir: int = 5) -> str:
        """
        Gera um resumo em formato de árvore da estrutura de arquivos na pasta 'artifacts'.
        Esta versão lê diretamente do sistema de arquivos e não apenas do `artifacts_state`.
        """
        artifacts_dir = self.get_project_path("artifacts")
        if not artifacts_dir.exists() or not artifacts_dir.is_dir():
            return "Diretório de artefatos não encontrado ou não é um diretório."

        summary_lines = [f"Estrutura de Artefatos em '{artifacts_dir.name}':"] # Usar nome relativo
        
        def build_tree_str_from_fs(current_path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                summary_lines.append(f"{prefix}└── ... (profundidade máxima atingida)")
                return

            try:
                # Listar apenas arquivos e diretórios, ignorar outros como links simbólicos por simplicidade
                # e ordenar para consistência.
                entries = sorted([entry for entry in current_path.iterdir() if entry.is_file() or entry.is_dir()], 
                                 key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                summary_lines.append(f"{prefix}└── [acesso negado]")
                return

            for i, entry in enumerate(entries):
                if i >= max_files_per_dir and entry.is_file(): # Limitar arquivos por diretório, não diretórios
                    if i == max_files_per_dir: # Adicionar apenas uma vez
                         summary_lines.append(f"{prefix}    └── ... (mais arquivos)")
                    continue # Pular o resto dos arquivos

                connector = "├── " if i < len(entries) - 1 or (i == max_files_per_dir and entry.is_dir()) else "└── "
                summary_lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
                
                if entry.is_dir():
                    new_prefix = prefix + ("│   " if i < len(entries) - 1 or (i == max_files_per_dir and entry.is_dir()) else "    ")
                    build_tree_str_from_fs(entry, new_prefix, depth + 1)

        build_tree_str_from_fs(artifacts_dir)
        if len(summary_lines) == 1: # Apenas o cabeçalho
            return "Nenhum artefato gerado ainda na pasta 'artifacts'."
        return "\n".join(summary_lines)
