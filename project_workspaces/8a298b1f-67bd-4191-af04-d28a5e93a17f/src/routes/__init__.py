from flask import Blueprint

# Import all routes from the submodules
from .main import main as main_blueprint
from .tarot import tarot as tarot_blueprint
from .payment import payment as payment_blueprint
from .user import user as user_blueprint
from .static_pages import static_pages as static_pages_blueprint

# Create a blueprint collection
routes_bp = Blueprint('routes', __name__)

# Register all blueprints
routes_bp.register_blueprint(main_blueprint, url_prefix='/')
routes_bp.register_blueprint(tarot_blueprint, url_prefix='/tarot')
routes_bp.register_blueprint(payment_blueprint, url_prefix='/payment')
routes_bp.register_blueprint(user_blueprint, url_prefix='/user')
routes_bp.register_blueprint(static_pages_blueprint, url_prefix='/pages')