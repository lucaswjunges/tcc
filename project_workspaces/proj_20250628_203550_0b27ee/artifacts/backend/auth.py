from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from backend.models import User

auth_bp = Blueprint('auth', __name__)
auth = HTTPBasicAuth()

@auth_bp.route('/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=request.json['username']).first()
    if not user or not check_password_hash(user.password, request.json['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    token = jwt.encode({
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token.decode('UTF-8')
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    if not request.json or not 'username' in request.json or not 'password' in request.json or not 'email' in request.json:
        return jsonify({'message': 'Missing username, password or email'}), 400
    
    if User.query.filter_by(username=request.json['username']).first() is not None:
        return jsonify({'message': 'Username already exists'}), 409
    
    new_user = User(
        username=request.json['username'],
        password=generate_password_hash(request.json['password'], method='sha256'),
        email=request.json['email'],
        role='user'
    )
    new_user.save()
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/protected', methods=['GET'])
@auth.login_required
def protected():
    return jsonify({'message': 'This is a protected route'}), 200

@auth.error_handler
def unauthorized(error):
    return jsonify({'message': 'Unauthorized access'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    auth.logout_user()
    return jsonify({'message': 'Successfully logged out'}), 200
