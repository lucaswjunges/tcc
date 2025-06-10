#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Limpando ambiente virtual antigo (se existir) e arquivos de cache..."
# Desativar qualquer venv ativo pode ser útil, mas 'deactivate' só funciona se o venv estiver ativo.
# type deactivate &>/dev/null && deactivate

rm -rf venv
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
rm -rf build dist *.egg-info evolux_engine.egg-info # Adicionado evolux_engine.egg-info


# Comente as linhas abaixo se não quiser recriar o .env ou o diretório de workspaces
# ATENÇÃO: Isso apagará o .env e o project_workspaces existentes!
# rm -f .env
# rm -rf project_workspaces

echo "Criando novo ambiente virtual 'venv'..."
python3 -m venv venv

echo "Ativando o ambiente virtual para este script..."
source venv/bin/activate

echo "Atualizando pip e instalando setuptools e wheel..."
pip install --upgrade pip setuptools wheel

echo "Instalando dependências de requirements.txt..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "AVISO: requirements.txt não encontrado. Pulando instalação de dependências."
fi

echo "Instalando projeto em modo editável..."
if [ -f setup.py ]; then
    pip install -e .
else
    echo "AVISO: setup.py não encontrado. Pulando instalação em modo editável."
fi


echo "Criando arquivo .env com valores padrão (se não existir ou se descomentado acima)..."
# Este bloco só cria o .env se ele não existir, para não sobrescrever chaves.
# Se você descomentou `rm -f .env` acima, ele será sempre recriado.
if [ ! -f .env ]; then
    echo "Criando novo arquivo .env..."
    cat << EOF > .env
EVOLUX_OPENROUTER_API_KEY=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
EVOLUX_OPENAI_API_KEY=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
EVOLUX_PROJECT_BASE_DIR=${HOME}/Documents/evolux-engine/project_workspaces
EVOLUX_LLM_PROVIDER=openrouter
EVOLUX_MODEL_PLANNER=anthropic/claude-3-haiku-20240307 # Modelo específico
EVOLUX_MODEL_EXECUTOR=anthropic/claude-3-haiku-20240307 # Modelo específico
EVOLUX_MAX_CONCURRENT_TASKS=5
EVOLUX_LOGGING_LEVEL=INFO
EOF
    echo "Arquivo .env criado. POR FAVOR, EDITE-O COM SUAS API KEYS REAIS."
else
    echo "Arquivo .env já existe. Não foi sobrescrito."
fi

# Cria o diretório de workspaces se não existir
PROJECT_BASE_DIR_VALUE=$(grep EVOLUX_PROJECT_BASE_DIR .env | cut -d '=' -f2)
if [ -z "$PROJECT_BASE_DIR_VALUE" ]; then
    # Tenta pegar do default se não estiver no .env (improvável se .env foi criado acima)
    PROJECT_BASE_DIR_VALUE="${HOME}/Documents/evolux-engine/project_workspaces"
fi
# Expande o ~ para o diretório home real
EVAL_PROJECT_BASE_DIR=$(eval echo "$PROJECT_BASE_DIR_VALUE")

if [ ! -d "$EVAL_PROJECT_BASE_DIR" ]; then
    echo "Criando diretório base de projetos em ${EVAL_PROJECT_BASE_DIR}..."
    mkdir -p "$EVAL_PROJECT_BASE_DIR"
fi


echo "---------------------------------------------------------------------"
echo "Script de limpeza e configuração concluído."
echo "Para ativar o ambiente virtual no seu terminal, execute:"
echo "source venv/bin/activate"
echo "Certifique-se de que o arquivo .env contém suas API keys corretas."
echo "---------------------------------------------------------------------"

# Desativar o venv ativado por este script (não afeta o terminal do usuário)
deactivate &>/dev/null || true
