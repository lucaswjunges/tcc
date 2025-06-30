import os

# Configurações do site
SITE_NAME = "VapeShop"
SITE_DESCRIPTION = "Loja especializada em vapes e atomizadores de óleo canábico."
SITE_ADMIN = "admin@vapeshop.com"

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = 'sqlite:///shop.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'você_deve_definir_uma_chave_secreta_aqui')

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Configurações de email
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# Configurações do Flask
DEBUG = False
TESTING = False