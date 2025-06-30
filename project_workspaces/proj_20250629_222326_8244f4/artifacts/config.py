import os

# Configurações do Projeto
PROJECT_NAME = "VapeShop"
VERSION = "1.0.0"
DESCRIPTION = "Loja de venda de vapes e pods funcional, estiloso e completo usando Python"

# Configurações do Ambiente
ENVIRONMENT = "development"  # development, staging, production
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configurações do Banco de Dados
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "name": os.getenv("DB_NAME", "vpes_shop"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

# Configurações do Servidor
SERVER = {
    "host": os.getenv("SERVER_HOST", "0.0.0.0"),
    "port": os.getenv("SERVER_PORT", "8000")
}

# Configurações de Segurança
SECURITY = {
    "secret_key": os.getenv("SECRET_KEY", "mysecretkey") + "vpes_shop",
    "algorithm": "HS256",
    "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "150")),
    "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
}

# Configurações de Email
EMAIL = {
    "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
    "port": os.getenv("EMAIL_PORT", "587"),
    "username": os.getenv("EMAIL_USERNAME", "noreply@vpes_shop.com"),
    "password": os.getenv("EMAIL_PASSWORD", "")
}

# Configurações do Armazenamento
STORAGE = {
    "type": os.getenv("STORAGE_TYPE", "local"),  # local, s3, etc.
    "path": os.getenv("STORAGE_PATH", "./uploads")
}

# Configurações de Logging
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "./logs/vpes_shop.log"
}

# Configurações de Pagamentos
PAYMENT = {
    "provider": os.getenv("PAYMENT_PROVIDER", "pagseguro"),
    "sandbox": os.getenv("PAYMENT_SANDBOX", "True"),
    "api_key": os.getenv("PAYMENT_API_KEY", "")
}

# Configurações de Cache
cache_config = {
    "enabled": os.getenv("CACHE_ENABLED", "False"),
    "timeout": int(os.getenv("CACHE_TIMEOUT", "3600"))
}

# Configurações de Rate Limiting
RATE_LIMITING = {
    "enabled": os.getenv("RATE_LIMITING_ENABLED", "False"),
    "requests_per_minute": int(os.getenv("REQUESTS_PER_MINUTE", "100"))
}

# Configurações de Desenvolvimento
DEVELOPMENT = {
    "auto_reload": DEBUG,
    "debug": DEBUG,
    "open_editor_on_error": True if DEBUG else False
}