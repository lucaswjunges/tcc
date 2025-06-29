import logging
import sys
import structlog
from structlog.types import Processor
from typing import Optional

# Tentar importar settings para LOGGING_LEVEL de forma segura
try:
    from evolux_engine.utils.env_vars import settings
    LOGGING_LEVEL_FROM_SETTINGS = settings.LOGGING_LEVEL.upper()
except ImportError:
    # Fallback se settings não puder ser importado (ex: durante setup inicial ou testes isolados)
    LOGGING_LEVEL_FROM_SETTINGS = "INFO"

def setup_logging(log_level_str: str = "INFO", use_json: bool = False):
    """
    Configura o structlog com opções flexíveis.
    
    Args:
        log_level_str: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Se True, usa formato JSON para logs estruturados
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

    # Escolhe o renderer baseado na configuração
    if use_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configuração do structlog
    structlog.configure(
        processors=shared_processors + [renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_structured_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Obtém um logger estruturado com contexto.
    
    Args:
        name: Nome do logger (opcional)
        
    Returns:
        Logger estruturado configurado
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()

def add_log_context(**kwargs) -> None:
    """
    Adiciona contexto global aos logs.
    
    Args:
        **kwargs: Pares chave-valor para adicionar ao contexto
    """
    for key, value in kwargs.items():
        structlog.contextvars.bind_contextvars(**{key: value})

def clear_log_context() -> None:
    """Remove todo o contexto global dos logs."""
    structlog.contextvars.clear_contextvars()

class LoggingMixin:
    """
    Mixin para adicionar capacidades de logging estruturado a classes.
    """
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._logger = get_structured_logger(cls.__name__)
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Retorna o logger da classe com contexto."""
        if not hasattr(self, '_logger'):
            self._logger = get_structured_logger(self.__class__.__name__)
        return self._logger
    
    def log_with_context(self, level: str, message: str, **context):
        """
        Faz log com contexto adicional.
        
        Args:
            level: Nível do log (info, warning, error, etc.)
            message: Mensagem do log
            **context: Contexto adicional
        """
        log_method = getattr(self.logger, level.lower())
        log_method(message, **context)

# Configurações específicas para o Evolux Engine
def setup_evolux_logging(
    level: str = LOGGING_LEVEL_FROM_SETTINGS,
    use_json: bool = False,
    add_project_context: bool = True
):
    """
    Configura logging específico para o Evolux Engine.
    
    Args:
        level: Nível de logging
        use_json: Se deve usar formato JSON
        add_project_context: Se deve adicionar contexto do projeto
    """
    setup_logging(level, use_json)
    
    if add_project_context:
        add_log_context(
            service="evolux_engine",
            version="2.0"
        )

# Chama a configuração quando o módulo é importado
setup_evolux_logging()

# Cria e exporta uma instância do logger para ser usada por outros módulos
log = get_structured_logger("evolux_engine")

# Funções de conveniência para logging rápido
def log_info(message: str, **context):
    """Log de informação com contexto."""
    log.info(message, **context)

def log_warning(message: str, **context):
    """Log de aviso com contexto."""
    log.warning(message, **context)

def log_error(message: str, **context):
    """Log de erro com contexto."""
    log.error(message, **context)

def log_debug(message: str, **context):
    """Log de debug com contexto."""
    log.debug(message, **context)

def log_critical(message: str, **context):
    """Log crítico com contexto."""
    log.critical(message, **context)