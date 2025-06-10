import os
import json
from datetime import datetime
from evolux_engine.utils.logging_utils import log # Usar o logger global configurado
from typing import Optional # <--- ADICIONE ESTA LINHA


class ContextManager:
    """
    Gerencia o contexto de um projeto específico, incluindo logs e estado.
    """
    def __init__(self, project_id: str, project_dir: str):
        """
        Inicializa o ContextManager.

        Args:
            project_id: O ID único do projeto.
            project_dir: O caminho completo para o diretório do projeto.
        """
        self.project_id: str = project_id
        self.project_dir: str = project_dir
        self.log_file_name: str = "project_audit.jsonl" # Log específico do projeto
        self.log_file_path: str = os.path.join(self.project_dir, self.log_file_name)

        if not os.path.exists(self.project_dir):
            try:
                os.makedirs(self.project_dir, exist_ok=True)
                log.info(f"Diretório do projeto criado: {self.project_dir}", project_id=self.project_id)
                self.add_log_entry("system", f"Diretório do projeto {self.project_id} criado em {self.project_dir}.")
            except OSError as e:
                log.error(f"Falha ao criar diretório do projeto {self.project_dir}: {e}", project_id=self.project_id)
                raise  # Re-lança a exceção para o chamador lidar

        log.debug(f"ContextManager inicializado para projeto {self.project_id}", path=self.project_dir)

    def add_log_entry(self, source: str, message: str, data: Optional[dict] = None):
        """
        Adiciona uma entrada de log ao arquivo de log do projeto.

        Args:
            source: A origem da entrada de log (ex: "system", "llm", "agent").
            message: A mensagem de log.
            data: Dados adicionais a serem incluídos no log (opcional).
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_id": self.project_id,
            "source": source,
            "message": message,
        }
        if data:
            log_entry.update(data)

        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError as e:
            log.error(f"Falha ao escrever no arquivo de log do projeto {self.log_file_path}: {e}",
                      project_id=self.project_id)

    # Você pode adicionar mais métodos aqui para:
    # - Salvar/carregar o estado do projeto (ex: ProjectContext)
    # - Gerenciar arquivos dentro do project_dir
    # - Interagir com o versionamento (git)
    # - etc.

    def get_project_file_path(self, relative_path: str) -> str:
        """Retorna o caminho absoluto para um arquivo dentro do diretório do projeto."""
        return os.path.join(self.project_dir, relative_path)

    def save_file(self, relative_path: str, content: str):
        """Salva conteúdo em um arquivo dentro do diretório do projeto."""
        full_path = self.get_project_file_path(relative_path)
        try:
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                log.info(f"Diretório pai criado: {parent_dir}", project_id=self.project_id)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log.info(f"Arquivo salvo: {full_path}", project_id=self.project_id)
            self.add_log_entry("system", f"Arquivo salvo: {relative_path}")
        except IOError as e:
            log.error(f"Falha ao salvar arquivo {full_path}: {e}", project_id=self.project_id)
            self.add_log_entry("system_error", f"Falha ao salvar arquivo {relative_path}: {e}")
            raise

    def create_directory(self, relative_path: str):
        """Cria um diretório dentro do diretório do projeto."""
        full_path = self.get_project_file_path(relative_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            log.info(f"Diretório criado: {full_path}", project_id=self.project_id)
            self.add_log_entry("system", f"Diretório criado: {relative_path}")
        except OSError as e:
            log.error(f"Falha ao criar diretório {full_path}: {e}", project_id=self.project_id)
            self.add_log_entry("system_error", f"Falha ao criar diretório {relative_path}: {e}")
            raise
