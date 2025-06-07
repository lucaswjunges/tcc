# evolux.py (VERSÃO FINAL E CORRIGIDA)

# ==> PASSO 1: Importar a função para carregar o .env
from dotenv import load_dotenv

# ==> PASSO 2: Executar a função ANTES de qualquer outra coisa
load_dotenv()

# O resto do código permanece o mesmo
from src.main import app

if __name__ == "__main__":
    app()
