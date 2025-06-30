"""
Exceções customizadas para o MCP LLM Server.

Este módulo define todas as exceções específicas do domínio usadas
pelo servidor MCP LLM.
"""

from typing import Optional, Dict, Any


class MCPLLMException(Exception):
    """Exceção base para todas as exceções do MCP LLM Server."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(MCPLLMException):
    """Exceção para erros de autenticação."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class AuthorizationError(MCPLLMException):
    """Exceção para erros de autorização."""
    
    def __init__(self, message: str = "Authorization failed", **kwargs):
        super().__init__(message, error_code="AUTHZ_ERROR", **kwargs)


class ConfigurationError(MCPLLMException):
    """Exceção para erros de configuração."""
    
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class LLMProviderError(MCPLLMException):
    """Exceção para erros de provedor de LLM."""
    
    def __init__(self, provider: str, message: str, **kwargs):
        self.provider = provider
        super().__init__(f"LLM Provider '{provider}': {message}", error_code="LLM_PROVIDER_ERROR", **kwargs)


class RateLimitError(MCPLLMException):
    """Exceção para erros de rate limiting."""
    
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, error_code="RATE_LIMIT_ERROR", **kwargs)


class ValidationError(MCPLLMException):
    """Exceção para erros de validação."""
    
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class NetworkError(MCPLLMException):
    """Exceção para erros de rede."""
    
    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class TimeoutError(MCPLLMException):
    """Exceção para erros de timeout."""
    
    def __init__(self, message: str = "Operation timed out", **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)