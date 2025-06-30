from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
import os
from datetime import timedelta
import jwt

# Configuração inicial
basedir = os.path.abspath(os.path.dirname(__file__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mysecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)

# Inicialização de dependências
db = SQLAlchemy(app)
mma = Marshmallow(app)
bcrypt = Bcrypt(app)

# Importação de modelos e schemas
from backend.models import Product, User, CartItem, Order
from backend.schemas import ProductSchema, UserSchema, CartItemSchema, OrderSchema

# Configuração do JWT
import flask_jwt_extended as jwt_ext

# Roteamento para usuários
@jwt_ext_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Novo usuário criado'})

@jwt_ext_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity={'user_id': user.id, 'username': user.username})
        return jsonify({'token': access_token})
    return jsonify({'message': 'Credenciais inválidas'}, 401)

# Roteamento para produtos
@jwt_ext_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    schema = ProductSchema(many=True)
    return jsonify(schema.dump(products))

@jwt_ext_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(ProductSchema().dump(product))

# Roteamento para o carrinho
@jwt_ext_bp.route('/cart', methods=['GET', 'POST', 'PUT', 'DELETE'])
def cart_operations():
    # Lógica para o carrinho
    return jsonify({'message': 'Operação no carrinho realizada'})

# Roteamento para pedidos
@jwt_ext_bp.route('/orders', methods=['GET', 'POST'])
def orders_operations():
    # Lógica para pedidos
    return jsonify({'message': 'Operação com pedido realizada'})

# Registro dos blueprints e inicialização do app
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
