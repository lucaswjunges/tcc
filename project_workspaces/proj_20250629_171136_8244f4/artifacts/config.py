import os

# Configurações do projeto

# Configurações gerais
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Configurações do banco de dados
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'vapes_shop')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Configurações do servidor
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = os.getenv('SERVER_PORT', '8000')

# Configurações do e-commerce
STORE_NAME = os.getenv('STORE_NAME', 'Vapes Shop')
STORE_DESCRIPTION = os.getenv('STORE_DESCRIPTION', 'Loja de vapes e pods premium')

# Configurações de segurança
SECRET_KEY = os.getenv('SECRET_KEY', 'chave_secreta_segura')

# Configurações de email
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.getenv('EMAIL_PORT', '587')
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# Configurações de pagamento
PAYMENT_GATEWAY = os.getenv('PAYMENT_GATEWAY', 'stripe')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')

# Configurações de log
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Configurações de cache
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))

# Configurações de tempo de execução
EXECUTION_TIME = int(os.getenv('EXECUTION_TIME', '30'))

# Configurações de upload de arquivos
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'png, jpg, jpeg, gif, pdf').split(', ')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '5242880'))  # 5MB in bytes

# Configurações de segurança para desenvolvimento
if DEBUG:
    # Em ambientes de desenvolvimento, aceitar origens não seguras para depuração
    SQLALCHEMY_WARN_DEPRECATED = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = 'lax'
else:
    # Em produção, usar configurações mais seguras
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Configurações da API
API_VERSION = os.getenv('API_VERSION', 'v1')
API_DOC_URL = f"/api/{API_VERSION}/docs"

# Configurações do OpenAI (se necessário para funcionalidades como chat assistente)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')