# MCP LLM Server - Makefile
# ================================

.PHONY: help install install-dev test test-unit test-integration lint format type-check clean build docs serve-docs

# Default target
help: ## Show this help message
	@echo "MCP LLM Server - Development Commands"
	@echo "====================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev,docs]"
	pre-commit install

# Testing
test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/ -v -m "unit"

test-integration: ## Run integration tests only
	pytest tests/ -v -m "integration"

test-coverage: ## Run tests with coverage report
	pytest tests/ --cov=mcp_llm_server --cov-report=html --cov-report=term

# Code Quality
lint: ## Run linting checks
	flake8 src/ tests/ examples/
	black --check src/ tests/ examples/

format: ## Format code with black
	black src/ tests/ examples/

type-check: ## Run type checking with mypy
	mypy src/mcp_llm_server

quality: lint type-check ## Run all quality checks

# Development
run: ## Run the server in development mode
	python -m mcp_llm_server --debug

run-example: ## Run basic usage example
	python examples/basic_usage.py

# Building
clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean ## Build distribution packages
	python -m build

publish-test: build ## Publish to test PyPI
	python -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	python -m twine upload dist/*

# Documentation
docs: ## Build documentation
	cd docs && mkdocs build

serve-docs: ## Serve documentation locally
	cd docs && mkdocs serve

# Docker
docker-build: ## Build Docker image
	docker build -t mcp-llm-server .

docker-run: ## Run Docker container
	docker run -p 8080:8080 --env-file .env mcp-llm-server

# Configuration
setup-env: ## Setup environment file from example
	cp .env.example .env
	@echo "Please edit .env file with your API keys"

validate-config: ## Validate configuration
	python -c "from mcp_llm_server.config import settings; settings.validate_all(); print('✅ Configuration is valid')"

# MCP Integration
mcp-add: ## Add server to Claude Code
	claude mcp add llm-server "python -m mcp_llm_server"

mcp-remove: ## Remove server from Claude Code
	claude mcp remove llm-server

mcp-list: ## List MCP servers
	claude mcp list

# Security
security-check: ## Run security checks
	pip-audit
	bandit -r src/

# Performance
profile: ## Run performance profiling
	python -m cProfile -o profile.stats -m mcp_llm_server
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Database (if using persistent storage)
migrate: ## Run database migrations (placeholder)
	@echo "No migrations needed for current in-memory storage"

# Logging
logs: ## View server logs
	tail -f logs/mcp-server.log

logs-error: ## View error logs only
	grep -E "(ERROR|CRITICAL)" logs/mcp-server.log | tail -20

# Monitoring
health-check: ## Check server health
	python -c "from mcp_llm_server.server import MCPLLMServer; import asyncio; server = MCPLLMServer(); print('✅ Server can be initialized')"

stats: ## Show server statistics
	python -c "from mcp_llm_server.config import settings; print('Server:', settings.server.name, settings.server.version)"

# Development Tools
shell: ## Start interactive Python shell with server context
	python -c "from mcp_llm_server import *; import asyncio; print('MCP LLM Server shell ready')"

debug: ## Run server with debug logging
	LOG_LEVEL=DEBUG python -m mcp_llm_server

# Git hooks
pre-commit: quality test-unit ## Run pre-commit checks
	@echo "✅ Pre-commit checks passed"

# Release
version: ## Show current version
	python -c "from mcp_llm_server import __version__; print(__version__)"

tag: ## Create git tag for current version
	git tag -a v$(shell python -c "from mcp_llm_server import __version__; print(__version__)") -m "Release v$(shell python -c "from mcp_llm_server import __version__; print(__version__)")"
	git push origin v$(shell python -c "from mcp_llm_server import __version__; print(__version__)")

# Cleanup
reset: ## Reset development environment
	make clean
	pip uninstall -y mcp-llm-server
	make install-dev

# All-in-one commands
setup: setup-env install-dev validate-config ## Complete setup for new development environment
	@echo "✅ Setup complete! Edit .env file and run 'make mcp-add' to integrate with Claude Code"

check: quality test ## Run all checks (quality + tests)

deploy: clean build publish ## Clean, build and publish package