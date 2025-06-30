"""
Configurações do MCP LLM Server.

Este módulo define todas as configurações do servidor usando Pydantic Settings
para validação de tipos e carregamento de múltiplas fontes (env vars, .env, etc).
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações gerais do servidor MCP."""
    
    name: str = Field(default="llm-server", env="MCP_SERVER_NAME")
    version: str = Field(default="1.0.0", env="MCP_SERVER_VERSION")
    description: str = Field(default="Multi-LLM MCP Server", env="MCP_SERVER_DESCRIPTION")
    author: str = Field(default="MCP LLM Team", env="MCP_SERVER_AUTHOR")
    
    debug: bool = Field(default=False, env="DEBUG")
    development_mode: bool = Field(default=False, env="DEVELOPMENT_MODE")


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações de logging."""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="plain", env="LOG_FORMAT")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    rotation: str = Field(default="daily", env="LOG_ROTATION")
    retention: int = Field(default=30, env="LOG_RETENTION")
    colors: bool = Field(default=True, env="LOG_COLORS")
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        valid_formats = {"json", "plain"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()


class SecurityConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações de segurança."""
    
    secret_key: str = Field(env="SECRET_KEY")
    token_expiry_hours: int = Field(default=24, env="TOKEN_EXPIRY_HOURS")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or len(v) < 16:
            raise ValueError("Secret key must be at least 16 characters long")
        return v


class OAuthConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações OAuth 2.0."""
    
    client_id: str = Field(env="OAUTH_CLIENT_ID")
    client_secret: str = Field(env="OAUTH_CLIENT_SECRET")
    redirect_uri: str = Field(default="http://localhost:8080/callback", env="OAUTH_REDIRECT_URI")
    scopes: List[str] = Field(default=["read", "write"], env="OAUTH_SCOPES")
    
    @field_validator("scopes", mode="before")
    @classmethod
    def parse_scopes(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v


class LLMProviderConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configuração base para provedores de LLM."""
    
    default_provider: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field(default="gpt-4-turbo-preview", env="DEFAULT_MODEL")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    timeout_seconds: int = Field(default=30, env="TIMEOUT_SECONDS")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações específicas do OpenAI."""
    
    api_key: str = Field(env="OPENAI_API_KEY")
    base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    default_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_DEFAULT_MODEL")
    max_tokens: int = Field(default=4096, env="OPENAI_MAX_TOKENS")
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v


class ClaudeConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações específicas do Claude."""
    
    api_key: str = Field(env="CLAUDE_API_KEY")
    base_url: str = Field(default="https://api.anthropic.com", env="CLAUDE_BASE_URL")
    default_model: str = Field(default="claude-3-sonnet-20240229", env="CLAUDE_DEFAULT_MODEL")
    max_tokens: int = Field(default=4096, env="CLAUDE_MAX_TOKENS")
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.startswith("sk-ant-"):
            raise ValueError("Claude API key must start with 'sk-ant-'")
        return v


class OpenRouterConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações específicas do OpenRouter."""
    
    api_key: str = Field(env="OPENROUTER_API_KEY")
    base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    default_model: str = Field(default="anthropic/claude-3-sonnet", env="OPENROUTER_DEFAULT_MODEL")
    max_tokens: int = Field(default=4096, env="OPENROUTER_MAX_TOKENS")
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.startswith("sk-or-"):
            raise ValueError("OpenRouter API key must start with 'sk-or-'")
        return v


class GeminiConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações específicas do Gemini."""
    
    api_key: str = Field(env="GEMINI_API_KEY")
    base_url: str = Field(default="https://generativelanguage.googleapis.com", env="GEMINI_BASE_URL")
    default_model: str = Field(default="gemini-1.5-pro", env="GEMINI_DEFAULT_MODEL")
    max_tokens: int = Field(default=4096, env="GEMINI_MAX_TOKENS")


class CacheConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    """Configurações de cache."""
    
    enabled: bool = Field(default=True, env="ENABLE_CACHE")
    ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")


class Settings:
    """
    Classe principal de configurações que agrega todas as configurações.
    
    Esta classe carrega configurações de múltiplas fontes:
    1. Variáveis de ambiente
    2. Arquivo .env 
    3. Valores padrão
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Inicializa as configurações.
        
        Args:
            env_file: Caminho para arquivo .env personalizado
        """
        # Determina o arquivo .env a ser usado
        if env_file is None:
            # Procura por .env no diretório atual ou no diretório pai
            current_dir = Path.cwd()
            env_candidates = [
                current_dir / ".env",
                current_dir.parent / ".env",
            ]
            
            for candidate in env_candidates:
                if candidate.exists():
                    env_file = str(candidate)
                    break
        
        # Configurações básicas do Pydantic Settings
        settings_kwargs = {
            "env_file": env_file,
            "env_file_encoding": "utf-8",
            "case_sensitive": False,
        }
        
        # Carrega todas as configurações
        self.server = ServerConfig(**settings_kwargs)
        self.logging = LoggingConfig(**settings_kwargs)
        self.security = SecurityConfig(**settings_kwargs)
        self.oauth = OAuthConfig(**settings_kwargs)
        self.llm = LLMProviderConfig(**settings_kwargs)
        
        # Configurações específicas dos provedores
        self.openai = OpenAIConfig(**settings_kwargs)
        self.claude = ClaudeConfig(**settings_kwargs)
        self.openrouter = OpenRouterConfig(**settings_kwargs)
        self.gemini = GeminiConfig(**settings_kwargs)
        
        self.cache = CacheConfig(**settings_kwargs)
    
    def validate_all(self) -> None:
        """Valida todas as configurações carregadas."""
        # Valida se pelo menos um provedor LLM está configurado
        providers_configured = []
        
        try:
            self.openai.api_key
            providers_configured.append("openai")
        except:
            pass
            
        try:
            self.claude.api_key
            providers_configured.append("claude")
        except:
            pass
            
        try:
            self.openrouter.api_key
            providers_configured.append("openrouter")
        except:
            pass
            
        try:
            self.gemini.api_key
            providers_configured.append("gemini")
        except:
            pass
        
        if not providers_configured:
            raise ValueError("At least one LLM provider must be configured")
        
        # Valida se o provedor padrão está configurado
        if self.llm.default_provider not in providers_configured:
            raise ValueError(
                f"Default provider '{self.llm.default_provider}' is not configured. "
                f"Available providers: {providers_configured}"
            )
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Retorna a configuração de um provedor específico.
        
        Args:
            provider: Nome do provedor
            
        Returns:
            Dicionário com configurações do provedor
        """
        provider_configs = {
            "openai": self.openai,
            "claude": self.claude,
            "openrouter": self.openrouter,
            "gemini": self.gemini,
        }
        
        if provider not in provider_configs:
            raise ValueError(f"Unknown provider: {provider}")
        
        return provider_configs[provider].dict()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte todas as configurações para um dicionário."""
        return {
            "server": self.server.dict(),
            "logging": self.logging.dict(),
            "security": self.security.dict(exclude={"secret_key"}),  # Não expor chave secreta
            "oauth": self.oauth.dict(exclude={"client_secret"}),  # Não expor client secret
            "llm": self.llm.dict(),
            "openai": self.openai.dict(exclude={"api_key"}),  # Não expor API keys
            "claude": self.claude.dict(exclude={"api_key"}),
            "openrouter": self.openrouter.dict(exclude={"api_key"}),
            "gemini": self.gemini.dict(exclude={"api_key"}),
            "cache": self.cache.dict(),
        }


# Instância global de configurações
settings = Settings()