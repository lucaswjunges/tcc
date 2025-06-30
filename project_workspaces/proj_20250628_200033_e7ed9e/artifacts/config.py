import os

# Configurações gerais do projeto
PROJECT_NAME = "VapeShop"
DEBUG = False

# Configurações do banco de dados
DB_HOST = "db"
DB_PORT = 5432
DB_NAME = "vpeshop_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres_password"

# Configurações de segurança
SECRET_KEY = "chave_secreta_segura"
SESSION_COOKIE_NAME = "vpeshop_session"
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos

# Configurações de e-mail
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "suporte@vpeshop.com"
EMAIL_PASSWORD = "senha_email"
EMAIL_USE_TLS = True

# Configurações do Docker
DOCKER_IMAGE_NAME = "vpeshop_app"
DOCKER_TAG = "latest"

# Configurações do site
SITE_TITLE = "VapeShop - Loja Virtual de Acessórios para Vapes"
SITE_DESCRIPTION = "A melhor experiência de compra de vapes e pods funcional"

# Configurações de armazenamento
UPLOAD_FOLDER = "app/static/uploads"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Configurações de cache
CACHE_TYPE = "simple"
CACHE_DEFAULT_TIMEOUT = 300

# Configurações de logging
LOG_LEVEL = "INFO"
LOG_FILE = "app.log"

# Configurações de rate limiting
REQUEST_RATE_LIMIT = 100  # Limite de 100 requisições por minuto
