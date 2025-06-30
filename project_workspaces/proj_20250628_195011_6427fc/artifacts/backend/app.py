from flask import Flask, jsonify, request
import bcrypt
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'supersecretkey'

# Mock database
products = [
    {'id': 1, 'name': 'Smartphone XYZ', 'price': 999.99, 'description': 'Smartphone de última geração'},
    {'id': 2, 'name': 'Notebook Pro', 'price': 1999.99, 'description': 'Notebook ultraregular com processador i9'},
    {'id': 3, 'name': 'Smartwatch', 'price': 299.99, 'description': 'Smartwatch com GPS e monitoramento de saúde'}
]

users = [
    {'id': 1, 'username': 'testuser', 'password': bcrypt.hashpw(b'password', bcrypt.gensalt()).decode('utf-8'), 'email': 'test@example.com'}
]

orders = []

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# Rota de autenticação
@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    user = next((u for u in users if u['username'] == auth.username), None)
    if not user:
        return jsonify({'message': 'User not found'}), 401
    if bcrypt.checkpw(auth.password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({'user': auth.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, 
                          app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})
    return jsonify({'message': 'Could not verify'}), 401

# Rota para produtos
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify({'products': products})

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({'message': 'Product not found'}), 404

# Rota para usuários
@app.route('/users', methods=['GET'])
@token_required
def get_users():
    return jsonify({'users': users})

@app.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({'message': 'User not found'}), 404

# Rota para carrinho
@app.route('/carts', methods=['GET'])
@token_required
def get_carts():
    # Simulação: cada usuário tem um carrinho vazio
    return jsonify({'carts': [{'user_id': user['id'], 'items': []} for user in users]}), 201

@app.route('/carts/<int:user_id>', methods=['POST'])
@token_required
def add_to_cart(user_id):
    # Verifica se o usuário existe
    user_cart = next((c for c in [{'user_id': u['id']} for u in users] if c['user_id'] == user_id), None)
    if not user_cart:
        return jsonify({'message': 'User not found'}), 404
    # Simples adição ao carrinho
    return jsonify({'message': 'Item added to cart'}), 201

# Rota para pedidos
@app.route('/orders', methods=['GET'])
@token_required
def get_orders():
    return jsonify({'orders': orders}), 200

@app.route('/orders', methods=['POST'])
@token_required
def create_order():
    # Simulação de criação de pedido
    new_order = {'id': len(orders) + 1, 'user_id': request.json.get('user_id'), 'status': 'pending', 'items': []}
    orders.append(new_order)
    return jsonify({'order': new_order}), 201

if __name__ == '__main__':
    app.run(debug=True)