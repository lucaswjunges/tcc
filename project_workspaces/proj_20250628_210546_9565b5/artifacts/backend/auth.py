import os
import datetime
import jwt
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import User, db

def init_auth(app):
    auth_bp = Blueprint('auth', __name__)
    
    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not data or not 'username' in data or not 'email' in data or not 'password' in data:
            return jsonify({'message': 'Missing fields'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 409
        
        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(username=data['username'], email=data['email'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or not 'email' in data or not 'password' in data:
            return jsonify({'message': 'Missing email or password'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Invalid email or password'}), 401
        
        # Create JWT
        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        token = jwt.encode({
            'user_id': user.id,
            'exp': expiration
        }, os.getenv('JWT_SECRET_KEY'), algorithm='HS256')
        
        return jsonify({
            'token': token.decode('utf-8'),
            'user_id': user.id
        }), 200
    
    @auth_bp.route('/protected', methods=['GET'])
    def protected():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Missing token'}), 401
        
        try:
            data = jwt.decode(token.split(' ')[1], os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return jsonify({'message': 'Successfully protected route'}), 200
    
    @app.route('/logout', methods=['GET'])
    def logout():
        # In a real application, you might implement server-side session management
        return jsonify({'message': 'Logout successful'}), 200
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
