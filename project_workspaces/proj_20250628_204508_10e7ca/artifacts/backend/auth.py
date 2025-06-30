from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, jwt_refresh_token_required, get_jwt
import datetime
from backend.models import User

# Configurações de autenticação
auth_bp = Blueprint('auth', __name__)

# Configurações do JWT
auth_bp.config['JWT_SECRET_KEY'] = 'super-secret'
auth_bp.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=15)
auth_bp.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)

# Registro de usuário
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Dados de usuário incorretos'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Usuário já existe'}), 400
    
    new_user = User(username=data['username'], password=data['password'])
    new_user.save()
    return jsonify({'message': 'Usuário registrado com sucesso'}), 201

# Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Dados de login incorretos'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.verify_password(data['password']):
        return jsonify({'message': 'Credenciais inválidas'}), 401
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_access_token(identity=user.id, additional_claims={'is_refresh': True})
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.username
    }), 200

# Proteção de rotas
@auth_bp.route('/protected', methods=['GET'])
@jwt_required
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': 'Usuário não autenticado'}), 401
    
    return jsonify({'message': f'Acesso concedido para {user.username}'}), 200

# Gerar novo token com refresh
@auth_bp.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

# Middleware de proteção
@auth_bp.route('/admin', methods=['GET'])
@jwt_required
def admin_protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': 'Acesso negado'}), 403
    
    return jsonify({'message': 'Acesso administrativo concedido'}), 200