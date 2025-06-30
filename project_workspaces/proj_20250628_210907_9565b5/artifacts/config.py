import os

# Configuração do Flask
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True')
FLASK_APP = os.environ.get('FLASK_APP', 'app.py')

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost/blog_db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de segurança
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'my_secret_key'
)
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos

# Configurações do ambiente
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = bool(os.environ.get('FLASK_DEBUG')) if ENV == 'development' else False
TESTING = ENV == 'testing'

# Configurações para uploads de arquivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Configurações de e-mail
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

# Outras configurações
BLOG_TITLE = 'Meu Blog'
BLOG_DESCRIPTION = 'Um blog simples construído com Flask'
