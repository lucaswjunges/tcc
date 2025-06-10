import logging
import sys
import structlog
from structlog.types import FilteringBoundLogger

# Configuração global do logger, acessível como 'log' após setup_logging ser chamado.
log: FilteringBoundLogger = structlog.get_logger()

def setup_logging(level: str = "INFO"):
    """
    Configura o structlog para logging.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Nível de log inválido: {level}")

    # Configuração padrão para logging (para bibliotecas que usam logging nativo)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Configuração do Structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(), # Para output colorido e legível no console
            # Para output JSON, descomente a linha abaixo e comente ConsoleRenderer:
            # structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # Atualiza a instância global 'log'
    global log
    log = structlog.get_logger("evolux_engine") # Pode dar um nome ao logger principal
    log.info(f"Logging configurado para o nível: {level}")

# Exemplo de como usar o logger em outros módulos:
# from evolux_engine.utils.logging_utils import log
# log.info("Esta é uma mensagem de info", dado_extra="valor")
# log.error("Esta é uma mensagem de erro", erro_detalhe="falha X")
