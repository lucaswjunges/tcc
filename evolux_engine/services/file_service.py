# src/services/file_service.py

import os
import hashlib
from pathlib import Path
from .observability_service import log

class FileService:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, relative_path: str) -> Path:
        full_path = self.workspace_path.joinpath(relative_path).resolve()
        if self.workspace_path.resolve() not in full_path.parents and full_path != self.workspace_path.resolve():
            raise PermissionError("Access denied: Cannot access files outside the project workspace.")
        return full_path

    def write_file(self, file_path: str, content: str):
        path = self._get_full_path(file_path)
        log.info(f"Writing file: {path}")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            log.info(f"Successfully wrote to {file_path}")
        except Exception as e:
            log.error(f"Failed to write file {file_path}", error=str(e), exc_info=True)
            raise

    def read_file(self, file_path: str) -> str | None:
        path = self._get_full_path(file_path)
        if not path.is_file():
            log.warn(f"File not found: {file_path}")
            return None
        log.info(f"Reading file: {path}")
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            log.error(f"Failed to read file {file_path}", error=str(e), exc_info=True)
            raise

    def list_files(self, sub_dir: str = ".") -> list[str]:
        dir_path = self._get_full_path(sub_dir)
        if not dir_path.is_dir():
            return []
        
        all_files = []
        for root, _, files in os.walk(dir_path):
            for name in files:
                full_file_path = Path(root) / name
                relative_path = full_file_path.relative_to(self.workspace_path)
                all_files.append(str(relative_path))
        return all_files

    def save_file(self, file_path: str, content: str):
        """Alias for write_file for compatibility"""
        return self.write_file(file_path, content)

    def get_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file content"""
        path = self._get_full_path(file_path)
        if not path.is_file():
            return ""
        try:
            with open(path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            log.error(f"Failed to hash file {file_path}", error=str(e), exc_info=True)
            return ""

    def delete_file(self, file_path: str):
        """Delete a file"""
        path = self._get_full_path(file_path)
        if not path.is_file():
            log.warn(f"File not found for deletion: {file_path}")
            return
        try:
            path.unlink()
            log.info(f"Successfully deleted file: {file_path}")
        except Exception as e:
            log.error(f"Failed to delete file {file_path}", error=str(e), exc_info=True)
            raise
