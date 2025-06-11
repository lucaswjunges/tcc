# evolux_engine/context_manager.py
import os
import json
from pathlib import Path
from evolux_engine.utils.logging_utils import log

class ContextManager:
    def __init__(self, project_id: str, base_path: str = "project_workspaces"):
        self.project_id = project_id
        self.base_path = Path(base_path)
        self.project_path = self.base_path / self.project_id
        self._ensure_project_dir_exists()
        log.info("ContextManager inicializado para projeto.", path=str(self.project_path), project_id=self.project_id)

    def _ensure_project_dir_exists(self):
        try:
            self.project_path.mkdir(parents=True, exist_ok=True)
            log.info("Diretório do projeto criado/verificado.", path=str(self.project_path), project_id=self.project_id)
        except Exception as e:
            log.error("Erro ao criar diretório do projeto.", path=str(self.project_path), error=str(e))
            raise

    def get_path(self, relative_path: str) -> Path:
        return self.project_path / relative_path

    def ensure_dir_exists(self, relative_dir_path: str):
        """Garante que um subdiretório dentro do projeto exista."""
        dir_path = self.get_path(relative_dir_path)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            log.debug(f"Diretório {dir_path} criado/verificado.")
        except Exception as e:
            log.error(f"Erro ao criar diretório {dir_path}.", error=str(e))
            raise

    def save_file(self, relative_filepath: str, content: str) -> Path:
        filepath = self.get_path(relative_filepath)
        try:
            # Garante que o diretório pai exista
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            log.info("Arquivo salvo.", path=str(filepath), project_id=self.project_id)
            return filepath
        except Exception as e:
            log.error("Erro ao salvar arquivo.", path=str(filepath), error=str(e))
            raise

    def load_file(self, relative_filepath: str) -> str:
        filepath = self.get_path(relative_filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            log.info("Arquivo carregado.", path=str(filepath), project_id=self.project_id)
            return content
        except FileNotFoundError:
            log.warning("Arquivo não encontrado para leitura.", path=str(filepath), project_id=self.project_id)
            return "" # Ou levantar erro
        except Exception as e:
            log.error("Erro ao carregar arquivo.", path=str(filepath), error=str(e))
            raise

    def save_json(self, relative_filepath: str, data: dict):
        filepath = self.get_path(relative_filepath)
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info("JSON salvo.", path=str(filepath), project_id=self.project_id)
        except Exception as e:
            log.error("Erro ao salvar JSON.", path=str(filepath), error=str(e))
            raise

    def load_json(self, relative_filepath: str) -> dict:
        filepath = self.get_path(relative_filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info("JSON carregado.", path=str(filepath), project_id=self.project_id)
            return data
        except FileNotFoundError:
            log.warning("Arquivo JSON não encontrado.", path=str(filepath), project_id=self.project_id)
            return {} # Ou levantar erro
        except json.JSONDecodeError:
            log.error("Erro ao decodificar JSON.", path=str(filepath), project_id=self.project_id)
            return {} # Ou levantar erro
        except Exception as e:
            log.error("Erro ao carregar JSON.", path=str(filepath), error=str(e))
            raise
