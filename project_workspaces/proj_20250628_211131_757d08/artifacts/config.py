import os

# Configurações do Projeto
PROJECT_NAME = "Sistema de Prevenção de Falhas em Motores Industriais"
ARTICLE_TITLE = "Prevenção de Falhas em Motores Industriais usando CNN e Visão Computacional"
AUTHORS = ["Nome do Autor 1", "Nome do Autor 2", "Nome do Autor 3"]
JOURNAL_NAME = "Journal de Engenharia e Tecnologia"
SUBMISSION_DATE = "2023-10-15"

# Configurações do Banco de Dados
DB_TYPE = "PostgreSQL"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "motor_failure_prevention"
DB_USER = "postgres_user"
DB_PASSWORD = "secure_password123"

# Configurações de Variáveis de Ambiente
ENVIRONMENT = "development"  # development, staging, production
DEBUG_MODE = True

# Configurações de Segurança
SECRET_KEY = "random_secure_key_123456789"  # Para assinatura de JWT, etc.

# Configurações de Armazenamento
UPLOAD_FOLDER = "data/uploads/"
SAVE_DIRECTORY = "data/"

# Configurações de API
API_BASE_URL = "https://api.example.com/motor-failure"
API_KEY = "api-key-1234567890"

# Configurações do Modelo ML
MODEL_TYPE = "CNN"
MODEL_PATH = "models/failure_detection_model.h5"
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 50
LEARNING_RATE = 0.001

# Configurações de Email
EMAIL_SERVER = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USER = "noreply@example.com"
EMAIL_PASSWORD = "password"
EMAIL_RECIPIENTS = ["reviewer1@example.com", "editor@example.com"]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# Configurações Gerais
MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
TIMEZONE = "America/Sao_Paulo"
