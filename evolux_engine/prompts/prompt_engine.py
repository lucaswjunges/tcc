from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
from pathlib import Path

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.llms.model_router import TaskCategory

logger = get_structured_logger("prompt_engine")

class PromptType(Enum):
    """Tipos de prompts disponíveis"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    COMBINED = "combined"

@dataclass
class PromptTemplate:
    """Template de prompt com variáveis e configurações"""
    name: str
    content: str
    variables: List[str] = field(default_factory=list)
    prompt_type: PromptType = PromptType.USER
    task_category: TaskCategory = TaskCategory.GENERIC
    min_tokens: int = 100
    max_tokens: int = 4000
    temperature: float = 0.7
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        # Extrair variáveis automaticamente do template
        self.variables = re.findall(r'\{(\w+)\}', self.content)

@dataclass
class PromptContext:
    """Contexto para construção de prompts"""
    project_goal: str = ""
    project_type: str = ""
    task_description: str = ""
    current_artifacts: str = ""
    error_history: List[str] = field(default_factory=list)
    iteration_count: int = 0
    additional_context: Dict[str, Any] = field(default_factory=dict)

class PromptEngine:
    """
    Engine para construção dinâmica de prompts contextualizados.
    Implementa o sistema de templates especificado na Seção 4 do README.
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.global_context: Dict[str, Any] = {}
        self._initialize_default_templates()
        
        logger.info(f"PromptEngine initialized with {len(self.templates)} templates")
    
    def _initialize_default_templates(self):
        """Inicializa templates padrão do sistema"""
        
        # Template avançado para geração de código com revisão
        self.register_template(PromptTemplate(
            name="code_generation",
            content="""You are a senior software engineer and code reviewer. Create high-quality, production-ready code for the following task:

**Project Goal:** {project_goal}
**Project Type:** {project_type}
**Task:** {task_description}
**Iteration:** {iteration_count}

**Current Project Structure:**
{current_artifacts}

**Previous Errors (if any):**
{error_history}

**CRITICAL REQUIREMENTS:**
- Write clean, maintainable, and well-documented code
- Include comprehensive error handling and input validation
- Add necessary imports and type hints (where applicable) 
- Follow industry best practices and design patterns for {project_type}
- Ensure code is production-ready and scalable
- Consider security implications and implement defensive programming
- Add meaningful comments for complex logic
- Ensure proper code structure and organization

**QUALITY CHECKLIST - Verify each item:**
1. Code compiles/runs without errors
2. Follows language-specific conventions and style guides
3. Handles edge cases and error conditions
4. Is secure and doesn't introduce vulnerabilities
5. Is efficient and performant
6. Is maintainable and well-organized
7. Includes appropriate tests or test hooks
8. Follows SOLID principles where applicable

**SELF-REVIEW PROCESS:**
Before finalizing, ask yourself:
- Does this code solve the problem completely?
- Are there any obvious bugs or issues?
- Could this be implemented more efficiently?
- Is the code readable by other developers?
- Have I considered security and error scenarios?

**Response Format:**
```json
{{
    "file_content": "your complete, production-ready code here",
    "quality_review": {{
        "code_quality_score": 1-10,
        "potential_issues": ["list any concerns"],
        "improvement_suggestions": ["list potential improvements"],
        "security_considerations": ["list security aspects addressed"]
    }}
}}
```""",
            task_category=TaskCategory.CODE_GENERATION,
            temperature=0.2,  # Menor temperatura para maior consistência
            max_tokens=6000,  # Mais tokens para respostas detalhadas
            examples=[
                {
                    "task": "Create Flask app.py with authentication",
                    "response": '{"file_content": "from flask import Flask, request, jsonify, session\\nfrom werkzeug.security import generate_password_hash, check_password_hash\\nimport os\\nfrom functools import wraps\\n\\napp = Flask(__name__)\\napp.secret_key = os.environ.get(\'SECRET_KEY\', \'dev-key-change-in-production\')\\n\\n# Mock user database\\nusers = {}\\n\\ndef login_required(f):\\n    @wraps(f)\\n    def decorated_function(*args, **kwargs):\\n        if \'user_id\' not in session:\\n            return jsonify({\'error\': \'Authentication required\'}), 401\\n        return f(*args, **kwargs)\\n    return decorated_function\\n\\n@app.route(\'/\')\\ndef home():\\n    return jsonify({\'message\': \'Hello World\', \'authenticated\': \'user_id\' in session})\\n\\n@app.route(\'/register\', methods=[\'POST\'])\\ndef register():\\n    try:\\n        data = request.get_json()\\n        if not data or not data.get(\'username\') or not data.get(\'password\'):\\n            return jsonify({\'error\': \'Username and password required\'}), 400\\n        \\n        username = data[\'username\'].strip()\\n        password = data[\'password\']\\n        \\n        if username in users:\\n            return jsonify({\'error\': \'User already exists\'}), 409\\n        \\n        users[username] = generate_password_hash(password)\\n        return jsonify({\'message\': \'User registered successfully\'}), 201\\n    except Exception as e:\\n        return jsonify({\'error\': \'Registration failed\'}), 500\\n\\nif __name__ == \'__main__\':\\n    app.run(debug=os.environ.get(\'FLASK_DEBUG\', False))", "quality_review": {"code_quality_score": 8, "potential_issues": ["Mock database not suitable for production"], "improvement_suggestions": ["Add real database integration", "Add input validation middleware"], "security_considerations": ["Password hashing implemented", "Secret key from environment", "Basic input validation"]}}'
                }
            ]
        ))
        
        # Template para planejamento
        self.register_template(PromptTemplate(
            name="task_planning", 
            content="""You are a project manager and software architect. Create a comprehensive plan for:

**Project Goal:** {project_goal}
**Project Type:** {project_type}

**Context:**
- Current artifacts: {current_artifacts}
- Iteration: {iteration_count}

**Instructions:**
1. Break down the goal into specific, actionable tasks
2. Consider dependencies between tasks
3. Prioritize by importance and complexity
4. Include testing and documentation tasks

**Response Format:**
```json
{{
    "tasks": [
        {{
            "description": "task description",
            "type": "CREATE_FILE|MODIFY_FILE|EXECUTE_COMMAND",
            "priority": "high|medium|low",
            "dependencies": [],
            "acceptance_criteria": "specific success criteria"
        }}
    ]
}}
```""",
            task_category=TaskCategory.PLANNING,
            temperature=0.5
        ))
        
        # Template rigoroso para validação com checklist detalhada
        self.register_template(PromptTemplate(
            name="validation_analysis",
            content="""You are a senior quality assurance engineer and code reviewer. Perform comprehensive validation:

**Task:** {task_description}
**Expected Outcome:** {expected_outcome}
**Acceptance Criteria:** {acceptance_criteria}

**Execution Result:**
- Exit Code: {exit_code}
- Output: {stdout}
- Errors: {stderr}
- Artifacts Changed: {artifacts_changed}

**Project Context:**
{current_artifacts}
**Iteration:** {iteration_count}

**COMPREHENSIVE VALIDATION CHECKLIST:**

1. **Functional Correctness:**
   - Does the task achieve its stated objective?
   - Are all requirements satisfied?
   - Does the output match expectations?

2. **Technical Quality:**
   - Is the implementation technically sound?
   - Are there any obvious bugs or issues?
   - Does it follow best practices?

3. **Code Quality (if applicable):**
   - Is the code readable and maintainable?
   - Are there proper error handling mechanisms?
   - Is the code secure and efficient?

4. **Integration Assessment:**
   - Does it integrate properly with existing components?
   - Are there any breaking changes?
   - Does it maintain system consistency?

5. **Performance Evaluation:**
   - Is the execution time reasonable?
   - Are there performance bottlenecks?
   - Is resource usage appropriate?

6. **Security Review:**
   - Are there any security vulnerabilities?
   - Is sensitive data handled properly?
   - Are inputs properly validated?

7. **Completeness Check:**
   - Are all parts of the task completed?
   - Are there any missing components?
   - Is documentation adequate?

**Response Format:**
```json
{{
    "validation_passed": true/false,
    "confidence_score": 0.0-1.0,
    "overall_quality_score": 1-10,
    "checklist": {{
        "correctness": true/false,
        "completeness": true/false,
        "efficiency": true/false,
        "maintainability": true/false,
        "security": true/false,
        "integration": true/false
    }},
    "detailed_analysis": {{
        "strengths": ["what was done well"],
        "weaknesses": ["areas that need improvement"],
        "risks": ["potential risks or issues"]
    }},
    "identified_issues": [
        {{
            "issue": "description of issue",
            "severity": "critical|high|medium|low",
            "impact": "description of impact",
            "fix_suggestion": "how to fix it"
        }}
    ],
    "suggested_improvements": [
        {{
            "improvement": "description of improvement",
            "priority": "high|medium|low",
            "effort_required": "low|medium|high",
            "expected_benefit": "description of benefit"
        }}
    ],
    "next_steps": ["prioritized list of recommended actions"],
    "requires_iteration": true/false,
    "iteration_focus": "what should be focused on in next iteration if needed"
}}
```""",
            task_category=TaskCategory.VALIDATION,
            temperature=0.1,  # Muito determinístico para validação
            max_tokens=4000
        ))
        
        # Template avançado para análise de erros com soluções múltiplas
        self.register_template(PromptTemplate(
            name="error_analysis",
            content="""You are a senior debugging expert and solution architect. Perform comprehensive error analysis:

**Task that failed:** {task_description}
**Error Details:**
- Exit Code: {exit_code}
- Error Output: {stderr}
- Standard Output: {stdout}

**Complete Error History:** {error_history}
**Project Context:** {current_artifacts}
**Iteration Count:** {iteration_count}

**COMPREHENSIVE ANALYSIS REQUIRED:**

1. **Root Cause Analysis:**
   - What exactly went wrong?
   - Why did it happen?
   - What conditions led to this failure?
   - Is this a recurring pattern?

2. **Error Classification:**
   - Syntax error, runtime error, logic error, environment issue?
   - Transient or persistent?
   - Critical or recoverable?

3. **Impact Assessment:**
   - What parts of the project are affected?
   - What are the downstream consequences?
   - How urgent is the fix?

4. **Multiple Solution Strategies:**
   - Provide 2-3 different approaches to fix
   - Rank them by probability of success
   - Consider trade-offs and side effects

5. **Prevention & Improvement:**
   - How to prevent similar errors
   - What processes or checks to add
   - Code quality improvements

**Response Format:**
```json
{{
    "root_cause": "detailed explanation of what went wrong and why",
    "error_classification": {{
        "type": "syntax|runtime|logic|environment|dependency",
        "severity": "critical|high|medium|low",
        "recurrence_risk": "high|medium|low"
    }},
    "impact_assessment": {{
        "affected_components": ["list of affected parts"],
        "urgency_level": "immediate|high|medium|low",
        "potential_side_effects": ["list of potential issues"]
    }},
    "solution_strategies": [
        {{
            "approach": "primary solution description",
            "success_probability": 0.9,
            "complexity": "low|medium|high",
            "estimated_time": "time estimate",
            "recovery_tasks": [
                {{
                    "description": "specific task to perform",
                    "command": "exact command or action",
                    "expected_outcome": "what should happen"
                }}
            ]
        }}
    ],
    "prevention_measures": [
        {{
            "measure": "prevention strategy",
            "implementation": "how to implement",
            "effectiveness": "high|medium|low"
        }}
    ],
    "quality_improvements": ["broader improvements to prevent similar issues"],
    "debugging_tips": ["specific debugging approaches for this type of error"]
}}
```""",
            task_category=TaskCategory.ERROR_ANALYSIS,
            temperature=0.3,  # Mais determinístico para análise
            max_tokens=5000   # Mais espaço para análise detalhada
        ))
        
        # Template para documentação
        self.register_template(PromptTemplate(
            name="documentation_generation",
            content="""You are a technical writer. Create comprehensive documentation for:

**Project Goal:** {project_goal}
**Project Type:** {project_type}

**Current Project Structure:**
{current_artifacts}

**Documentation Requirements:**
- Clear installation instructions
- Usage examples
- API documentation (if applicable)
- Architecture overview
- Contributing guidelines

**Response Format:**
```json
{{
    "file_content": "markdown documentation content"
}}
```""",
            task_category=TaskCategory.DOCUMENTATION,
            temperature=0.4
        ))
    
    def register_template(self, template: PromptTemplate):
        """Registra um novo template"""
        self.templates[template.name] = template
        logger.debug(f"Template registered: {template.name}, category: {template.task_category.value}")
    
    def build_iterative_prompt(self, 
                              template_name: str,
                              context: PromptContext,
                              previous_attempts: List[str] = None,
                              additional_vars: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Constrói prompt iterativo com melhorias baseadas em tentativas anteriores.
        """
        # Adicionar histórico de tentativas ao contexto
        if previous_attempts:
            context.additional_context['previous_attempts'] = previous_attempts
            context.additional_context['iteration_feedback'] = "Learn from previous attempts and improve"
        
        return self.build_prompt(template_name, context, additional_vars)
    
    def build_prompt(self, 
                    template_name: str,
                    context: PromptContext,
                    additional_vars: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Constrói prompt usando template e contexto.
        
        Args:
            template_name: Nome do template a usar
            context: Contexto do projeto
            additional_vars: Variáveis adicionais
            
        Returns:
            Prompt construído ou None se template não encontrado
        """
        
        template = self.templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None
        
        # Construir variáveis para substituição
        variables = {
            'project_goal': context.project_goal,
            'project_type': context.project_type,
            'task_description': context.task_description,
            'current_artifacts': context.current_artifacts,
            'error_history': '\n'.join(context.error_history[-3:]),  # Últimos 3 erros
            'iteration_count': context.iteration_count,
            'timestamp': datetime.now().isoformat()
        }
        
        # Adicionar contexto adicional
        variables.update(context.additional_context)
        
        # Adicionar variáveis extras
        if additional_vars:
            variables.update(additional_vars)
        
        # Adicionar variáveis globais
        variables.update(self.global_context)
        
        try:
            # Substituir variáveis no template
            prompt = template.content.format(**variables)
            
            # Adicionar exemplos se configurados
            if template.examples:
                examples_text = self._format_examples(template.examples)
                prompt = f"{prompt}\n\n**Examples:**\n{examples_text}"
            
            logger.debug(f"Prompt built successfully for template: {template_name}, length: {len(prompt)}, variables_used: {len(variables)}")
            
            return prompt
            
        except KeyError as e:
            logger.error(f"Missing variable in template: {template_name}, missing_var: {str(e)}, available_vars: {list(variables.keys())}")
            return None
        except Exception as e:
            logger.error(f"Error building prompt for template: {template_name}, error: {str(e)}")
            return None
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Formata exemplos para inclusão no prompt"""
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"Example {i}:")
            for key, value in example.items():
                formatted.append(f"  {key}: {value}")
            formatted.append("")
        return "\n".join(formatted)
    
    def build_conversation(self, 
                          messages: List[Dict[str, str]],
                          context: PromptContext) -> List[Dict[str, str]]:
        """
        Constrói conversa com contexto injetado.
        
        Args:
            messages: Lista de mensagens [{"role": "user", "content": "..."}]
            context: Contexto do projeto
            
        Returns:
            Lista de mensagens com contexto injetado
        """
        
        enhanced_messages = []
        
        for message in messages:
            enhanced_content = message["content"]
            
            # Injetar contexto em mensagens do usuário
            if message["role"] == "user":
                enhanced_content = self._inject_context_into_message(enhanced_content, context)
            
            enhanced_messages.append({
                "role": message["role"],
                "content": enhanced_content
            })
        
        return enhanced_messages
    
    def _inject_context_into_message(self, content: str, context: PromptContext) -> str:
        """Injeta contexto relevante em uma mensagem"""
        
        # Se a mensagem já tem contexto suficiente, não modifica
        if len(content) > 1000:
            return content
        
        context_injection = f"""
**Project Context:**
- Goal: {context.project_goal}
- Type: {context.project_type}
- Current artifacts: {context.current_artifacts[:200]}...

**Your Task:** {content}
"""
        
        return context_injection
    
    def get_template_for_category(self, category: TaskCategory) -> Optional[str]:
        """Retorna nome do template mais adequado para uma categoria"""
        
        category_mapping = {
            TaskCategory.CODE_GENERATION: "code_generation",
            TaskCategory.PLANNING: "task_planning", 
            TaskCategory.VALIDATION: "validation_analysis",
            TaskCategory.ERROR_ANALYSIS: "error_analysis",
            TaskCategory.DOCUMENTATION: "documentation_generation",
            TaskCategory.GENERIC: "code_generation"  # Fallback
        }
        
        return category_mapping.get(category)
    
    def set_global_context(self, key: str, value: Any):
        """Define contexto global disponível para todos os templates"""
        self.global_context[key] = value
        logger.debug(f"Global context updated for key: {key}")
    
    def load_templates_from_directory(self, directory: Union[str, Path]):
        """Carrega templates de um diretório"""
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Template directory not found at path: {str(directory)}")
            return
        
        loaded_count = 0
        for template_file in directory.glob("*.txt"):
            try:
                template_content = template_file.read_text(encoding='utf-8')
                template_name = template_file.stem
                
                # Criar template básico
                template = PromptTemplate(
                    name=template_name,
                    content=template_content
                )
                
                self.register_template(template)
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"Failed to load template from file: {str(template_file)}, error: {str(e)}")
        
        logger.info(f"Templates loaded from directory: {str(directory)}, loaded: {loaded_count}")
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do engine"""
        
        category_count = {}
        for template in self.templates.values():
            category = template.task_category.value
            category_count[category] = category_count.get(category, 0) + 1
        
        return {
            'total_templates': len(self.templates),
            'templates_by_category': category_count,
            'global_context_vars': len(self.global_context),
            'available_templates': list(self.templates.keys())
        }
