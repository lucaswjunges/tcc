from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from backend.models import User, Product, Cart, Order, db, bcrypt

# Initialize Flask app
def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(f'config.Config{config_name.capitalize()}')
    
    # Initialize databases
    db.init_app(app)
    bcrypt.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Authentication Routes
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # User Routes
    from .routes.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # Product Routes
    from .routes.products import products_bp
    app.register_blueprint(products_bp, url_prefix='/products')
    
    # Cart Routes
    from .routes.cart import cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')
    
    # Order Routes
    from .routes.orders import orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')
    
    # Database initialization
    with app.app_context():
        db.create_all()
    
    return app

# Create the application factory
app = create_app()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': 'The request was invalid or cannot be served'
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'The request requires user authentication'
    }), 401

if __name__ == '__main__':
    app.run(debug=True)
