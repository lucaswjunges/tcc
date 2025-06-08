# run.py
import sys
from pathlib import Path

# Adiciona o diretório atual ao path do Python para garantir que 'src' seja encontrado.
# Esta é a "força bruta" que resolve problemas de importação.
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("--- Iniciando a execução a partir de run.py ---")
print(f"Python Path: {sys.path[0]}")

# Importa a função principal do seu pacote
# Note que agora usamos a importação absoluta que funciona a partir da raiz.
from src.main import main

if __name__ == "__main__":
    # Chama a função principal. O argparse dentro dela pegará os argumentos da linha de comando.
    main()
