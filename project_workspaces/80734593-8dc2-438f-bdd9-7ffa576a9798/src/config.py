# src/config.py

import os

# Environment configuration
class Config:
    # Base directory for the application
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tarot_cards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_COOKIE_NAME = 'tarot_session'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'mycsrfsecretkey'
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'yes', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', 'yes', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Payment configuration
    PAYMENT_PROVIDER = 'stripe'  # or 'paypal', 'razorpay', etc.
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Tarot configuration
    TAROT_DECKS = [
        {
            'name': 'Rider-Waite-Smith',
            'description': 'The classic tarot deck with detailed symbolism',
            'price': 49.99
        },
        {
            'name': 'Pentacles',
            'description': 'Focuses on manifestation and abundance',
            'price': 44.99
        },
        {
            'name': 'Thoth',
            'description': 'Advanced tarot system for deep spiritual work',
            'price': 79.99
        }
    ]
    
    # Website configuration
    WEBSITE_NAME = 'Oracle of the Stars'
    WEBSITE_DESCRIPTION = 'Professional tarot card readings and guidance'
    WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://oracleofthestars.com')
    WEBSITE_LOGO = os.environ.get('WEBSITE_LOGO', '/static/img/logo.png')
    
    # Currency configuration
    CURRENCY = 'USD'
    CURRENCY_SYMBOL = '$'
    
    # Legal configuration
    TERMS_OF_SERVICE_URL = '/terms'
    PRIVACY_POLICY_URL = '/privacy'
    RETURN_POLICY_URL = '/return-policy'
    
    # Moderation configuration
    MODERATION_REQUIRED = True
    MODERATION_EMAIL = os.environ.get('MODERATION_EMAIL')
    
    # Business configuration
    BUSINESS_LICENSE = os.environ.get('BUSINESS_LICENSE')
    BUSINESS_REGISTRATION = os.environ.get('BUSINESS_REGISTRATION')
    BUSINESS_TAX_ID = os.environ.get('BUSINESS_TAX_ID')
    
    # Rate limiting configuration
    MAX_REQUESTS_PER_MINUTE = 10
    MAX_REQUESTS_PER_HOUR = 100

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS', True))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_db.sqlite'
    MAIL_PORT = 1025
    MAIL_SERVER = 'localhost'
    MAIL_USERNAME = 'dev@example.com'
    MAIL_PASSWORD = 'devpassword'
    STRIPE_PUBLISHABLE_KEY = 'pk_test_1234567890'
    STRIPE_SECRET_KEY = 'sk_test_0987654321'

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'testingsecretkey'
    WTF_CSRF_ENABLED = False
    MAIL_ENABLED = False
    STRIPE_PUBLISHABLE_KEY = None
    STRIPE_SECRET_KEY = None