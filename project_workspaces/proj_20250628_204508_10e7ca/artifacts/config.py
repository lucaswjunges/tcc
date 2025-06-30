import os

# Configurações do projeto
PROJETO_NOME = "Meu Portfólio"
PROJETO_VERSION = "1.0.0"

# Configurações do banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "portfolio_db")
DB_USER = os.getenv("DB_USER", "portfolio_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "senha_secreta")

# Configurações do servidor
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
PORT = os.getenv("PORT", "3000")

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_aqui")

# Configurações de ambiente
ENV = os.getenv("FLASK_ENV", "production")

# Configurações de e-mail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.getenv("EMAIL_PORT", "587")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")