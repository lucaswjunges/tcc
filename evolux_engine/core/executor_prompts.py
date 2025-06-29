"""
Prompts para o TaskExecutorAgent
"""

FILE_MANIPULATION_SYSTEM_PROMPT = """
Você é um assistente especializado em manipulação de arquivos para desenvolvimento de software.
Sua tarefa é gerar ou modificar arquivos conforme as instruções fornecidas.
Sempre retorne sua resposta em formato JSON válido com a chave solicitada.
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
    existing_artifacts_summary: str
) -> str:
    return f"""
Gere o conteúdo para o arquivo: {file_path}

Diretriz: {guideline}

Contexto do projeto:
- Objetivo: {project_goal}
- Tipo: {project_type}
- Artefatos existentes: {existing_artifacts_summary}

Retorne a resposta em formato JSON:
{{
    "file_content": "conteúdo do arquivo aqui"
}}
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