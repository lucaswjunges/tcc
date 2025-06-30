from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
import os

# Configuração do aplicativo
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização de extensões
db = SQLAlchemy(app)
mma = Marshmallow(app)
bcrypt = Bcrypt(app)

# Modelo de Produto
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    image = db.Column(db.String(200))

    def __init__(self, name, description, price, image):
        self.name = name
        self.description = description
        self.price = price
        self.image = image

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(60))
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.is_admin = is_admin

# Modelo de Carrinho
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)

# Modelo de Pedido
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

# Inicialização do esquema para serialização
with mma.init_app(app):
    class ProductSchema(mma.SQLAlchemyAutoSchema):
        class Meta:
            model = Product

    class UserSchema(mma.SQLAlchemyAutoSchema):
        class Meta:
            model = User

    class CartSchema(mma.SQLAlchemyAutoSchema):
        class Meta:
            model = Cart

    class OrderSchema(mma.SQLAlchemyAutoSchema):
        class Meta:
            model = Order

    class OrderItemSchema(mma.SQLAlchemyAutoSchema):
        class Meta:
            model = OrderItem

# Rota para inicializar o banco de dados
@app.route('/init-db')
def init_db():
    db.create_all()
    return jsonify({'message': 'Banco de dados inicializado'})

# Rota para registrar um novo usuário
@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or any(k not in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Dados insuficientes'}), 400

    if User.query.filter(User.email == data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 409

    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuário registrado com sucesso'}), 201

# Rota para login do usuário
@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or any(k not in data for k in ['email', 'password']):
        return jsonify({'error': 'Dados insuficientes'}), 400

    user = User.query.filter(User.email == data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Em uma implementação real, você usaria JWT ou sessões seguras
        return jsonify({'message': 'Login realizado com sucesso'}), 200
    return jsonify({'error': 'Credenciais inválidas'}), 401

# Rota para criar um novo produto
@app.route('/api/products', methods=['POST'])
def create_product():
    if not request.json or any(k not in request.json for k in ['name', 'description', 'price', 'image']):
        return jsonify({'error': 'Dados insuficientes'}), 400

    new_product = Product(
        name=request.json['name'],
        description=request.json['description'],
        price=request.json['price'],
        image=request.json['image']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Produto criado com sucesso'}), 201

# Rota para obter todos os produtos
@app.route('/api/products')
def get_products():
    products = Product.query.all()
    schema = ProductSchema(many=True)
    result = schema.dump(products)
    return jsonify({'products': result}), 200

# Rota para obter um produto específico
@app.route('/api/products/<int:id>')
def get_product(id):
    product = Product.query.get_or_404(id)
    schema = ProductSchema()
    result = schema.dump(product)
    return jsonify({'product': result}), 200

# Rota para adicionar item ao carrinho
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    if not data or any(k not in data for k in ['user_id', 'product_id', 'quantity']):
        return jsonify({'error': 'Dados insuficientes'}), 400

    # Verificar se o item já existe no carrinho
    existing_item = Cart.query.filter(
        Cart.user_id == data['user_id'],
        Cart.product_id == data['product_id']
    ).first()

    if existing_item:
        existing_item.quantity += data['quantity']
    else:
        new_item = Cart(
            user_id=data['user_id'],
            product_id=data['product_id'],
            quantity=data['quantity']
        )
        db.session.add(new_item)

    db.session.commit()
    return jsonify({'message': 'Item adicionado ao carrinho'}), 201

# Rota para criar pedido
@app.route('/api/orders', methods=['POST'])
def create_order():
    if not request.json or 'user_id' not in request.json:
        return jsonify({'error': 'Dados insuficientes'}), 400

    user_id = request.json['user_id']
    cart_items = Cart.query.filter(Cart.user_id == user_id).all()

    if not cart_items:
        return jsonify({'error': 'Carrinho vazio'}), 400

    # Calcular total
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    # Criar pedido
    new_order = Order(user_id=user_id, total_amount=total_amount)
    db.session.add(new_order)
    db.session.commit()

    # Adicionar itens ao pedido
    for item in cart_items:
        new_order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(new_order_item)
        # Remover item do carrinho
        db.session.delete(item)

    db.session.commit()
    return jsonify({'message': 'Pedido criado com sucesso', 'order_id': new_order.id}), 201

# Rota para obter histórico de pedidos do usuário
@app.route('/api/orders/<int:user_id>')
def get_order_history(user_id):
    orders = Order.query.filter(Order.user_id == user_id).all()
    if not orders:
        return jsonify({'message': 'Nenhum pedido encontrado'}), 200

    order_schema = OrderSchema(many=True)
    result = order_schema.dump(orders)
    return jsonify({'orders': result}), 200

# Executar o aplicativo
if __name__ == '__main__':
    app.run(debug=True)
