from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    cart = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    # Relacionamentos
    cart_items = db.relationship('Cart', backref='product', lazy=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')

    # Funções auxiliares
    def get_order_items(self):
        return Cart.query.filter_by(user_id=self.user_id).all()

    # Rotação de autenticação
    @jwt.user_identity
    def get_user_identity(current_user):
        return current_user.id

    # Inicialização do aplicativo
    def init_app(app):
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key')
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
        db.init_app(app)
        migrate.init_app(app, db)
        jwt.init_app(app)

    # Rotas de autenticação
    @app.route('/login', methods=['POST'])
    def login():
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        # Verificação de usuário e senha
        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == password:  # Na prática, usar hash de senha
            access_token = create_access_token(identity=user.id)
            return jsonify(access_token=access_token), 200
        return jsonify(error='Credenciais inválidas'), 401

    @app.route('/register', methods=['POST'])
    def register():
        username = request.json.get('username', None)
        email = request.json.get('email', None)
        password = request.json.get('password', None)
        if not username or not email or not password:
            return jsonify(error='Todos os campos são obrigatórios'), 400
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return jsonify(error='Usuário já existe'), 400
        new_user = User(username=username, email=email, password_hash=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message='Usuário criado com sucesso'), 201

    # Rotas de produtos
    @app.route('/products', methods=['GET'])
    def get_products():
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200

    @app.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict()), 200

    # Similar para POST, PUT, DELETE
    @app.route('/products', methods=['POST'])
    def create_product():
        data = request.json
        new_product = Product(**data)
        db.session.add(new_product)
        db.session.commit()
        return jsonify(message='Produto criado'), 201

    # Rotas de usuários
    @app.route('/users', methods=['GET'])
    def get_users():
        users = User.query.all()
        return jsonify([u.to_dict() for u in users]), 200

    @app.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200

    # Similar para outras operações
    @app.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        user = User.query.get_or_404(user_id)
        data = request.json
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return jsonify(message='Usuário atualizado'), 200

    # Rotas de carrinho
    @app.route('/cart/<int:user_id>', methods=['GET'])
    def get_cart(user_id):
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        return jsonify([item.to_dict() for item in cart_items]), 200

    @app.route('/cart/<int:cart_id>', methods=['POST'])
    def add_to_cart(cart_id):
        # Lógica para adicionar item ao carrinho
        return jsonify(message='Item adicionado ao carrinho'), 201

    # Similar para remover, atualizar
    # Rotas de pedidos
    @app.route('/orders', methods=['POST'])
    def create_order():
        # Criar pedido com base no carrinho do usuário
        return jsonify(message='Pedido criado'), 201

    @app.route('/orders/<int:order_id>', methods=['GET'])
    def get_order(order_id):
        order = Order.query.get_or_404(order_id)
        return jsonify(order.to_dict()), 200

def create_app():
    app = Flask(__name__)
    app.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
