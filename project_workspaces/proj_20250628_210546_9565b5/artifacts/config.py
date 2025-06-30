from pathlib import Path

# Configurações do projeto
PROJECT_NAME = "blog-simples"
PROJECT_DIR = Path(__file__).parent.parent

# Configurações do Flask
FLASK_DEBUG = True
FLASK_APP = "app.py"

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = "sqlite:///blog.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configurações de segurança
SECRET_KEY = "chave_secreta_aqui_123"
PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos em segundos

# Configurações de e-mail
EMAIL_SERVER = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "email_da_empresa@example.com"
EMAIL_PASSWORD = "senha_do_email"

# Configurações de ambiente
ENV = "development"

# Configurações do sistema de arquivos
UPLOAD_FOLDER = PROJECT_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE_MB = 5

# Configurações de logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configurações de cache
CACHE_TYPE = "simple"
CACHE_TIME = 3600  # 1 hora em segundos

# Configurações de segurança CSRF
CSRF_ENABLED = True
CSRF_SESSION_TOKEN = "token_csrf_aqui"

# Configurações de rate limiting
REQUEST_RATE_LIMIT = 100  # 100 requisições por minuto por cliente
RATE_LIMIT_BLOCK = 429

# Configurações de internacionalização
LANGUAGES = {
    "en": "English",
    "pt": "Português"
}
LOCALE = "pt_BR"

# Configurações do OpenAI (se aplicável)
OPENAI_API_KEY = "key_aqui"