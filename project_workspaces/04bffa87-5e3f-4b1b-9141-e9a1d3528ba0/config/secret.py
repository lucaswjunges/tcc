# config/secret.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///tarot_cards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAYMENT_SECRET = os.environ.get('PAYMENT_SECRET') or 'your-payment-secret-here'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    TAROT_DECK = os.environ.get('TAROT_DECK') or 'standard'
    DEBUG = os.environ.get('DEBUG') in ('True', '1', 'true')