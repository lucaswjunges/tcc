import os

# Configurações gerais do projeto
PROJECT_NAME = "VapeStore"
DEBUG_MODE = os.environ.get("DEBUG", "False").lower() in ["true", "1"]

# Configurações de segurança
SECRET_KEY = os.environ.get("SECRET_KEY", "mysecretkey")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "True").lower() in ["true", "1"]
CSRF_ENABLED = os.environ.get("CSRF_ENABLED", "True").lower() in ["true", "1"]

# Configurações de banco de dados
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "vapestore_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

# Configurações de e-commerce
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "stripe")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_test_123")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_123")

# Configurações de e-mail
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.environ.get("EMAIL_PORT", "587")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ["true", "1"]
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "noreply@vapestore.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# Configurações de upload de imagens
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Configurações de logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# Configurações do servidor
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = os.environ.get("SERVER_PORT", "5000")

# Configurações de cache
CACHE_TYPE = os.environ.get("CACHE_TYPE", "simple")
CACHE_REDIS_HOST = os.environ.get("CACHE_REDIS_HOST", "localhost")
CACHE_REDIS_PORT = os.environ.get("CACHE_REDIS_PORT", "6379")

# Configurações de rate limiting
RATE_LIMIT_MAX = os.environ.get("RATE_LIMIT_MAX", "100")
RATE_LIMIT_WINDOW = os.environ.get("RATE_LIMIT_WINDOW", "minute")

# Configurações de segurança adicional
SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "mysecuresalt")
PERMANENT_SESSIONS = os.environ.get("PERMANENT_SESSIONS", "True").lower() in ["true", "1"]