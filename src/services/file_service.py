import os
from pathlib import Path
from src.services.observability_service import log

class FileService:
    """
    Um serviço dedicado a lidar com todas as operações de arquivo
    dentro do espaço de trabalho do projeto.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        log.info(f"FileService initialized for workspace: {self.workspace_path}")

    def _get_full_path(self, relative_path: str) -> Path:
        """
        Converte um caminho relativo em um caminho absoluto seguro dentro do workspace.
        Impede o acesso a arquivos fora do diretório do projeto (travessia de diretório).
        """
        full_path = self.workspace_path.joinpath(relative_path).resolve()
        
        # Verificação de segurança: garantir que o caminho resolvido ainda está dentro do workspace
        if self.workspace_path.resolve() not in full_path.parents and full_path != self.workspace_path.resolve():
            log.error("Security alert: Attempted to access path outside workspace.",
                      requested_path=relative_path, resolved_path=str(full_path))
            raise PermissionError("Access denied: Cannot access files outside the project workspace.")
        
        return full_path

    def write_file(self, file_path: str, content: str):
        """
        Escreve o conteúdo em um arquivo dentro do workspace.
        Cria diretórios intermediários se eles não existirem.
        """
        path = self._get_full_path(file_path)
        log.info(f"Writing file: {path}")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            log.info(f"Successfully wrote to {file_path}")
        except Exception as e:
            log.error(f"Failed to write file {file_path}", error=str(e), exc_info=True)
            raise

    def read_file(self, file_path: str) -> str:
        """Lê o conteúdo de um arquivo dentro do workspace."""
        path = self._get_full_path(file_path)
        log.info(f"Reading file: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            log.warn(f"File not found: {file_path}")
            return None # Retorna None se o arquivo não existir
        except Exception as e:
            log.error(f"Failed to read file {file_path}", error=str(e), exc_info=True)
            raise

    def list_files(self, sub_dir: str = ".") -> list[str]:
        """Lista todos os arquivos recursivamente em um subdiretório do workspace."""
        dir_path = self._get_full_path(sub_dir)
        log.info(f"Listing files in: {dir_path}")
        if not dir_path.is_dir():
            return []
        
        all_files = []
        for root, _, files in os.walk(dir_path):
            for name in files:
                # Converte o caminho completo de volta para um caminho relativo ao workspace
                full_file_path = Path(root) / name
                relative_path = full_file_path.relative_to(self.workspace_path)
                all_files.append(str(relative_path))
        return all_files
