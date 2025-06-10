rm -rf venv
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
rm -rf build dist *.egg-info
rm -rf project_workspaces
rm .env  # Opcional, se quiser recriar o .env
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements.txt
echo "EVOLUX_OPENROUTER_API_KEY=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" > .env
echo "EVOLUX_PROJECT_BASE_DIR=/home/lucas-junges/Documents/evolux-engine/project_workspaces" >> .env
echo "EVOLUX_LLM_PROVIDER=openrouter" >> .env
echo "EVOLUX_MODEL_PLANNER=anthropic/claude-3-haiku" >> .env
echo "EVOLUX_MODEL_EXECUTOR=anthropic/claude-3-haiku" >> .env
echo "EVOLUX_MAX_CONCURRENT_TASKS=5" >> .env
echo "EVOLUX_LOGGING_LEVEL=INFO" >> .env
python3 run.py --goal "criar um site em python local que mostre hello world"

