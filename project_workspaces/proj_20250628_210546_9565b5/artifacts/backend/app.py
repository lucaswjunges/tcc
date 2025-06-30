from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from backend.models import db, User, Product, Cart, Order

app = Flask(__name__)
api = Api(app)

# Initialize database
with app.app_context():
    db.create_all()

# Authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return jsonify({'token': 'authentication_token_here'})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Product routes
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'description': p.description} for p in products])

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description})

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        price=data['price'],
        description=data.get('description', '')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully', 'product_id': new_product.id}), 201

# Cart routes
@app.route('/cart', methods=['GET'])
def get_cart():
    cart_items = Cart.query.all()
    return jsonify([{'id': item.id, 'product_id': item.product_id, 'quantity': item.quantity} for item in cart_items])

@app.route('/cart/<int:cart_id>', methods=['PUT'])
def update_cart(cart_id):
    data = request.get_json()
    cart_item = Cart.query.get_or_404(cart_id)
    cart_item.quantity = data['quantity']
    db.session.commit()
    return jsonify({'message': 'Cart updated successfully'})

@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data['product_id']
    quantity = data['quantity']
    cart_item = Cart.query.filter_by(product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        new_cart_item = Cart(product_id=product_id, quantity=quantity)
        db.session.add(new_cart_item)
    db.session.commit()
    return jsonify({'message': 'Item added to cart successfully'})

# Order routes
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([{'id': o.id, 'user_id': o.user_id, 'order_date': o.order_date} for o in orders])

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'id': order.id, 'user_id': order.user_id, 'order_date': order.order_date})

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(user_id=data['user_id'])
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'message': 'Order created successfully', 'order_id': new_order.id}), 201

if __name__ == '__main__':
    app.run(debug=True)