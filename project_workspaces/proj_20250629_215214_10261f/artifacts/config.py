import os

# Configurações gerais do projeto
PROJECT_NAME = "VapeShop"
PRODUCTION_ENV = False
DEBUG_MODE = True

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
SESSION_COOKIE_SECURE = True
CSRF_ENABLED = True

# Configurações de banco de dados
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/vapeshop'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de e-commerce
PRICING_TAX_RATE = 0.12  # Taxa de imposto (12%)
PAYMENT_PROVIDER = 'stripe'  # ou 'pagseguro', 'mercadopago', etc.

# Configurações de autenticação
AUTH_TOKEN_EXPIRATION = 14400  # 4 horas em segundos

# Configurações de e-mail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Configurações de armazenamento de arquivos
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Configurações de log
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configurações de métricas e análise
ANALYTICS_TRACKING_ID = os.environ.get('ANALYTICS_ID')
