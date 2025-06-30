from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicializar SQLAlchemy e Migrate
db = SQLAlchemy()
migrate = Migrate()

# Função para inicializar o banco de dados
def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)

# Configurações do banco de dados
# Esta função deve ser chamada no app.py

def configure_database(app):
    # Configurações do SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vapes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'chave_secreta'
    app.config['UPLOAD_FOLDER'] = 'static/images'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

    # Inicializar o banco de dados
    init_db(app)

# Inicialização das tabelas
# Esta função deve ser chamada após a configuração

def create_tables(app):
    with app.app_context():
        db.create_all()
