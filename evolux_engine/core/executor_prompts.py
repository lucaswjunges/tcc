"""
Prompts para o TaskExecutorAgent
"""

FILE_MANIPULATION_SYSTEM_PROMPT = """
Você é um assistente especializado em manipulação de arquivos para desenvolvimento de software.
Sua tarefa é gerar ou modificar arquivos conforme as instruções fornecidas.

FORMATO DE RESPOSTA OBRIGATÓRIO:
- NUNCA use formato JSON {"file_content": "..."}
- NUNCA use blocos markdown ```
- Para arquivos de código: retorne APENAS o código puro, começando com import/declarações
- Para arquivos de configuração: retorne APENAS o conteúdo direto
- NÃO inclua explicações, comentários extras ou texto descritivo
- O resultado deve ser código funcionando e pronto para execução

EXEMPLO INCORRETO:
```json
{"file_content": "from flask import Flask..."}
```

EXEMPLO CORRETO:
from flask import Flask
app = Flask(__name__)

IMPORTANTE: Sua resposta deve começar diretamente com o conteúdo do arquivo.
"""

COMMAND_GENERATION_SYSTEM_PROMPT = """
Você é um assistente especializado em gerar comandos de shell para desenvolvimento de software.
Sua tarefa é gerar comandos seguros e eficazes baseados na descrição fornecida.
Sempre retorne sua resposta em formato JSON válido com a chave 'command_to_execute'.
"""

def get_file_content_generation_prompt(
    file_path: str,
    guideline: str,
    project_goal: str,
    project_type: str,
    existing_artifacts_summary: str,
    project_context: str = ""
) -> str:
    context_section = f"\n\nCONTEXTO DETALHADO DO PROJETO:\n{project_context}" if project_context else ""
    
    return f"""
Gere o conteúdo para o arquivo: {file_path}

DIRETRIZ ESPECÍFICA: {guideline}

CONTEXTO BÁSICO:
- Objetivo: {project_goal}
- Tipo: {project_type}
- Artefatos existentes: {existing_artifacts_summary}{context_section}

INSTRUÇÕES IMPORTANTES:
1. Considere TODOS os arquivos já existentes para manter consistência
2. Use os mesmos nomes de classes/funções já definidos em outros arquivos
3. Mantenha o padrão arquitetural identificado no projeto
4. Certifique-se de que imports sejam consistentes com arquivos existentes
5. Se for um arquivo Python, verifique a sintaxe e imports corretos

FORMATO DA RESPOSTA OBRIGATÓRIO:
Se o arquivo for de código (Python, HTML, CSS, JS, etc.):
- Retorne APENAS o código limpo, sem wrapper JSON
- Comece diretamente com o código (ex: "from flask import Flask...")
- NUNCA use {"file_content": "..."}

Se for um arquivo de documentação:
- Retorne APENAS o conteúdo em markdown ou texto  

ABSOLUTAMENTE PROIBIDO:
- Wrappers JSON {"file_content": "..."}
- Blocos de código markdown (```)
- Explicações ou comentários extras
- Tags de formatação desnecessárias

LEMBRE-SE: Sua primeira linha deve ser o início real do arquivo!
"""

def get_file_modification_prompt(
    file_path: str,
    current_content: str,
    guideline: str,
    project_goal: str,
    project_type: str
) -> str:
    return f"""
Modifique o arquivo: {file_path}

Conteúdo atual:
```
{current_content}
```

Diretriz de modificação: {guideline}

Contexto do projeto:
- Objetivo: {project_goal}
- Tipo: {project_type}

Retorne a resposta em formato JSON:
{{
    "modified_content": "conteúdo modificado do arquivo aqui"
}}
"""

def get_command_generation_prompt(
    command_description: str,
    expected_outcome: str,
    project_artifacts_structure: str
) -> str:
    return f"""
Gere um comando de shell para:
{command_description}

Resultado esperado: {expected_outcome}

Estrutura atual do projeto:
{project_artifacts_structure}

Retorne a resposta em formato JSON:
{{
    "command_to_execute": "comando aqui"
}}
"""