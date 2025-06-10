#!/bin/bash
echo "Limpando ambiente virtual e arquivos de cache..."
# Desativar qualquer venv ativo pode ser útil, mas 'deactivate' só funciona se o venv estiver ativo.
# type deactivate &>/dev/null && deactivate

rm -rf venv
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
rm -rf build dist *.egg-info
# rm -rf project_workspaces # Cuidado com isso se tiver trabalho que não quer perder
# rm -f .env  # Cuidado com isso se tiver chaves que não quer perder

echo "Criando novo ambiente virtual..."
python3 -m venv venv

echo "Ativando o ambiente virtual e instalando dependências..."
# A ativação aqui só vale para este script.
source venv/bin/activate

echo "Instalando projeto em modo editável..."
pip install -e .
echo "Instalando dependências de requirements.txt..."
pip install -r requirements.txt

echo "Criando arquivo .env..."
# Cuidado para não sobrescrever .env se já existir e tiver segredos
cat << EOF > .env
