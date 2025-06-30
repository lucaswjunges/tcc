import os

# Configurações do Flask
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False')
FLASK_APP = 'wsgi:app'

# Configurações do Banco de Dados
SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de Segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configurações de Email (se aplicável)
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

# Configurações Gerais
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos

# Logging
LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'False').lower() in ['true', '1', 'yes']
LOG_FILENAME = 'app.log'

# Configurações de Desenvolvimento
if os.environ.get('FLASK_ENV') == 'development':
    DEBUG_TB_ENABLED = True
    WTF_CSRF_ENABLED = False