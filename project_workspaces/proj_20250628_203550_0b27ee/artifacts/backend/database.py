from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Inicializar o banco de dados
# Configurações do SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

# Configuração do banco de dados def config_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    
# Definir modelos
# Exemplo de modelo de usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Outros modelos conforme necessário

# Função de inicialização do banco de dados
def init_db(app):
    config_db(app)
    #db.create_all()  # Comentar para evitar múltiplas criações

# Configuração para migrações
# migrações serão gerenciadas via Flask-Migrate
