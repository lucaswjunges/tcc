import os

# Configurações principais do projeto
PROJECT_NAME = "VapeShop"
DEBUG = False

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
SESSION_COOKIE_SECURE = True

# Configurações de banco de dados
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'vpeshop_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Configurações do servidor
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
SERVER_PORT = os.environ.get('SERVER_PORT', '8000')

# Configurações de e-commerce
PAYMENT_GATEWAY = os.environ.get('PAYMENT_GATEWAY', 'stripe')
SHIPPING_COST = 10.00

# Configurações de e-mail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '587')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True

# Configurações de logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configurações de desenvolvimento (ativadas apenas em ambiente de desenvolvimento)
debug_enabled = os.environ.get('DEBUG_ENABLED', 'False').lower() in ['true', '1', 'yes']