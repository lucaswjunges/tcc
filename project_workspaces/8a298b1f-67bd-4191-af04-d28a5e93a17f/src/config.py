# src/config.py

import os

# Project configuration
PROJECT_NAME = "TarôSapiens"
VERSION = "1.0.0"
DESCRIPTION = "Website de adivinhações de Tarô completo e funcional"

# Environment configuration
ENV = "development"  # development, staging, production
DEBUG = False
TESTING = False

# Paths configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
TEMPLATES_AUTO_RELOAD = True

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = True
PERMANENT_SESSION_LIFETIME = 14 * 24 * 60 * 60  # 14 days

# Database configuration
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tarot_db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "TarôSapiens <contato@tarosapiens.com>"

# Tarot configuration
TAROT_DECK = "Rider-Waite-Smith"
DECK_CARDS = 78
MAX_READING_CARDS = 10
MIN_READING_CARDS = 3
DEFAULT_SPREAD = "beginner"
CARD_MEANINGS_PATH = os.path.join(BASE_DIR, "data/card_meanings.json")

# Payment configuration
PAYMENT_GATEWAY = "stripe"
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
PRICE_ID = "price_1PJZ9p2eOwRkFpL5QjKjKjKj"  # Example price ID

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://tarosapiens.com",
    "https://www.tarosapiens.com"
]

# Rate limiting configuration
REQUEST_RATE_LIMIT = {
    "tarot_reading": {
        "limit": 5,
        "seconds": 3600,
        "message": "Você pode fazer uma nova consulta de Tarô em 1 hora."
    },
    "premium_feature": {
        "limit": 3,
        "seconds": 86400,
        "message": "Você pode acessar esta funcionalidade premium diariamente."
    }
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "tarot": {
            "format": "%(asctime)s - Tarot Card: %(card_name)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_FOLDER, "app.log"),
            "formatter": "standard"
        },
        "tarot_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_FOLDER, "tarot.log"),
            "formatter": "tarot"
        }
    },
    "loggers": {
        "": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True
        },
        "tarot": {
            "handlers": ["tarot_file"],
            "level": "DEBUG",
            "propagate": True
        }
    }
}

# Business configuration
BUSINESS_HOURS = {
    "start": "08:00",
    "end": "20:00",
    "timezone": "America/Sao_Paulo"
}
CONTACT_EMAIL = "contato@tarosapiens.com"
PRICING = {
    "standard": {
        "name": "Consulta Simples",
        "price": 49.99,
        "cards": 3,
        "description": "Uma consulta rápida com 3 cartas para responder sua pergunta principal."
    },
    "premium": {
        "name": "Consulta Premium",
        "price": 99.99,
        "cards": 7,
        "description": "Uma análise detalhada com 7 cartas, incluindo retrospectiva e perspectiva."
    },
    "extended": {
        "name": "Leitura Extensa",
        "price": 199.99,
        "cards": 15,
        "description": "Leitura completa com 15 cartas para uma análise abrangente de sua situação."
    }
}
ETHICS_STATEMENT = """
Nossas leituras de Tarô são realizadas com ética e respeito:
- Sempre honram a liberdade de escolha do cliente
- Não fazem predições absolutas ou determinísticas
- Respeitam o processo livre da vida do cliente
- Mantêm confidencialidade absoluta
- Oferecem orientação, não julgamento
"""

# Legal configuration
TERMS_PATH = os.path.join(BASE_DIR, "legal/terms.html")
PRIVACY_PATH = os.path.join(BASE_DIR, "legal/privacy.html")
LICENSE_PATH = os.path.join(BASE_DIR, "LICENSE")