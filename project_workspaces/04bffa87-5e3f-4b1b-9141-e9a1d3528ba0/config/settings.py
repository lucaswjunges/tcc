# config/settings.py

import os

# Configurações da aplicação
APP_NAME = "Tarô Divinação"
APP_VERSION = "1.0.0"
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://tarot_user:tarot_pass@localhost/tarot_db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações do servidor
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

# Configurações de segurança
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')

# Configurações de email
EMAIL_BACKEND = 'smtp'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'tarot@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'tarot_password')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Tarô Divinação <tarot@example.com>')

# Configurações de pagamento
PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER', 'stripe')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_123')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_123')
PRICE_ID = os.environ.get('PRICE_ID', 'price_123')

# Configurações de armazenamento
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Configurações de cache
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 3600

# Configurações de logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = 'logs/tarot.log'

# Configurações de métricas
METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'False').lower() in ('true', '1', 'yes')
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

# Configurações de internacionalização
LANGUAGES = {
    'pt': 'Português',
    'en': 'English'
}
BABEL_DEFAULT_LOCALE = 'pt'
BABEL_SUPPORTED_LOCALES = ['pt', 'en']

# Configurações de SEO
SITE_DESCRIPTION = os.environ.get('SITE_DESCRIPTION', 'Consultoria de Tarô online com profunda análise e orientação espiritual')
SITE_KEYWORDS = os.environ.get('SITE_KEYWORDS', 'tarô, adivinhação, cartas, espiritualidade, tarólogo, consultoria')
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
TWITTER_ACCOUNT = os.environ.get('TWITTER_ACCOUNT', '@tarotdivinacao')
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', 'UA-00000000-1')