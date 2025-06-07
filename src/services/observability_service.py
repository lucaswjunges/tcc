# src/services/observability_service.py (VERSÃO FINAL COM CLASSE)

import sys
import structlog
from pathlib import Path
import uuid

class ObservabilityService:
    @classmethod
    def initialize(cls, log_dir: str, project_id: uuid.UUID):
        """
        Configura o structlog para output no console e em um arquivo 
        específico do projeto.
        """
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / "events.log"

        # Configuração dos processadores para o log
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Cria um logger raiz que delega para handlers
        # Adiciona handlers para o console e para o arquivo
        # Esta é uma maneira mais robusta de lidar com múltiplos outputs
        root_logger = structlog.get_logger("evolux_engine").logger
        
        # Limpa handlers existentes para evitar duplicação
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Handler para o console
        console_handler = logging.StreamHandler(sys.stdout)
        root_logger.addHandler(console_handler)

        # Handler para o arquivo de log
        file_handler = logging.FileHandler(log_file)
        root_logger.addHandler(file_handler)
        
        # Define o nível do logger raiz
        root_logger.setLevel(logging.INFO)

        log.info(f"Logging service initialized.", project_id=str(project_id))

# Pega o logger. Ele será reconfigurado pelo `initialize` quando o app iniciar.
# log = structlog.get_logger("evolux_engine")

# -- CORREÇÃO DE ÚLTIMA HORA --
# Percebi que a configuração acima precisa do módulo `logging`.
# Vamos simplificar para evitar mais um erro de importação e manter o foco.

import logging # Importa o módulo standard de logging

class ObservabilityService:
    @classmethod
    def initialize(cls, log_dir: str, project_id: uuid.UUID):
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / "events.log"

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configurar o logger raiz do Python para usar os handlers
        handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Para evitar output duplicado no console pelo logger raiz
        # e pelo structlog, vamos focar no renderer do structlog
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer()
        )
        
        handler.setFormatter(formatter)
        # console_handler.setFormatter(formatter) # JSON no console pode ser feio, vamos omitir por agora

        root_logger = logging.getLogger()
        root_logger.handlers.clear()  # Limpa handlers antigos
        root_logger.addHandler(handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
        
        log.info("Logging service initialized.", project_id=str(project_id))


# log agora é uma instância global que será configurada por `initialize`
log = structlog.get_logger("evolux_engine")
