from flask import Blueprint, request, jsonify
from flask_restful import Resource, Api
from werkzeug.security import check_password_hash, generate_password_hash
from backend.models import User
import jwt
import datetime

# Configuração da autenticação
auth_bp = Blueprint('auth', __name__)
api = Api(auth_bp)

# Configurações
SECRET_KEY = 'secret'

# Classe para recursos de autenticação
class AuthResource(Resource):
    def __init__(self):
        self.req_parser = request.parser
        self.req_parser.add_argument('username', type=str, required=True, help='Username is required')
        self.req_parser.add_argument('password', type=str, required=True, help='Password is required')
        super(AuthResource, self).__init__()

    def post(self):
        # Obtém os dados da requisição
        data = self.req_parser.parse_args()
        username = data['username']
        password = data['password']

        # Verifica se o usuário existe
        user = User.query.filter_by(username=username).first()
        if not user:
            return {'message': 'User not found'}, 401

        # Verifica a senha
        if not check_password_hash(user.password, password):
            return {'message': 'Invalid credentials'}, 401

        # Gera o token
        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        access_token = jwt.encode(
            {'public_id': user.id, 'exp': expiration},
            SECRET_KEY, algorithm='HS256'
        )

        return {'access_token': access_token.decode('UTF-8')}, 200

# Classe para registro
class RegisterResource(Resource):
    def __init__(self):
        self.req_parser = request.parser
        self.req_parser.add_argument('username', type=str, required=True, help='Username is required')
        self.req_parser.add_argument('password', type=str, required=True, help='Password is required')
        self.req_parser.add_argument('email', type=str, required=False, help='Email is optional')
        super(RegisterResource, self).__init__()

    def post(self):
        # Obtém os dados da requisição
        data = self.req_parser.parse_args()
        username = data['username']
        password = data['password']
        email = data.get('email')

        # Verifica se o usuário já existe
        if User.query.filter_by(username=username).first():
            return {'message': 'User already exists'}, 400

        # Cria o novo usuário
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        if email:
            new_user.email = email
        new_user.save()

        return {'message': 'User created successfully'}, 201

# Proteção de rotas
from functools import wraps
from flask import g, jsonify
import jwt

# Decorador para proteger rotas
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Verifica se o token está presente nos cookies
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decodifica o token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['public_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            g.user = current_user
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(*args, **kwargs)
    return decorated

# Configura as rotas
api.add_resource(RegisterResource, '/register')
api.add_resource(AuthResource, '/login')

# Exemplo de rota protegida
@auth_bp.route('/protected', methods=['GET'])
@token_required
def protected():
    return {'message': f'Protected route accessed by user {g.user.username}'}, 200