"""
Sistema de logging estruturado para o MCP LLM Server.

Este módulo configura o sistema de logging usando structlog para fornecer
logs estruturados e facilitar debugging e monitoramento.
"""

import os
import sys
import logging
from typing import Any, Dict, Optional
from pathlib import Path

import structlog
from rich.logging import RichHandler
from rich.console import Console


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
    enable_colors: bool = True
) -> None:
    """
    Configura o sistema de logging estruturado.
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formato do log ("json", "plain")
        log_file: Caminho para o arquivo de log (opcional)
        enable_colors: Se deve usar cores no console
    """
    # Converte string de nível para enum
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configura processadores do structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=enable_colors))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configura handlers
    handlers = []
    
    # Handler para console
    if enable_colors and format_type != "json":
        console_handler = RichHandler(
            console=Console(stderr=True),
            show_time=False,
            show_path=False,
            markup=True
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
    
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configura logging básico
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Obtém um logger estruturado para o módulo especificado.
    
    Args:
        name: Nome do módulo/componente
        
    Returns:
        Logger estruturado configurado
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin que adiciona capacidades de logging a qualquer classe.
    
    Uso:
        class MyClass(LoggerMixin):
            def some_method(self):
                self.logger.info("Doing something", param="value")
    """
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Retorna um logger configurado para a classe atual."""
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__name__
            module_name = self.__class__.__module__
            logger_name = f"{module_name}.{class_name}"
            self._logger = get_logger(logger_name)
        return self._logger
    
    def log_method_call(self, method_name: str, **kwargs) -> None:
        """
        Log uma chamada de método com parâmetros.
        
        Args:
            method_name: Nome do método sendo chamado
            **kwargs: Parâmetros do método
        """
        self.logger.debug(
            "Method called",
            method=method_name,
            class_name=self.__class__.__name__,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log um erro com contexto adicional.
        
        Args:
            error: Exceção que ocorreu
            context: Contexto adicional para o erro
        """
        self.logger.error(
            "Error occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            class_name=self.__class__.__name__,
            context=context or {}
        )


# Inicializa logging com configurações padrão do ambiente
def init_logging_from_env() -> None:
    """Inicializa logging usando variáveis de ambiente."""
    level = os.getenv("LOG_LEVEL", "INFO")
    format_type = os.getenv("LOG_FORMAT", "plain")
    log_file = os.getenv("LOG_FILE")
    enable_colors = os.getenv("LOG_COLORS", "true").lower() == "true"
    
    configure_logging(
        level=level,
        format_type=format_type,
        log_file=log_file,
        enable_colors=enable_colors
    )