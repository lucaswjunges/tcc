from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, jwt_required
from backend.models import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid username or password'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return jsonify({'message': 'Missing username, password or email'}), 400
    
    if User.query.filter_by(username=data['username']).first() is not None:
        return jsonify({'message': 'Username already exists'}), 400
    
    new_user = User(username=data['username'], email=data['email'], password=data['password'])
    new_user.save()
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    return jsonify(logged_in_as=user.username), 200