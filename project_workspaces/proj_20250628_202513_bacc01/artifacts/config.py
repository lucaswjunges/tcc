import os

# Configurações do Projeto
NOME_PROJETO = "Prevenção de Falhas em Motores Industriais"
VERSAO = "1.0.0"
DATA_CRIACAO = "2023-01-01"
DESCRICAO = "Sistema de prevenção de falhas em motores industriais usando CNN e Visão Computacional. Objetivo: desenvolvimento de um artigo publicável em LaTeX."

# Configurações do Banco de Dados
database = {
    "host": "localhost",
    "port": 5432,
    "name": "motor_failure_prevention",
    "user": "postgres",
    "password": "postgres123",
    "sslmode": "disable"
}

# Configurações de Caminhos
ROOT_DIR = os.path.abspath(os.path.dirname(__file__)).replace('\', '/')
DATA_DIR = os.path.join(ROOT_DIR, "data")
MODELOS_DIR = os.path.join(ROOT_DIR, "modelos")
RESULTADOS_DIR = os.path.join(ROOT_DIR, "resultados")
LOG_DIR = os.path.join(ROOT_DIR, "logs")

# Configurações de Visão Computacional
camera_config = {
    "resolucao": "1920x1080",
    "fps": 30,
    "formato_imagem": "jpeg",
    "redimensionamento": 0.5
}

# Configurações de Treinamento da CNN
modelo_cnn = {
    "arquitetura": "ResNet50",
    "camadas": {
        "input": [3, 224, 224],
        "output": 1
    },
    "otimizador": "adam",
    "taxa_aprendizado": 0.001,
    "epocas": 50,
    "batch_size": 32
}

# Configurações para Geração de LaTeX
latex_config = {
    "template": "templates/template.tex",
    "destacamento": "engineering-report",
    "nivel": "bacharelado",
    "incluir_anexos": True,
    "incluir_codigo_fonte": False
}

# Configurações de Ambiente
ambiente = {
    "modo": "desenvolvimento",
    "debug": True,
    "host": "0.0.0.0",
    "port": 5000
}

# Variáveis de Ambiente (serão substituídas pelo .env)
SECRET_KEY = "chave_secreta_segura"
DEBUG = True
