import os

# Configurações do projeto
PROJETO_NOME = "Loja Eletrônica"
PROJETO_DESCRICAO = "Loja virtual para venda de eletrônicos"
PROJETO_VERSION = "1.0.0"

# Configurações do banco de dados
database_type = "postgresql"
database_host = "localhost"
database_name = "ecommerce_eletronicos"
database_user = "postgres_user"
database_password = "secure_password123"
database_port = 5432

# Configurações de segurançaSECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
SESSION_COOKIE_MAX_AGE = 14400
CSRF_ENABLED = True

# Configurações do servidorDEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'
PORT = int(os.environ.get('FLASK_PORT', 5000))
HOST = os.environ.get('FLASK_HOST', '0.0.0.0')

# Configurações de e-commerceCARRINHO_LIMITE = 5
PEDIDO_ENTREGA_PADRAO = 3  # dias úteis

# Configurações do ambiente
AMBIENTE_DESENVOLVIMENTO = os.environ.get('DESENVOLVIMENTO', 'False') == 'True'
AMBIENTE_PRODUCAO = os.environ.get('PRODUCAO', 'False') == 'True'

# Configurações de e-mailEMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USUARIO = "contato@loja.com.br"
EMAIL_SENHA = os.environ.get('EMAIL_PASSWORD')
EMAIL_USUARIO_REMETENTE = "contato@loja.com.br"

# Configurações de armazenamentoUPLOADS_PASTA = "static/uploads"
MAX_UPLOAD_SIZE = 1024 * 1024 * 10  # 10 MB

# Configurações de pagamentoPROCESSOR_PAGAMENTO = "pagseguro"
API_KEY_PAGSEGURO = os.environ.get('API_KEY_PAGSEGURO')
