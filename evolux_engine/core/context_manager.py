import os
import json
from pathlib import Path
from typing import Optional
from loguru import logger # <--- MUDANÇA AQUI

class ContextManager:
    def __init__(self, project_id: str, base_project_dir: str = "project_workspaces"): # Mudança no nome do parâmetro
        self.project_id = project_id
        # Certifique-se de que base_project_dir seja interpretado corretamente
        # Se for um caminho relativo, pode ser relativo ao CWD ou à raiz do projeto,
        # dependendo de como é passado de settings.py
        # Se settings.PROJECT_BASE_DIR for um caminho absoluto, isso é mais seguro.
        self.base_path = Path(base_project_dir) 
        self.project_path = self.base_path / self.project_id
        self._ensure_project_dir_exists()
        logger.info(
            "ContextManager inicializado para projeto.", 
            path=str(self.project_path), 
            project_id=self.project_id
        )

    def _ensure_project_dir_exists(self):
        try:
            self.project_path.mkdir(parents=True, exist_ok=True)
            logger.info(
                "Diretório do projeto criado/verificado.", 
                path=str(self.project_path), 
                project_id=self.project_id
            )
        except Exception as e:
            logger.opt(exception=True).error(
                "Erro ao criar diretório do projeto.", 
                path=str(self.project_path), 
                project_id=self.project_id,
                # error_details=str(e) # opt(exception=True) já inclui isso
            )
            raise

    def get_path(self, relative_path: str) -> Path:
        """Retorna o caminho absoluto para um arquivo/diretório dentro do projeto."""
        return self.project_path / relative_path

    def ensure_dir_exists(self, relative_dir_path: str):
        """Garante que um subdiretório dentro do projeto exista."""
        dir_path = self.get_path(relative_dir_path)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Subdiretório '{dir_path}' verificado/criado.", project_id=self.project_id)
        except Exception as e:
            logger.opt(exception=True).error(
                f"Erro ao criar subdiretório '{dir_path}'.", 
                project_id=self.project_id
            )
            raise

    def save_file(self, relative_filepath: str, content: str) -> Path:
        filepath = self.get_path(relative_filepath)
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True) # Garante que o diretório pai exista
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Arquivo salvo.", path=str(filepath), project_id=self.project_id)
            return filepath
        except Exception as e:
            logger.opt(exception=True).error(
                "Erro ao salvar arquivo.", 
                path=str(filepath), 
                project_id=self.project_id
            )
            raise

    def load_file(self, relative_filepath: str) -> str:
        filepath = self.get_path(relative_filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info("Arquivo carregado.", path=str(filepath), project_id=self.project_id)
            return content
        except FileNotFoundError:
            logger.warning("Arquivo não encontrado para leitura.", path=str(filepath), project_id=self.project_id)
            # Considere se deve levantar um erro aqui em vez de retornar string vazia
            # raise FileNotFoundError(f"Arquivo não encontrado: {filepath}") 
            return "" 
        except Exception as e:
            logger.opt(exception=True).error(
                "Erro ao carregar arquivo.", 
                path=str(filepath), 
                project_id=self.project_id
            )
            raise

    def save_json(self, relative_filepath: str, data: dict):
        filepath = self.get_path(relative_filepath)
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("JSON salvo.", path=str(filepath), project_id=self.project_id)
        except Exception as e:
            logger.opt(exception=True).error(
                "Erro ao salvar JSON.", 
                path=str(filepath), 
                project_id=self.project_id
            )
            raise

    def load_json(self, relative_filepath: str) -> Optional[dict]: # Retorno pode ser None se não encontrado
        filepath = self.get_path(relative_filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("JSON carregado.", path=str(filepath), project_id=self.project_id)
            return data
        except FileNotFoundError:
            logger.warning("Arquivo JSON não encontrado.", path=str(filepath), project_id=self.project_id)
            return None # Melhor retornar None para indicar ausência
        except json.JSONDecodeError:
            logger.opt(exception=True).error(
                "Erro ao decodificar JSON.", 
                path=str(filepath), 
                project_id=self.project_id
            )
            return None # Ou levantar um erro específico
        except Exception as e:
            logger.opt(exception=True).error(
                "Erro ao carregar JSON.", 
                path=str(filepath), 
                project_id=self.project_id
            )
            raise # Re-levanta a exceção se for algo inesperado
