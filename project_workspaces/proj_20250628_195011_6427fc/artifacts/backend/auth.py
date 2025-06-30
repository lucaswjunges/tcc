from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields, marshal_with
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import bcrypt
import datetime
from backend.models import User

auth_ns = Namespace('auth', description='Authentication operations')

# Models
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

register_model = auth_ns.model('Register', {
    'name': fields.String(required=True, description='User name'),
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password')
})

# Response models
user_model = auth_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'name': fields.String(description='User name'),
    'email': fields.String(description='User email')
})

token_response = auth_ns.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'expires_in': fields.Integer(description='Token expiration time in seconds')
})

# Authentication Controller
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response)
    def post(self):
        """
        Login endpoint to receive user credentials and return a JWT token.
        """
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            auth_ns.abort(400, "Missing email or password")
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and verify password
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            auth_ns.abort(401, "Invalid email or password")
        
        # Create JWT token
        access_token = create_access_token(
            identity={'user_id': user.id, 'email': user.email},
            expires_delta=datetime.timedelta(minutes=15)
        )
        
        return {'access_token': access_token, 'expires_in': 900}

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(user_model)
    def post(self):
        """
        Register endpoint to create a new user account.
        """
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not name or not email or not password:
            auth_ns.abort(400, "Missing required fields")
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            auth_ns.abort(409, "Email already registered")
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = User(name=name, email=email, password=hashed_password)
        new_user.save()
        
        return new_user, 201

@auth_ns.route('/protected')
class Protected(Resource):
    @jwt_required()
    @auth_ns.marshal_with(user_model)
    def get(self):
        """
        Protected endpoint to demonstrate JWT token usage.
        """
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            auth_ns.abort(403, "User not found")
        
        return user

@auth_ns.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        """
        Logout endpoint (typically used for frontend to clear token storage)
        """
        auth_ns.abort(405, "Logout not implemented")

@auth_ns.route('/refresh')
class Refresh(Resource):
    @jwt_required(refresh=True)
    @auth_ns.marshal_with(token_response)
    def post(self):
        """
        Token refresh endpoint to obtain a new access token.
        """
        current_user = get_jwt_identity()
        new_token = create_access_token(
            identity=current_user,
            expires_delta=datetime.timedelta(minutes=15)
        )
        return {'access_token': new_token, 'expires_in': 900}

@auth_ns.route('/profile')
class Profile(Resource):
    @jwt_required()
    @auth_ns.marshal_with(user_model)
    def get(self):
        """
        User profile endpoint to fetch current user information.
        """
        user_id = get_jwt_identity()['user_id']
        user = User.query.get(user_id)
        
        if not user:
            auth_ns.abort(403, "User not found")
        
        return user

@auth_ns.errorhandler(400)
def bad_request(error):
    return auth_ns.abort(400, str(error))

@auth_ns.errorhandler(401)
def unauthorized(error):
    return auth_ns.abort(401, str(error))

@auth_ns.errorhandler(403)
def forbidden(error):
    return auth_ns.abort(403, str(error))

@auth_ns.errorhandler(404)
def not_found(error):
    return auth_ns.abort(404, str(error))

@auth_ns.errorhandler(409)
def conflict(error):
    return auth_ns.abort(409, str(error))
