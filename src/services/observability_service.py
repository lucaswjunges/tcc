# src/services/observability_service.py

import logging
import sys
import structlog
from pathlib import Path
from typing import Optional

def setup_logging(project_id: Optional[str] = None):
    """
    Configura o logging estruturado para o Evolux Engine.

    Logs serão enviados para o stdout e, se um project_id for fornecido,
    para um arquivo específico do projeto.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if not project_id else structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configuração do logger raiz do Python para capturar logs de bibliotecas
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear() # Limpa handlers pré-existentes

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(console_handler)

    if project_id:
        # Garante que o diretório de logs exista
        log_dir = Path(f"project_workspaces/{project_id}/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Handler para arquivo
        log_file = log_dir / "execution.log"
        file_handler = logging.FileHandler(log_file)
        root_logger.addHandler(file_handler)

    log = structlog.get_logger("evolux_engine")
    log.info("Logging service initialized.", project_id=project_id)
    return log

# Exemplo de logger global para ser usado em outros módulos
# Isso evita a necessidade de passar a instância do logger para todo lado.
# Basta importar `log` de `observability_service`.
log = structlog.get_logger("evolux_engine")

