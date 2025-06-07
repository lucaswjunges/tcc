import logging
import sys
from pathlib import Path

import structlog

# Esta é a variável 'log' que está sendo usada em outros lugares.
log: structlog.stdlib.BoundLogger = structlog.get_logger("evolux_engine")

# Esta é a função 'init_logging' que estava faltando.
def init_logging(log_dir: str):
    """
    Initializes structured logging for the entire application.
    Logs to both a file (JSON format) and the console.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "events.log"

    # Configuração padrão do logging do Python
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configuração do structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Adiciona um handler para o arquivo de log, formatando em JSON.
    handler = logging.FileHandler(log_file)
    # A formatação do FileHandler é simples, pois o structlog já fez o trabalho.
    handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Adicionamos nosso handler à raiz do logger do structlog
    # para que todos os logs criados com structlog.get_logger() vão para o arquivo.
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    # Definimos o nível de log para INFO para não poluir com DEBUG de bibliotecas.
    root_logger.setLevel(logging.INFO)

    log.info("Logging initialized.", log_file=str(log_file))

