#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Limpando ambiente virtual antigo (se existir) e arquivos de cache..."
# Desativar qualquer venv ativo pode ser útil, mas 'deactivate' só funciona se o venv estiver ativo.
# type deactivate &>/dev/null && deactivate

rm -rf venv
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
rm -rf build dist *.egg-info evolux_engine.egg-info


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
# --- Chaves de API (POR FAVOR, PREENCHA COM SUAS CHAVES REAIS) ---
EVOLUX_OPENROUTER_API_KEY=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
EVOLUX_OPENAI_API_KEY=sk-proj-pzow2j29yNVz-uiaxlAuIiXd9k_WuK1ylbLagIBRNqo1hu8XrZaF3NvXJfwW148R3lPER4
EVOLUX_GOOGLE_API_KEY=AIzaSyBp-PRpkDEpbBuuKQIF7_hiyQueqpJLAtE
OPENROUTER_API_KEY=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
OPENAI_API_KEY=sk-proj-pzow2j29yNVz-uiaxlAuIiXd9k_WuK1ylbLagIBRNqo1hu8XrZaF3NvXJfwW148R3lPER4
GOOGLE_API_KEY=AIzaSyBp-PRpkDEpbBuuKQIF7_hiyQueqpJLAtE

# --- Configurações do Projeto ---
# O padrão será o diretório 'project_workspaces' dentro da pasta atual.
EVOLUX_PROJECT_BASE_DIR=${PWD}/project_workspaces

# --- Configurações de LLM (padrão configurado para Gemini) ---
EVOLUX_LLM_PROVIDER=google
EVOLUX_MODEL_PLANNER=gemini-1.5-pro-latest
EVOLUX_MODEL_EXECUTOR=gemini-1.5-pro-latest

# --- Configurações de Rede (usado pelo OpenRouter) ---
EVOLUX_HTTP_REFERER="http://localhost:3000"
EVOLUX_APP_TITLE="Evolux Engine (TCC)"

# --- Configurações de Execução ---
EVOLUX_MAX_CONCURRENT_TASKS=3
EVOLUX_MAX_ITERATIONS=10
EVOLUX_MAX_REPLAN_ATTEMPTS=3

# --- Configurações de Logging ---
EVOLUX_LOGGING_LEVEL=INFO
EVOLUX_LOG_TO_FILE=False

EOF
    echo "Arquivo .env criado. POR FAVOR, EDITE-O COM SUAS API KEYS REAIS."
else
    echo "Arquivo .env já existe. Não foi sobrescrito."
fi

# Cria o diretório de workspaces se não existir
# Usando PWD para garantir que o caminho seja absoluto e correto
if [ ! -d "${PWD}/project_workspaces" ]; then
    echo "Criando diretório base de projetos em ${PWD}/project_workspaces..."
    mkdir -p "${PWD}/project_workspaces"
fi


echo "---------------------------------------------------------------------"
echo "Script de limpeza e configuração concluído."
echo "Para ativar o ambiente virtual no seu terminal, execute:"
echo "source venv/bin/activate"
echo "Certifique-se de que o arquivo .env contém suas API keys corretas."
echo "---------------------------------------------------------------------"

# Desativar o venv ativado por este script (não afeta o terminal do usuário)
deactivate &>/dev/null || true