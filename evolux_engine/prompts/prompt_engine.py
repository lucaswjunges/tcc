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
        
        logger.info("PromptEngine initialized", 
                   template_count=len(self.templates))
    
    def _initialize_default_templates(self):
        """Inicializa templates padrão do sistema"""
        
        # Template para geração de código
        self.register_template(PromptTemplate(
            name="code_generation",
            content="""You are a senior software engineer. Create high-quality code for the following task:

**Project Goal:** {project_goal}
**Project Type:** {project_type}
**Task:** {task_description}

**Current Project Structure:**
{current_artifacts}

**Requirements:**
- Write clean, maintainable code
- Include appropriate error handling
- Add necessary imports
- Follow best practices for {project_type}
- Ensure code is production-ready

**Response Format:**
```json
{{
    "file_content": "your code here"
}}
```""",
            task_category=TaskCategory.CODE_GENERATION,
            temperature=0.3,
            examples=[
                {
                    "task": "Create Flask app.py",
                    "response": '{"file_content": "from flask import Flask\\napp = Flask(__name__)\\n\\n@app.route(\'/\')\\ndef home():\\n    return \'Hello World\'\\n\\nif __name__ == \'__main__\':\\n    app.run(debug=True)"}'
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
        
        # Template para validação
        self.register_template(PromptTemplate(
            name="validation_analysis",
            content="""You are a quality assurance engineer. Analyze the execution result:

**Task:** {task_description}
**Expected Outcome:** {expected_outcome}

**Execution Result:**
- Exit Code: {exit_code}
- Output: {stdout}
- Errors: {stderr}

**Project Context:**
{current_artifacts}

**Analysis Required:**
1. Did the task complete successfully?
2. Does the output meet the acceptance criteria?
3. Are there any issues or improvements needed?

**Response Format:**
```json
{{
    "validation_passed": true/false,
    "confidence_score": 0.0-1.0,
    "issues_found": ["list of issues"],
    "suggested_improvements": ["list of improvements"],
    "next_steps": ["recommended actions"]
}}
```""",
            task_category=TaskCategory.VALIDATION,
            temperature=0.2
        ))
        
        # Template para análise de erros
        self.register_template(PromptTemplate(
            name="error_analysis",
            content="""You are a debugging expert. Analyze this error and provide solutions:

**Task that failed:** {task_description}
**Error Details:**
- Exit Code: {exit_code}
- Error Output: {stderr}
- Standard Output: {stdout}

**Error History:** {error_history}

**Project Context:**
{current_artifacts}

**Analysis Required:**
1. Root cause of the error
2. Specific fix recommendations
3. Prevention strategies

**Response Format:**
```json
{{
    "root_cause": "explanation of what went wrong",
    "fix_strategy": "how to fix this specific error",
    "prevention_measures": "how to prevent similar errors",
    "recovery_tasks": [
        {{
            "description": "task to fix the issue",
            "command": "specific command or action"
        }}
    ]
}}
```""",
            task_category=TaskCategory.ERROR_ANALYSIS,
            temperature=0.4
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
        logger.debug("Template registered", 
                    name=template.name,
                    category=template.task_category.value)
    
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
            logger.error("Template not found", template=template_name)
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
            
            logger.debug("Prompt built successfully",
                        template=template_name,
                        length=len(prompt),
                        variables_used=len(variables))
            
            return prompt
            
        except KeyError as e:
            logger.error("Missing variable in template",
                        template=template_name,
                        missing_var=str(e),
                        available_vars=list(variables.keys()))
            return None
        except Exception as e:
            logger.error("Error building prompt",
                        template=template_name,
                        error=str(e))
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
        logger.debug("Global context updated", key=key)
    
    def load_templates_from_directory(self, directory: Union[str, Path]):
        """Carrega templates de um diretório"""
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning("Template directory not found", path=str(directory))
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
                logger.error("Failed to load template",
                           file=str(template_file),
                           error=str(e))
        
        logger.info("Templates loaded from directory",
                   directory=str(directory),
                   loaded=loaded_count)
    
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