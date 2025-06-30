from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
import os

# Configurações
basedir = os.path.abspath(os.path.dirname(__file__))

# Inicialização da aplicação
app = Flask(__name__)

# Configuração do SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do Marshmallow
app.config['MARAHHOWMASS_ALLOW_ALL_ORIGINS'] = True

# Configuração do Bcrypt
app.config['BCRYPT_LOG_LEVEL'] = 2

# Inicialização das extensões
db = SQLAlchemy(app)
mma = Marshmallow(app)
bcrypt = Bcrypt(app)

# Importação de rotas
from backend.routes import bp_auth, bp_products, bp_users, bp_cart, bp_orders

# Registro das rotas
app.register_blueprint(bp_auth, url_prefix='/api/auth')
app.register_blueprint(bp_products, url_prefix='/api/products')
app.register_blueprint(bp_users, url_prefix='/api/users')
app.register_blueprint(bp_cart, url_prefix='/api/cart')
app.register_blueprint(bp_orders, url_prefix='/api/orders')

# Inicialização da conexão com o banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
