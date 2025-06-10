# Conteúdo para: evolux_engine/utils/logging_utils.py
import logging
import sys
import structlog
from structlog.types import Processor

# Tentar importar settings para LOGGING_LEVEL de forma segura
try:
    from evolux_engine.utils.env_vars import settings
    LOGGING_LEVEL_FROM_SETTINGS = settings.LOGGING_LEVEL.upper()
except ImportError:
    # Fallback se settings não puder ser importado (ex: durante setup inicial ou testes isolados)
    LOGGING_LEVEL_FROM_SETTINGS = "INFO"
    # print("DEBUG logging_utils: Não foi possível importar 'settings', usando LOGGING_LEVEL padrão.")


def setup_logging(log_level_str: str = "INFO"):
    """
    Configura o structlog.
    """
    # Converte o nível de string para o valor numérico do logging
    numeric_log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Configuração padrão do logging do Python (structlog encaminha para aqui)
    logging.basicConfig(
        format="%(message)s",  # O formato é controlado pelo renderer do structlog
        stream=sys.stdout,
        level=numeric_log_level,
    )

    # Processadores comuns do structlog
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]

    # Configuração do structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.dev.ConsoleRenderer(), # Para desenvolvimento local
            # structlog.processors.JSONRenderer(), # Para produção, se preferir JSON
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # print(f"DEBUG logging_utils: structlog configurado com nível {log_level_str}.")


# Chama a configuração quando o módulo é importado
# Usa o nível das settings se disponível, senão o fallback
setup_logging(LOGGING_LEVEL_FROM_SETTINGS)

# Cria e exporta uma instância do logger para ser usada por outros módulos
log = structlog.get_logger() #  <-------------------- ADICIONAR ESTA LINHA

# Teste rápido (opcional, remova após confirmar que funciona)
# log.info("Logger 'log' de logging_utils.py inicializado e pronto para uso.")
