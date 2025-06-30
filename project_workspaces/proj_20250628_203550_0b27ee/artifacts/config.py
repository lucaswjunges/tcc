import os

# Configurações gerais do projeto
PROJETO_NOME = "Sistema de Prevenção de Falhas em Motores Industriais"
PROJETO_VERSION = "1.0"

# Diretórios do projeto
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATASET_DIR = os.path.join(ROOT_DIR, 'data', 'dataset')
MODELOS_DIR = os.path.join(ROOT_DIR, 'models')
RESULTADOS_DIR = os.path.join(ROOT_DIR, 'results')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')

# Configurações do banco de dados
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'senha'),
    'database': os.environ.get('DB_NAME', 'motores_previsao')
}

# Configurações da API
API_CONFIG = {
    'host': os.environ.get('API_HOST', '0.0.0.0'),
    'port': int(os.environ.get('API_PORT', 5000)),
    'debug': os.environ.get('API_DEBUG', 'False').lower() == 'true'
}

# Configurações do treinamento da CNN
CNN_CONFIG = {
    'image_size': (224, 224),
    'batch_size': int(os.environ.get('BATCH_SIZE', 32)),
    'epochs': int(os.environ.get('EPOCHS', 50)),
    'learning_rate': float(os.environ.get('LEARNING_RATE', 0.001)),
    'model_type': os.environ.get('MODEL_TYPE', 'resnet50')
}

# Configurações do LaTeX
TEX_CONFIG = {
    'font': os.environ.get('TEX_FONT', 'Times New Roman'),
    'fontsize': int(os.environ.get('TEX_FONTSIZE', 12)),
    'margins': int(os.environ.get('TEX_MARGINS', 1)),
    'output_dir': os.path.join(ROOT_DIR, 'artigo')
}

# Configurações de segurança
SECURITY_CONFIG = {
    'secret_key': os.environ.get('SECRET_KEY', 'chave_secreta_aqui')
}

# Configurações de e-mail
EMAIL_CONFIG = {
    'host': os.environ.get('EMAIL_HOST', 'smtp.gmail.com'),
    'port': int(os.environ.get('EMAIL_PORT', 587)),
    'user': os.environ.get('EMAIL_USER'),
    'password': os.environ.get('EMAIL_PASSWORD')
}

# Configurações de backup
BACKUP_CONFIG = {
    'frequency': os.environ.get('BACKUP_FREQUENCY', 'daily'),
    'destination': os.environ.get('BACKUP_DESTINATION', '/vol/backups')
}