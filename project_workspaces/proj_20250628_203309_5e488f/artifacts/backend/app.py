from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, jwt_refresh_token, get_jwt_identity
from datetime import timedelta

# Initialize the application
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
db = SQLAlchemy(app)
mma = Marshmallow(app)
jwt = JWTManager(app)

# Import models
from backend.models import User, Product, CartItem, Order

db.create_all()

# API Endpoints
# Authentication
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or any(key not in data for key in ['username', 'password', 'email', 'role']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=data['role']
    )
    new_user.save()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity={'id': user.id, 'role': user.role})
    return jsonify({'access_token': access_token}), 200

# Products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'description': p.description} for p in products]), 200

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description}), 200

@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({'message': 'Admin privilege required'}), 403
    
    data = request.get_json()
    if not data or any(key not in data for key in ['name', 'price', 'description']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_product = Product(
        name=data['name'],
        price=data['price'],
        description=data['description']
    )
    new_product.save()
    return jsonify({'message': 'Product created successfully'}), 201

# Users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users]), 200

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role}), 200

# Cart
@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    current_user = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=current_user['id']).all()
    return jsonify([{'product_id': item.product_id, 'quantity': item.quantity} for item in cart_items]), 200

@app.route('/cart/<int:product_id>', methods=['POST'])
@jwt_required()
def add_to_cart(product_id):
    current_user = get_jwt_identity()
    data = request.get_json()
    quantity = data.get('quantity', 1)
    
    cart_item = CartItem.query.filter_by(user_id=current_user['id'], product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user['id'], product_id=product_id, quantity=quantity)
    
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({'message': 'Product added to cart'}), 201

# Orders
@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    current_user = get_jwt_identity()
    orders = Order.query.filter_by(user_id=current_user['id']).all()
    return jsonify([{'id': o.id, 'total_amount': o.total_amount, 'status': o.status, 'order_date': o.order_date} for o in orders]), 200

@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    current_user = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=current_user['id']).all()
    if not cart_items:
        return jsonify({'message': 'Cart is empty'}), 400
    
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    new_order = Order(user_id=current_user['id'], total_amount=total_amount, status='Pending')
    db.session.add(new_order)
    db.session.commit()
    
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Order created successfully'}), 201

# Run the application
if __name__ == '__main__':
    app.run(debug=True)