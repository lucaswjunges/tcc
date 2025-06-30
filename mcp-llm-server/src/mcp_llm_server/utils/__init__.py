"""
Utilitários para o MCP LLM Server.

Este módulo contém utilitários compartilhados usados em todo o servidor,
incluindo logging, exceções e outras funcionalidades auxiliares.
"""

from .exceptions import (
    MCPLLMException,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    LLMProviderError,
    RateLimitError,
    ValidationError,
    NetworkError,
    TimeoutError,
)

from .logging import (
    configure_logging,
    get_logger,
    LoggerMixin,
    init_logging_from_env,
)

__all__ = [
    # Exceptions
    "MCPLLMException",
    "AuthenticationError", 
    "AuthorizationError",
    "ConfigurationError",
    "LLMProviderError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    
    # Logging
    "configure_logging",
    "get_logger",
    "LoggerMixin",
    "init_logging_from_env",
]