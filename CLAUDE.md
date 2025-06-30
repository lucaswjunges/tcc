# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Evolux Engine** is an autonomous AI orchestration system designed to function as a "digital software engineering brain". It transforms high-level project goals into complete, validated deliverables through iterative, autonomous execution without continuous human supervision.

The system implements a **P.O.D.A. cognitive cycle** (Plan, Orient, Decide, Act) with strict modular architecture, defense-in-depth security, and comprehensive observability. The goal is to achieve the complete specification outlined in `readme.md` - an enterprise-grade autonomous software development platform.

## Key Commands

### Basic Operations
```bash
# Run a project with the system
python3 run.py --goal "Create a Flask web application with user authentication"

# Continue an existing project
python3 run.py --goal "Additional requirements" --project-id "proj_20250629_173411_7a4577"

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Development Commands
```bash
# Test core functionality
python3 -c "from evolux_engine.core.orchestrator import Orchestrator; print('✅ Core imports working')"

# Test string utilities
python3 -c "from evolux_engine.utils.string_utils import extract_code_blocks; print('✅ Utils working')"

# Check logging system
python3 -c "from evolux_engine.utils.logging_utils import log; log.info('✅ Logging working')"
```

## Architecture Overview

### Core Orchestration Flow
The system follows a **cognitive cycle** managed by the `Orchestrator`:

1. **Planning Phase**: `PlannerAgent` decomposes high-level goals into task queues
2. **Orientation Phase**: `ContextManager` provides current project state
3. **Decision Phase**: `PromptEngine` + `ModelRouter` create optimized prompts and select models  
4. **Action Phase**: `SecurityGateway` → `SecureExecutor` → `SemanticValidator` execute and validate

### Key Components

#### Core Agents (`evolux_engine/core/`)
- **`Orchestrator`**: Central coordinator managing the cognitive cycle
- **`PlannerAgent`**: Breaks down goals into actionable task sequences with dependency resolution
- **`TaskExecutorAgent`**: Executes individual tasks with LLM integration
- **`SemanticValidator`**: Validates execution results against task intent

#### LLM Infrastructure (`evolux_engine/llms/`)
- **`LLMClient`**: Unified interface for all LLM providers (OpenRouter, OpenAI, Google)
- **`LLMFactory`**: Dynamic LLM instantiation based on provider configuration
- **`ModelRouter`**: Intelligent model selection based on task type and performance metrics

#### Security & Execution (`evolux_engine/security/`, `evolux_engine/execution/`)
- **`SecurityGateway`**: Multi-layer command validation (whitelist/blacklist + AI validation)
- **`SecureExecutor`**: Docker-based sandboxed execution with resource limits

#### Context & State Management (`evolux_engine/services/`)
- **`ContextManager`**: Manages project lifecycle and persistent state
- **`AdvancedContextManager`**: Enhanced context with caching, versioning, and snapshots
- **`ConfigManager`**: Multi-source configuration management (env vars, .env, YAML)

#### Observability (`evolux_engine/services/`)
- **`EnterpriseObservabilityService`**: Metrics collection, distributed tracing, alerting
- Structured logging with RotatingFileHandler and JSON output

### Data Contracts (`evolux_engine/schemas/contracts.py`)

All inter-module communication uses strict Pydantic schemas:
- **`ProjectContext`**: Complete project state with metrics and artifact tracking
- **`Task`**: Individual work units with dependencies and acceptance criteria  
- **`ExecutionResult`**: Command execution results with resource usage
- **`ValidationResult`**: Semantic validation outcomes with feedback

## Critical Implementation Details

### Configuration System
The system uses a sophisticated multi-source configuration approach:
- Environment variables take precedence
- `.env` file for local development
- YAML configuration files for complex settings
- Pydantic validation ensures type safety

### Security Architecture
Defense-in-depth security implementation:
1. **Input Sanitization**: Command normalization and cleanup
2. **AI-based Intent Analysis**: LLM evaluates command safety
3. **Static Analysis**: Whitelist/blacklist pattern matching
4. **Sandboxed Execution**: Docker containers with resource limits
5. **Comprehensive Auditing**: All commands logged immutably

### Error Recovery System
Advanced failure handling with pattern recognition:
- **Transient failures**: Automatic retry with exponential backoff
- **Format failures**: Auto-correction of malformed LLM responses
- **Execution failures**: Feedback-driven debugging cycles
- **Semantic failures**: Task refinement based on validation results
- **Strategic failures**: Escalation to planner for alternative approaches

### Project Workspace Structure
```
project_workspaces/
└── <project_id>/
    ├── artifacts/      # Generated code and files
    ├── context.json    # Persistent project state
    ├── logs/          # Execution logs
    ├── backups/       # State snapshots
    └── temp/          # Temporary execution files
```

## String Utilities & LLM Response Handling

The system includes sophisticated utilities for parsing LLM responses:
- **Code block extraction**: Multi-language support with fallback patterns
- **JSON parsing**: Robust extraction from mixed content with error recovery
- **Response cleaning**: Removes LLM artifacts and formatting issues
- **Content normalization**: Whitespace and encoding standardization

## Task Recovery & Dependencies

The planner implements advanced task management:
- **Failure pattern analysis**: Learns from repeated failures
- **Recovery strategy generation**: Creates targeted fixes based on error types
- **Dependency resolution**: Ensures proper task execution order
- **Adaptive replanning**: Modifies approach when tasks repeatedly fail

## Enterprise Features

### Performance Optimization
- **Model routing**: Selects optimal models based on task type and cost
- **Connection pooling**: Efficient API usage
- **Intelligent caching**: Reduces redundant LLM calls
- **Resource monitoring**: Tracks CPU, memory, and execution time

### Observability & Monitoring
- **Structured logging**: JSON format with correlation IDs
- **Metrics collection**: Performance, cost, and success rate tracking
- **Distributed tracing**: Request flow across components
- **Health monitoring**: System status and alerting

### Configuration Management
- **Multi-environment support**: Development, staging, production configs
- **Dynamic updates**: Runtime configuration changes
- **Validation pipeline**: Comprehensive setting verification
- **Template system**: Default configurations for project types

## Working with the Codebase

### Adding New LLM Providers
1. Extend the `LLMProvider` enum in `contracts.py`
2. Create provider-specific implementation in `evolux_engine/llms/`
3. Update `LLMFactory` to handle the new provider
4. Add configuration options to `GlobalConfig`

### Creating New Task Types
1. Add to `TaskType` enum in `contracts.py`
2. Implement handling in `TaskExecutorAgent`
3. Update `PlannerAgent` to generate the new task type
4. Add validation logic in `SemanticValidator`

### Extending Security Rules
1. Update whitelist/blacklist patterns in `SecurityGateway`
2. Modify AI validation prompts for new security scenarios
3. Add new risk assessment categories
4. Update audit logging for new security events

### Important Notes
- All API keys must be configured via environment variables or `.env` file
- The system is designed to run autonomously - avoid hardcoded paths or manual interventions
- Use structured logging throughout - never use print statements
- Follow the Pydantic schema contracts strictly for inter-module communication
- Docker is required for secure command execution
- The system learns from failures - check `failure_history` and `recovery_strategies` for debugging