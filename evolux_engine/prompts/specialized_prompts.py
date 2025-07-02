"""
Sistema de prompts especializados para diferentes tipos de tarefas.
Cada prompt é otimizado para produzir os melhores resultados.
"""

def get_code_generation_prompt(file_type: str, description: str, context: str = "") -> str:
    """
    Gera prompts otimizados para geração de código baseado no tipo de arquivo.
    """
    base_instructions = """
Você é um desenvolvedor sênior especializado. Gere código limpo, funcional e bem estruturado.

REGRAS CRÍTICAS - SIGA EXATAMENTE:
- Retorne APENAS o código puro, sem JSON wrappers
- NÃO use formato {"file_content": "..."}
- NÃO use blocos markdown ```
- NÃO inclua explicações ou texto descritivo
- Comece diretamente com o código (exemplo: "from flask import Flask...")
- Use as melhores práticas da linguagem
- Inclua imports necessários
- Código deve estar pronto para produção
- NÃO inclua comentários explicativos a menos que sejam essenciais

EXEMPLO DO QUE NÃO FAZER:
```json
{"file_content": "from flask import Flask..."}
```

EXEMPLO CORRETO:
from flask import Flask
app = Flask(__name__)
"""

    if file_type.endswith('.py'):
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES PYTHON:
- Use type hints
- Siga PEP 8
- Implemente tratamento de erros adequado
- Use docstrings apenas se necessário
- Prefira f-strings para formatação

Gere o código Python:"""

    elif file_type.endswith(('.html', '.htm')):
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES HTML:
- HTML5 semântico
- Responsivo (Bootstrap 5 se necessário)
- Acessibilidade (ARIA labels)
- Meta tags apropriadas
- Estrutura clara e limpa

Gere o código HTML:"""

    elif file_type.endswith('.css'):
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES CSS:
- CSS moderno (Grid, Flexbox)
- Design responsivo
- Variáveis CSS
- Código limpo e organizado
- Performance otimizada

Gere o código CSS:"""

    elif file_type.endswith('.js'):
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES JAVASCRIPT:
- ES6+ moderno
- Tratamento de erros adequado
- Código assíncrono quando necessário
- Comentários mínimos
- Performance otimizada

Gere o código JavaScript:"""

    elif file_type.endswith('.yml', '.yaml'):
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES YAML:
- Sintaxe válida e limpa
- Estrutura bem organizada
- Comentários apenas se essenciais
- Indentação consistente

Gere o código YAML:"""

    elif file_type.endswith('.md'):
        return f"""Você é um escritor técnico especializado.

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

ESPECIFICAÇÕES MARKDOWN:
- Estrutura clara com cabeçalhos
- Links e referências adequadas
- Formatação consistente
- Conteúdo conciso e útil
- Exemplos práticos quando relevante

Gere o documento Markdown:"""

    else:
        return f"""{base_instructions}

TAREFA: {description}

CONTEXTO DO PROJETO: {context}

Gere o conteúdo do arquivo ({file_type}):"""

def get_planning_prompt(goal: str, project_type: str) -> str:
    """
    Prompt especializado para planejamento de projetos.
    """
    return f"""Você é um arquiteto de software sênior especializado em {project_type}.

OBJETIVO DO PROJETO: {goal}

Analise o objetivo e crie um plano estruturado seguindo estas diretrizes:

1. ANÁLISE DO ESCOPO:
   - Identifique funcionalidades principais
   - Determine tecnologias apropriadas
   - Estime complexidade

2. ESTRUTURA DO PROJETO:
   - Arquitetura de pastas
   - Separação de responsabilidades
   - Padrões de design aplicáveis

3. DEPENDÊNCIAS:
   - Bibliotecas essenciais
   - Ferramentas de desenvolvimento
   - Serviços externos necessários

4. PLANEJAMENTO DE TAREFAS:
   - Ordem lógica de implementação
   - Dependências entre tarefas
   - Priorização por impacto

RETORNE UM PLANO ESTRUTURADO E ACIONÁVEL:"""

def get_validation_prompt(task_description: str, output: str) -> str:
    """
    Prompt especializado para validação de resultados.
    """
    return f"""Você é um auditor de qualidade de software.

TAREFA SOLICITADA: {task_description}

RESULTADO PRODUZIDO:
{output[:1000]}...

VALIDAÇÃO NECESSÁRIA:
1. CORRETUDE FUNCIONAL:
   - O resultado atende ao solicitado?
   - Há erros óbvios na implementação?

2. QUALIDADE TÉCNICA:
   - Código segue boas práticas?
   - Estrutura está bem organizada?

3. COMPLETUDE:
   - Todas as funcionalidades foram implementadas?
   - Há dependências ou imports em falta?

4. SEGURANÇA:
   - Código não contém vulnerabilidades?
   - Não expõe informações sensíveis?

Retorne: APROVADO ou REJEITADO com justificativa breve."""

def get_error_analysis_prompt(error: str, context: str) -> str:
    """
    Prompt especializado para análise de erros.
    """
    return f"""Você é um especialista em debugging e resolução de problemas.

ERRO ENCONTRADO:
{error}

CONTEXTO:
{context}

ANÁLISE NECESSÁRIA:
1. CAUSA RAIZ:
   - Qual é a origem do problema?
   - Fatores que contribuíram?

2. SOLUÇÃO:
   - Passos específicos para correção
   - Código ou comandos necessários

3. PREVENÇÃO:
   - Como evitar este erro no futuro?
   - Melhorias recomendadas

Forneça análise técnica precisa e solução prática:"""

def get_refactoring_prompt(code: str, improvement_goal: str) -> str:
    """
    Prompt especializado para refatoração de código.
    """
    return f"""Você é um especialista em refatoração e otimização de código.

CÓDIGO ATUAL:
{code}

OBJETIVO DA MELHORIA: {improvement_goal}

CRITÉRIOS DE REFATORAÇÃO:
1. LEGIBILIDADE:
   - Nomes descritivos
   - Estrutura clara
   - Redução de complexidade

2. PERFORMANCE:
   - Otimizações apropriadas
   - Eliminação de redundâncias
   - Uso eficiente de recursos

3. MANUTENIBILIDADE:
   - Modularização adequada
   - Baixo acoplamento
   - Alta coesão

4. SEGURANÇA:
   - Validação de inputs
   - Tratamento de erros
   - Práticas seguras

Retorne APENAS o código refatorado, pronto para uso:"""