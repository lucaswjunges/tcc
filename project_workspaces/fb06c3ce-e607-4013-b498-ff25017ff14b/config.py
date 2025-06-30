import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'  # MUST change in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tarot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    DEBUG = True  # Set to False in production
    # Stripe configuration (for payments)
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    # Email configuration (for notifications etc.)
    MAIL_SERVER = 'smtp.gmail.com' # Example: Replace with your mail server
    MAIL_PORT = 587 # Example: Replace with your mail server's port
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') # Your email address
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # Your email password or app password


class ProductionConfig(Config):
    DEBUG = False
    # Update database URI for production


class DevelopmentConfig(Config):
    DEBUG = True
    # Other development-specific settings


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # In-memory database for testing
    WTF_CSRF_ENABLED = False # Disable CSRF protection for testing


# Dictionary to access configurations by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig  # Default configuration
}