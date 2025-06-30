# src/config.py
import os

# Project Configuration
PROJECT_NAME = "Tarot Insights"
DESCRIPTION = "Professional Tarot card reading service"
WEBSITE_URL = "https://tarotinsights.example.com"
CONTACT_EMAIL = "contact@tarotinsights.example.com"
PAYMENT_EMAIL = "payments@tarotinsights.example.com"

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'secure_random_key_here')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = True
USE_XSRF_PROTECTION = True
XSRF_TOKEN_TIMEOUT = 3600  # 1 hour

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL', 
    'postgresql://user:password@localhost/tarot_db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Email Configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'yes', '1']
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', 'yes', '1']
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'noreply@tarotinsights.example.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')
MAIL_DEFAULT_SENDER = MAIL_USERNAME

# Tarot Deck Configuration
DEFAULT_DECK = "Rider-Waite-Smith"
DECKS = {
    "Rider-Waite-Smith": {
        "name": "Rider-Waite-Smith Tarot",
        "cards": 78,
        "elements": ["Cups", "Pentacles", "Swords", "Wands"]
    },
    "Pentacles": {
        "name": "Pentacles Minor Arcana",
        "cards": 21,
        "elements": ["Pentacles"]
    }
}

# Payment Configuration
PAYMENT_PROVIDER = "Stripe"  # or "PayPal", "Square", etc.
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
PAYMENT_PRICE_ID = "price_1ABC123456789D"  # Example price ID

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Business Configuration
MINIMUM_AGE = 18
MAX_READINGS_PER_CUSTOMER = 3
READING_DURATION_MINUTES = 15
TIP_PERCENTAGE = 15  # Percentage for tips

# Legal Configuration
TERMS_URL = "/static/legal/terms.html"
PRIVACY_URL = "/static/legal/privacy.html"
COOKIE_POLICY_URL = "/static/legal/cookie-policy.html"

# Maintenance Mode
MAINTENANCE_MODE = os.environ.get('MAINTENANCE_MODE', 'False').lower() in ['true', 'yes', '1']

# Analytics Configuration
ANALYTICS_ID = os.environ.get('ANALYTICS_ID', '')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Rate Limiting
REQUEST_RATE_LIMIT = "100 per day"
SESSION_RATE_LIMIT = "5 per minute"

# Content Moderation
CONTENT_MODERATION_ENABLED = True
MODERATION_EMAIL = "moderation@tarotinsights.example.com"

# GDPR Configuration
GDPR_COMPLIANCE = True
EU_DATA_PROCESSING = True