from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from config import SECRET_KEY
from backend.models import User

auth_bp = Blueprint('auth', __name__)

# Classe para gerenciar rotas de autenticação
class AuthResource(Resource):
    def __init__(self):
        self.api = Api(auth_bp)

    def register_routes(self):
        self.api.add_resource(RegisterResource, '/register')
        self.api.add_resource(LoginResource, '/login')
        self.api.add_resource(ProtectedRoute, '/protected', methods=['GET'])

# Rota de registro
class RegisterResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or any(k not in data for k in ['username', 'password', 'email']):
            return {'message': 'Dados insuficientes'}, 400

        hashed_password = generate_password_hash(data['password']).decode('utf-8')
        new_user = User(
            username=data['username'],
            password_hash=hashed_password,
            email=data['email']
        )
        new_user.save()
        return {'message': 'Usuário cadastrado com sucesso'}, 201

# Rota de login
class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or any(k not in data for k in ['username', 'password']):
            return {'message': 'Dados insuficientes'}, 400

        user = User.query.filter_by(username=data['username']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            return {'message': 'Credenciais inválidas'}, 401

        # Gerar token JWT
        access_token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            },
            SECRET_KEY
        )
        refresh_token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            },
            SECRET_KEY
        )

        return {
            'access_token': access_token.decode('utf-8'),
            'refresh_token': refresh_token.decode('utf-8'),
            'user_id': user.id
        }, 200

# Rota protegida
class ProtectedRoute(Resource):
    def get(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {'message': 'Token não fornecido'}, 401

        try:
            token = auth_header.split(' ')[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['user_id']
            # Aqui você pode buscar o usuário do banco
            return {'message': f'Acesso concedido para usuário {user_id}'}, 200
        except jwt.ExpiredSignatureError:
            return {'message': 'Token expirado'}, 401
        except jwt.InvalidTokenError:
            return {'message': 'Token inválido'}, 401


# Função para inicializar as rotas
def init_auth_routes(app):
    auth_resource = AuthResource()
    auth_resource.register_routes()
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return auth_bp
