from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from models import User

# Create blueprint
auth_bp = Blueprint('auth', __name__)
api = Api(auth_bp)

# Configuration
SECRET_KEY = 'your_secret_key'

# Registration endpoint
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or any(k not in data for k in ['username', 'password', 'email']):
        return jsonify({'message': 'Missing fields'}), 400
    
    if User.query.filter_by(username=data['username']).first() or 
       User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    new_user = User(
        username=data['username'],
        password=generate_password_hash(data['password'], method='sha256'),
        email=data['email']
    )
    new_user.save()
    return jsonify({'message': 'User created'}), 201

# Login endpoint
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or any(k not in data for k in ['username', 'password']):
        return jsonify({'message': 'Missing fields'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Token expiration time (30 minutes)
    token_expiration = datetime.timedelta(minutes=30)
    access_token = jwt.encode(
        {
            'sub': user.id,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + token_expiration
        },
        SECRET_KEY
    )
    
    return jsonify({
        'access_token': access_token.decode('UTF-8'),
        'expires_in': int(token_expiration.total_seconds())
    }), 200

# Protected route example
@auth_bp.route('/protected', methods=['GET'])
def protected_route():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing token'}), 401
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['sub']
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    
    # You would validate the user here (check if user exists and is active)
    return jsonify({'message': 'Protected route accessed', 'user_id': user_id}), 200

# Add routes to API
api.add_resource(register, '/register')
api.add_resource(login, '/login')
api.add_resource(protected_route, '/protected')
