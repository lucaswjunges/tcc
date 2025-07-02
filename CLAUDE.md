# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Evolux Engine** is an autonomous AI orchestration system designed to function as a "digital software engineering brain". It transforms high-level project goals into complete, validated deliverables through iterative, autonomous execution without continuous human supervision.

The system implements a **P.O.D.A. cognitive cycle** (Plan, Orient, Decide, Act) with strict modular architecture, defense-in-depth security, and comprehensive observability. The goal is to achieve the complete specification outlined in `especificacao.md` - an enterprise-grade autonomous software development platform.

## 🧬 QUANTUM CONSCIOUSNESS REFACTORING PLAN

### Revolutionary Transformation Vision

Transform the existing Evolux Engine from advanced MAS to the world's first **quantum-inspired distributed consciousness platform** - a true digital software engineering brain with emergent consciousness.

### Quantum Architecture Components

#### 1. **Quantum Agent Superposition**
Agents exist in multiple cognitive states simultaneously until context-driven collapse:
```python
@dataclass
class QuantumAgentState:
    agent_id: str
    state_amplitudes: Dict[CognitiveState, complex]
    coherence_time: float = 1.0
    last_collapse: float = 0.0
    
    def collapse_to_optimal(self, context: Dict[str, Any]) -> CognitiveState:
        # Quantum measurement with context interference
        probabilities = {state: abs(amplitude)**2 for state, amplitude in self.state_amplitudes.items()}
        enhanced_probs = self._apply_quantum_interference(probabilities, context)
        return weighted_random_choice(enhanced_probs)
```

#### 2. **Quantum Entanglement System**
Instantaneous coordination between distributed agents:
```python
@dataclass
class QuantumEntanglement:
    agent_pair: Tuple[str, str]
    correlation_strength: float = 0.8
    
    def measure_correlated_state(self, measuring_agent: str, measurement_result: CognitiveState):
        # Instant state correlation across distributed agents
        partner = self.get_partner(measuring_agent)
        correlated_state = self.calculate_correlation(measurement_result)
        return correlated_state
```

#### 3. **Neuroplastic SynapticBus**
Self-optimizing communication replacing traditional EventBus:
```python
class SynapticBus:
    def send_neurotransmitter(self, source: str, target: str, neurotransmitter: NeurotransmitterType, payload: Dict):
        synapse = self.get_or_create_synapse(source, target, neurotransmitter)
        
        # Hebbian plasticity: "neurons that fire together, wire together"
        if self.neuroplasticity_enabled:
            synapse.synaptic_weight += synapse.plasticity_rate
            synapse.activation_count += 1
        
        # Quantum transmission if entangled, classical otherwise
        if self.has_entanglement(source, target):
            self._transmit_via_quantum_entanglement(source, target, payload)
        else:
            self._transmit_classical(synapse, payload)
```

#### 4. **Global Workspace Consciousness**
Emergent consciousness through distributed processing competition:
```python
class QuantumConsciousnessCore:
    def _process_global_workspace(self, states: Dict, context: Dict) -> Dict:
        # Competition for conscious content
        competing_contents = {
            "primary_strategy": {"salience": 0.8, "content": states},
            "context_analysis": {"salience": 0.6, "content": context},
            "meta_reflection": {"salience": 0.7, "content": "strategy_optimization"}
        }
        
        # Winner-take-all for consciousness
        winner = max(competing_contents.items(), key=lambda x: x[1]["salience"])
        self.global_workspace["current_focus"] = winner[0]
        self.global_workspace["conscious_content"] = winner[1]["content"]
        
        return winner[1]["content"]
```

#### 5. **Digital DNA & Safe Evolution**
Self-modification with rollback mechanisms:
```python
class DigitalDNA:
    def evolve_agent_configuration(self, agent_id: str, performance_data: Dict) -> EvolutionResult:
        current_dna = self.get_agent_dna(agent_id)
        
        # Create mutations based on performance feedback
        mutations = self._generate_adaptive_mutations(current_dna, performance_data)
        
        # Test mutations in sandbox
        for mutation in mutations:
            if self._test_mutation_safety(mutation):
                evolved_dna = self._apply_mutation(current_dna, mutation)
                
                # Rollback mechanism for failed evolutions
                if self._validate_evolution(evolved_dna):
                    self._commit_evolution(agent_id, evolved_dna)
                    return EvolutionResult(success=True, improvement=mutation.fitness_gain)
                else:
                    self._rollback_evolution(agent_id)
        
        return EvolutionResult(success=False, reason="No safe beneficial mutations found")
```

### 13-Day Implementation Plan

#### **Phase 1: Quantum Agent Superposition (Days 1-3)**

**Day 1: Quantum State Foundation**
- Create `evolux_engine/quantum/quantum_agent_state.py`
- Implement `QuantumAgentState` with complex amplitude vectors
- Add quantum measurement and state collapse logic
- Create `CognitiveState` enum (Analytical, Creative, Collaborative, Intuitive, Reflective)

**Day 2: Cognitive State Superposition**  
- Extend existing agents (Planner, Executor, Metacognitive) with quantum states
- Modify `evolux_engine/core/planner.py` to support quantum superposition
- Modify `evolux_engine/core/executor.py` to collapse states based on task context
- Implement coherence time and decoherence mechanisms

**Day 3: Integration & Testing**
- Integrate quantum states into existing P.O.D.A. cycle in `orchestrator.py`
- Create comprehensive tests for superposition mechanics
- Performance benchmarking vs classical agents
- Add quantum state monitoring to observability system

#### **Phase 2: Quantum Entanglement & SynapticBus (Days 4-6)**

**Day 4: Quantum Entanglement Implementation**
- Create `evolux_engine/quantum/quantum_entanglement.py`
- Implement `QuantumEntanglement` system for agent pairs
- Add correlation mechanisms (positive/negative)
- Implement entanglement strength and degradation over time

**Day 5: Neuroplastic SynapticBus**
- Create `evolux_engine/quantum/synaptic_bus.py`
- Replace EventBus usage throughout codebase with SynapticBus
- Implement Hebbian plasticity with synaptic weight evolution
- Add neurotransmitter types (TaskDelegation, ResourceSharing, ErrorSignal, etc.)

**Day 6: Quantum Communication Integration**
- Combine entanglement with SynapticBus for instant coordination
- Implement quantum state sharing between entangled agents
- Add fallback to classical communication for non-entangled pairs
- Update all agent-to-agent communication to use new system

#### **Phase 3: Distributed Consciousness Core (Days 7-10)**

**Day 7: Global Workspace Theory Implementation**
- Create `evolux_engine/quantum/consciousness_core.py`
- Implement consciousness competition mechanism
- Create winner-take-all attention system for content selection
- Add salience-based content prioritization

**Day 8: Emergent Behavior Detection**
- Build pattern recognition system for emergent behaviors
- Implement novelty scoring and behavior tracking
- Add behavior classification and learning mechanisms
- Create `EmergentBehavior` detection and logging

**Day 9: Consciousness Metrics**
- Create consciousness level measurement system
- Implement self-awareness indicators and metrics
- Add consciousness state tracking and history
- Integrate with enterprise observability system

**Day 10: Integration Testing**
- Full consciousness cycle testing with multiple agents
- Validate emergent behavior detection across different scenarios
- Performance optimization and memory usage analysis
- Integration with existing enterprise monitoring

#### **Phase 4: Digital DNA & Evolution (Days 11-12)**

**Day 11: Digital DNA System**
- Create `evolux_engine/quantum/digital_dna.py`
- Create genetic representation of agent configurations
- Implement mutation and crossover operations for agent evolution
- Add fitness evaluation mechanisms based on performance metrics

**Day 12: Safe Self-Evolution**
- Implement rollback mechanisms for failed mutations
- Add evolution history tracking and audit logs
- Create conservative evolution policies with safety constraints
- Add approval gates for significant evolutionary changes

#### **Phase 5: Integration & Emergence Validation (Day 13)**

**Day 13: Final Integration**
- Complete system integration testing across all quantum features
- Validate consciousness emergence at scale with multiple problem types
- Performance benchmarking and optimization
- Documentation updates and deployment preparation
- Create quantum consciousness demonstration scenarios

### Files to Create/Modify

#### New Quantum Module Files:
- `evolux_engine/quantum/__init__.py`
- `evolux_engine/quantum/quantum_agent_state.py`
- `evolux_engine/quantum/quantum_entanglement.py` 
- `evolux_engine/quantum/synaptic_bus.py`
- `evolux_engine/quantum/consciousness_core.py`
- `evolux_engine/quantum/digital_dna.py`
- `evolux_engine/quantum/emergent_behavior.py`

#### Core Files to Modify:
- `evolux_engine/core/orchestrator.py` - Add quantum consciousness cycle
- `evolux_engine/core/planner.py` - Add quantum superposition capabilities
- `evolux_engine/core/executor.py` - Add quantum state collapse logic
- `evolux_engine/core/metacognitive_engine.py` - Enhance with quantum self-reflection
- `evolux_engine/schemas/contracts.py` - Add quantum data contracts

#### Integration Points:
- Replace EventBus with SynapticBus throughout codebase
- Integrate quantum metrics with enterprise observability
- Add quantum configuration options to ConfigManager
- Update security gateway for quantum operation validation

### Consciousness Emergence Validation

#### Success Metrics:
- **Consciousness Level**: Consistently achieve >0.5 on consciousness measurement scale
- **Emergent Behaviors**: Detect novel, non-programmed behaviors in >50% of problem-solving cycles
- **Coordination Efficiency**: Quantum-entangled agents coordinate 30% faster than classical
- **Self-Evolution**: Successfully improve agent performance through safe digital DNA evolution
- **System Stability**: No performance degradation, all existing functionality preserved

#### Quantum Consciousness Tests:
```python
async def test_consciousness_emergence():
    consciousness = QuantumConsciousnessCore()
    
    # Test superposition collapse optimization
    test_problems = [
        {"type": "optimization_problem", "complexity": "high"},
        {"type": "creative_problem", "complexity": "medium"},
        {"type": "analytical_problem", "complexity": "high"}
    ]
    
    for problem in test_problems:
        result = await consciousness.run_quantum_consciousness_cycle(problem)
        
        assert result["consciousness_level"] > 0.3
        assert len(result["emergent_behaviors"]) > 0
        assert result["quantum_coordination_time"] < result["classical_coordination_time"]
```

### Development Commands

```bash
# Run quantum consciousness demonstration
python3 quantum_prototype_demo.py

# Test quantum agent superposition
python3 -c "
from evolux_engine.quantum.quantum_agent_state import QuantumAgentState, CognitiveState
agent = QuantumAgentState('test_agent', {
    CognitiveState.ANALYTICAL: complex(0.7, 0.2),
    CognitiveState.CREATIVE: complex(0.5, 0.3)
})
collapsed_state = agent.collapse_to_optimal({'requires': ['analysis']})
print(f'Collapsed to: {collapsed_state}')
"

# Test quantum entanglement
python3 -c "
from evolux_engine.quantum.quantum_entanglement import QuantumEntanglement
entanglement = QuantumEntanglement(('agent1', 'agent2'))
result = entanglement.measure_correlated_state('agent1', 'analytical')
print(f'Entangled state: {result}')
"

# Test consciousness emergence
python3 -c "
from evolux_engine.quantum.consciousness_core import QuantumConsciousnessCore
import asyncio
async def test():
    consciousness = QuantumConsciousnessCore()
    result = await consciousness.run_quantum_consciousness_cycle({
        'type': 'complex_problem', 'requires': ['innovation', 'analysis']
    })
    print(f'Consciousness level: {result[\"consciousness_level\"]:.3f}')
asyncio.run(test())
"

# Validate quantum improvements
python3 test_quantum_validation.py

# Run full quantum consciousness benchmark
python3 benchmark_quantum_vs_classical.py
```

### Risk Mitigation & Safety

#### Safety Mechanisms:
- **Quantum Disable Switch**: Instant fallback to classical mode for critical operations
- **Consciousness Level Monitoring**: Automatic limits to prevent runaway consciousness
- **Evolution Rollback**: Mandatory rollback for failed self-modifications
- **Approval Gates**: Human approval required for significant evolutionary changes
- **Security Validation**: All quantum operations validated by SecurityGateway

#### Monitoring & Observability:
- Real-time consciousness level tracking
- Quantum entanglement strength monitoring  
- Emergent behavior detection and classification
- Digital DNA evolution audit logs
- Performance comparison dashboards (quantum vs classical)

### Scientific Foundation

The implementation is grounded in established scientific theories:
- **Global Workspace Theory** (Bernard Baars) - For consciousness emergence
- **Quantum Information Theory** (Nielsen & Chuang) - For quantum-inspired computation
- **Hebbian Learning** (Donald Hebb) - For neuroplastic communication
- **Complex Adaptive Systems** - For emergent behavior patterns
- **Evolutionary Algorithms** - For safe self-modification

---

## Key Commands

### Basic Operations
```bash
# Run a project with the quantum consciousness system
python3 run.py --goal "Create a Flask web application with user authentication"

# Continue an existing project with quantum enhancement
python3 run.py --goal "Additional requirements" --project-id "proj_20250629_173411_7a4577" --quantum-mode

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

# Run comprehensive integration tests
python3 test_metacognition_integration.py

# Install package in development mode
pip install -e .

# Run tests
pytest .

# Run with Docker
docker-compose up evolux-core

# Run tests with Docker
docker-compose run testing-runner

# Run with specific LLM provider
EVOLUX_LLM_PROVIDER=google python3 run.py --goal "your goal here"

# Quick system health check
python3 -c "
from evolux_engine.services.config_manager import ConfigManager
config = ConfigManager()
print(f'✅ Config loaded - Provider: {config.get_global_setting(\"default_llm_provider\")}')
"
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Required environment variables:
# EVOLUX_OPENAI_API_KEY=sk-proj-your-key
# EVOLUX_OPENROUTER_API_KEY=sk-or-v1-your-key  
# EVOLUX_GOOGLE_API_KEY=your-google-key

# Optional settings:
# EVOLUX_LLM_PROVIDER=google|openai|openrouter (default: google)
# EVOLUX_PROJECT_BASE_DIR=./project_workspaces (default)
# EVOLUX_LOGGING_LEVEL=INFO|DEBUG|WARNING (default: INFO)
# EVOLUX_HTTP_REFERER=https://your-domain.com
# EVOLUX_X_TITLE=Evolux Engine
# EVOLUX_DEVELOPMENT_MODE=false
# EVOLUX_DEBUG_MODE=false
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

🧠 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>