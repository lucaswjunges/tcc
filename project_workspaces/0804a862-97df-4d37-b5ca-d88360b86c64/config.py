import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'  # Replace with a strong, randomly generated key
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tarot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True  # Set to False for production

    # Stripe configuration (for payments)
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')

    # Other configuration options as needed (e.g., email settings, etc.)
    MAIL_SERVER = 'smtp.gmail.com' # Example: Replace with your mail server
    MAIL_PORT = 587  # Example
    MAIL_USE_TLS = True  # Example
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')