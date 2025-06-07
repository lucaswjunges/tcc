# src/services/config_manager.py (VERSÃO FINAL CORRIGIDA)

from pathlib import Path
import yaml
from typing import Dict, Any

from src.schemas.contracts import SystemConfig
from src.services.observability_service import log

class ConfigManager:
    _config: SystemConfig = None
    _config_path = Path('config.yaml')
    _local_config_path = Path('config.local.yaml')

    @classmethod
    def _deep_merge(cls, source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mescla recursivamente dicionários. As chaves de `source` sobrescrevem as de `destination`.
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
                destination[key] = cls._deep_merge(value, destination[key])
            else:
                destination[key] = value
        return destination

    @classmethod
    def get_config(cls) -> SystemConfig:
        if cls._config is not None:
            return cls._config

        try:
            # Carrega a configuração padrão
            with open(cls._config_path, 'r') as f:
                default_config_data = yaml.safe_load(f) or {}

            # Carrega a configuração local, se existir
            local_config_data = {}
            if cls._local_config_path.exists():
                with open(cls._local_config_path, 'r') as f:
                    local_config_data = yaml.safe_load(f) or {}
            
            # **AQUI ESTÁ A CORREÇÃO**: Usando a mesclagem profunda
            merged_config_data = cls._deep_merge(local_config_data, default_config_data)

            # Valida a configuração mesclada com o Pydantic
            cls._config = SystemConfig(**merged_config_data)
            log.info("Configuration loaded and validated successfully.")
            return cls._config
        except FileNotFoundError:
            log.critical(f"Configuration file not found at {cls._config_path}")
            raise
        except Exception as e:
            log.critical("Failed to load or validate configuration.", error=str(e), exc_info=True)
            raise e

