"""
Configurações simplificadas do MCP LLM Server.

Esta versão usa carregamento manual de variáveis de ambiente para evitar
problemas com Pydantic Settings.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Caminho para o arquivo .env
ENV_FILE = str(Path(__file__).parent.parent.parent.parent / '.env')

# Carrega o arquivo .env explicitamente
load_dotenv(ENV_FILE)


@dataclass
class ServerConfig:
    """Configurações do servidor."""
    name: str = "llm-server"
    version: str = "1.0.0"
    description: str = "Multi-LLM MCP Server"
    author: str = "MCP LLM Team"
    debug: bool = False
    development_mode: bool = False
    
    def __post_init__(self):
        self.name = os.getenv("MCP_SERVER_NAME", self.name)
        self.version = os.getenv("MCP_SERVER_VERSION", self.version)
        self.description = os.getenv("MCP_SERVER_DESCRIPTION", self.description)
        self.author = os.getenv("MCP_SERVER_AUTHOR", self.author)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"


@dataclass
class LoggingConfig:
    """Configurações de logging."""
    level: str = "INFO"
    format: str = "plain"
    file: Optional[str] = None
    rotation: str = "daily"
    retention: int = 30
    colors: bool = True
    
    def __post_init__(self):
        self.level = os.getenv("LOG_LEVEL", self.level).upper()
        self.format = os.getenv("LOG_FORMAT", self.format).lower()
        self.file = os.getenv("LOG_FILE", self.file)
        self.rotation = os.getenv("LOG_ROTATION", self.rotation)
        self.retention = int(os.getenv("LOG_RETENTION", str(self.retention)))
        self.colors = os.getenv("LOG_COLORS", "true").lower() == "true"


@dataclass
class SecurityConfig:
    """Configurações de segurança."""
    secret_key: str = ""
    token_expiry_hours: int = 24
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    def __post_init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "")
        if not self.secret_key:
            raise ValueError("SECRET_KEY is required")
        if len(self.secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters long")
        
        self.token_expiry_hours = int(os.getenv("TOKEN_EXPIRY_HOURS", str(self.token_expiry_hours)))
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", str(self.rate_limit_requests)))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", str(self.rate_limit_window)))


@dataclass
class OAuthConfig:
    """Configurações OAuth."""
    client_id: str = "mcp-llm-client-2024"
    client_secret: str = "super-secret-client-key-for-oauth-2024"
    redirect_uri: str = "http://localhost:8080/callback"
    scopes: List[str] = field(default_factory=lambda: ["read", "write"])
    
    def __post_init__(self):
        self.client_id = os.getenv("OAUTH_CLIENT_ID", self.client_id)
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET", self.client_secret)
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", self.redirect_uri)
        
        scopes_env = os.getenv("OAUTH_SCOPES")
        if scopes_env:
            self.scopes = [s.strip() for s in scopes_env.split(",")]


@dataclass
class LLMProviderConfig:
    """Configurações gerais de provedores LLM."""
    default_provider: str = "openai"
    default_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 30
    
    def __post_init__(self):
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", self.default_provider)
        self.default_model = os.getenv("DEFAULT_MODEL", self.default_model)
        self.max_tokens = int(os.getenv("MAX_TOKENS", str(self.max_tokens)))
        self.temperature = float(os.getenv("TEMPERATURE", str(self.temperature)))
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", str(self.timeout_seconds)))
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")


@dataclass
class OpenAIConfig:
    """Configurações do OpenAI."""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    
    def __post_init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.api_key.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        
        self.base_url = os.getenv("OPENAI_BASE_URL", self.base_url)
        self.default_model = os.getenv("OPENAI_DEFAULT_MODEL", self.default_model)
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", str(self.max_tokens)))


@dataclass
class ClaudeConfig:
    """Configurações do Claude."""
    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    default_model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    
    def __post_init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY", "")
        if self.api_key and not self.api_key.startswith("sk-ant-"):
            raise ValueError("Claude API key must start with 'sk-ant-'")
        
        self.base_url = os.getenv("CLAUDE_BASE_URL", self.base_url)
        self.default_model = os.getenv("CLAUDE_DEFAULT_MODEL", self.default_model)
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", str(self.max_tokens)))


@dataclass
class OpenRouterConfig:
    """Configurações do OpenRouter."""
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3-sonnet"
    max_tokens: int = 4096
    
    def __post_init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        if not self.api_key.startswith("sk-or-"):
            raise ValueError("OpenRouter API key must start with 'sk-or-'")
        
        self.base_url = os.getenv("OPENROUTER_BASE_URL", self.base_url)
        self.default_model = os.getenv("OPENROUTER_DEFAULT_MODEL", self.default_model)
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", str(self.max_tokens)))


@dataclass
class GeminiConfig:
    """Configurações do Gemini."""
    api_key: str = ""
    base_url: str = "https://generativelanguage.googleapis.com"
    default_model: str = "gemini-1.5-pro"
    max_tokens: int = 4096
    
    def __post_init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        self.base_url = os.getenv("GEMINI_BASE_URL", self.base_url)
        self.default_model = os.getenv("GEMINI_DEFAULT_MODEL", self.default_model)
        self.max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", str(self.max_tokens)))


@dataclass
class CacheConfig:
    """Configurações de cache."""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 1000
    
    def __post_init__(self):
        self.enabled = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", str(self.ttl_seconds)))
        self.max_size = int(os.getenv("CACHE_MAX_SIZE", str(self.max_size)))


class SimpleSettings:
    """
    Classe principal de configurações simplificada.
    
    Esta versão carrega configurações manualmente das variáveis de ambiente.
    """
    
    def __init__(self):
        """Inicializa as configurações."""
        # Carrega todas as configurações
        self.server = ServerConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.oauth = OAuthConfig()
        self.llm = LLMProviderConfig()
        self.cache = CacheConfig()
        
        # Configurações específicas dos provedores
        # Só cria as configurações se as API keys estiverem disponíveis
        self.openai = None
        self.claude = None
        self.openrouter = None
        self.gemini = None
        
        # Carrega configurações opcionais dos provedores
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.openai = OpenAIConfig()
            except ValueError:
                pass  # API key inválida, ignora
        
        if os.getenv("CLAUDE_API_KEY"):
            try:
                self.claude = ClaudeConfig()
            except ValueError:
                pass  # API key inválida, ignora
        
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                self.openrouter = OpenRouterConfig()
            except ValueError:
                pass  # API key inválida, ignora
        
        if os.getenv("GEMINI_API_KEY"):
            try:
                self.gemini = GeminiConfig()
            except ValueError:
                pass  # API key inválida, ignora
    
    def validate_all(self) -> None:
        """Valida todas as configurações carregadas."""
        # Valida se pelo menos um provedor LLM está configurado
        providers_configured = []
        
        if self.openai:
            providers_configured.append("openai")
            
        if self.claude:
            providers_configured.append("claude")
            
        if self.openrouter:
            providers_configured.append("openrouter")
            
        if self.gemini:
            providers_configured.append("gemini")
        
        if not providers_configured:
            raise ValueError("At least one LLM provider must be configured")
        
        # Valida se o provedor padrão está configurado
        if self.llm.default_provider not in providers_configured:
            # Usa o primeiro provedor configurado como padrão
            self.llm.default_provider = providers_configured[0]
    
    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Retorna a configuração de um provedor específico.
        
        Args:
            provider: Nome do provedor
            
        Returns:
            Dicionário com configurações do provedor ou None se não configurado
        """
        provider_configs = {
            "openai": self.openai,
            "claude": self.claude,
            "openrouter": self.openrouter,
            "gemini": self.gemini,
        }
        
        if provider not in provider_configs:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = provider_configs[provider]
        if config is None:
            return None
        
        return {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "default_model": config.default_model,
            "max_tokens": config.max_tokens,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte todas as configurações para um dicionário."""
        result = {
            "server": self.server.__dict__,
            "logging": self.logging.__dict__,
            "security": {k: v for k, v in self.security.__dict__.items() if k != "secret_key"},
            "oauth": {k: v for k, v in self.oauth.__dict__.items() if k != "client_secret"},
            "llm": self.llm.__dict__,
            "cache": self.cache.__dict__,
        }
        
        # Adiciona configurações de provedores (sem API keys)
        for provider_name in ["openai", "claude", "openrouter", "gemini"]:
            provider_config = getattr(self, provider_name)
            if provider_config:
                result[provider_name] = {
                    k: v for k, v in provider_config.__dict__.items() 
                    if k != "api_key"
                }
            else:
                result[provider_name] = {"configured": False}
        
        return result


# Função para criar configurações de forma lazy
def get_settings() -> SimpleSettings:
    """Retorna instância de configurações de forma lazy."""
    return SimpleSettings()


# Instância global de configurações - será criada quando necessário
_settings = None


def settings() -> SimpleSettings:
    """Retorna a instância global de configurações."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings