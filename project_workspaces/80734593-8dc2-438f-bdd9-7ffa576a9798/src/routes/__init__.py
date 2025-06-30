from flask import Blueprint

# Import all route blueprints
from .home import home_bp
from .tarot import tarot_bp
from .about import about_bp
from .contact import contact_bp
from .payment import payment_bp
from .reading import reading_bp
from .blog import blog_bp
from .admin import admin_bp

# List of all blueprints to register with the main app
ALL_BLUEPRINTS = [
    home_bp,
    tarot_bp,
    about_bp,
    contact_bp,
    payment_bp,
    reading_bp,
    blog_bp,
    admin_bp
]

__all__ = ['ALL_BLUEPRINTS']