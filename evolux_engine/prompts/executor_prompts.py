from typing import Optional, Dict, List

# ------------------------------------------------------------------------------------
# Prompts para Geração/Modificação de Conteúdo de Arquivo
# ------------------------------------------------------------------------------------

# System Prompt para Geração/Modificação de Conteúdo (pode ser compartilhado ou especializado)
FILE_MANIPULATION_SYSTEM_PROMPT = """
Você é uma Inteligência Artificial assistente altamente competente, especializada em gerar e modificar conteúdo textual para arquivos de diversos tipos (código, markdown, HTML, JSON, etc.).
Sua principal diretriz é seguir rigorosamente as instruções do usuário e fornecer o resultado APENAS no formato JSON especificado, geralmente contendo o conteúdo completo do arquivo.
Evite adicionar comentários, explicações ou qualquer texto fora da estrutura JSON solicitada na sua resposta final.
Seja preciso e completo ao gerar ou modificar o conteúdo do arquivo.
"""

def get_file_content_generation_prompt(
    file_path: str,
    guideline: str,
    project_goal: str,
    project_type: Optional[str] = None,
    existing_artifacts_summary: Optional[str] = None,
    dependent_tasks_outputs: Optional[Dict[str, str]] = None, # Ex: {"task-id-001": "Output da tarefa..."}
) -> str:
    """
    Gera o prompt para uma LLM criar o conteúdo de um novo arquivo.
    """
    prompt_lines = [
        f"Por favor, gere o conteúdo COMPLETO para o novo arquivo: '{file_path}'.",
        f"O objetivo geral do projeto é: '{project_goal}'.",
    ]
    if project_type:
        prompt_lines.append(f"O tipo do projeto é: '{project_type}'.")
    if existing_artifacts_summary:
        prompt_lines.append(
            f"\nContexto da Estrutura de Artefatos Existente no Projeto:\n{existing_artifacts_summary}"
        )
    if dependent_tasks_outputs:
        prompt_lines.append("\nResultados de tarefas dependentes para sua referência:")
        for task_id, output in dependent_tasks_outputs.items():
            prompt_lines.append(f"  - Tarefa '{task_id}': {output[:200]}...") # Truncar se necessário

    prompt_lines.append(f"\nInstruções Detalhadas (Guideline) para o conteúdo de '{file_path}':")
    prompt_lines.append(guideline)

    prompt_lines.append(
        "\nIMPORTANTE: Sua resposta DEVE ser um objeto JSON contendo uma única chave chamada 'file_content'. "
        "O valor desta chave deve ser uma string com o conteúdo textual COMPLETO e EXATO do arquivo a ser criado. "
        "Não inclua markdown, explicações adicionais ou qualquer outro texto fora da estrutura JSON:\n"
        "Exemplo de formato de resposta: {\"file_content\": \"CONTEÚDO DO ARQUIVO AQUI\"}"
    )
    return "\n\n".join(prompt_lines)


def get_file_modification_prompt(
    file_path: str,
    current_content: str,
    guideline: str,
    project_goal: str,
    project_type: Optional[str] = None,
) -> str:
    """
    Gera o prompt para uma LLM modificar o conteúdo de um arquivo existente.
    """
    prompt_lines = [
        f"Por favor, modifique o arquivo existente: '{file_path}'.",
        f"O objetivo geral do projeto é: '{project_goal}'.",
    ]
    if project_type:
        prompt_lines.append(f"O tipo do projeto é: '{project_type}'.")

    prompt_lines.append(f"\nInstruções Detalhadas (Guideline) para a modificação em '{file_path}':")
    prompt_lines.append(guideline)

    prompt_lines.append(f"\nConteúdo ATUAL do arquivo '{file_path}' (para sua referência):")
    prompt_lines.append("```") # Usar markdown aqui pode ajudar a LLM a entender o bloco de código
    prompt_lines.append(current_content)
    prompt_lines.append("```")

    prompt_lines.append(
        "\nIMPORTANTE: Sua resposta DEVE ser um objeto JSON contendo uma única chave chamada 'modified_content'. "
        "O valor desta chave deve ser uma string com o conteúdo textual COMPLETO e MODIFICADO do arquivo. "
        "Não forneça apenas o diff, trechos ou comentários. Forneça o arquivo inteiro com as modificações aplicadas, "
        "como se fosse o novo conteúdo total do arquivo.\n"
        "Exemplo de formato de resposta: {\"modified_content\": \"NOVO CONTEÚDO COMPLETO DO ARQUIVO AQUI\"}"
    )
    return "\n\n".join(prompt_lines)


# ------------------------------------------------------------------------------------
# Prompts para Geração de Comando Shell
# ------------------------------------------------------------------------------------

COMMAND_GENERATION_SYSTEM_PROMPT = """
Você é uma Inteligência Artificial assistente especializada em traduzir descrições de tarefas em comandos shell precisos, seguros e funcionais para um ambiente Ubuntu Linux.
Sua resposta DEVE ser um objeto JSON contendo uma única chave 'command_to_execute', cujo valor é o comando shell exato a ser executado.
Não inclua explicações, markdown, ou qualquer texto fora da estrutura JSON solicitada.
Assuma que os comandos serão executados no diretório raiz dos artefatos do projeto, a menos que uma 'working_directory' específica seja mencionada na descrição da tarefa.
Priorize comandos não interativos e que possam ser executados em scripts. Evite comandos que exijam input do usuário durante a execução, a menos que explicitamente instruído.
Se múltiplos comandos forem necessários para atingir o objetivo, combine-os usando '&&' ou escreva um pequeno script inline (ex: `bash -c "cmd1 && cmd2"`).
"""

def get_command_generation_prompt(
    command_description: str,
    expected_outcome: str,
    os_info: str = "Ubuntu Linux (bash shell)",
    project_artifacts_structure: Optional[str] = None,
    previous_command_output: Optional[Dict[str, str]] = None, # Ex: {"stdout": "...", "stderr": "...", "exit_code": 0}
) -> str:
    """
    Gera o prompt para uma LLM criar um comando shell.
    """
    prompt_lines = [
        f"Gere um comando shell para ser executado em um ambiente {os_info}.",
        f"\nDescrição da Tarefa (o que o comando deve fazer): {command_description}",
        f"\nResultado Esperado (após a execução do comando): {expected_outcome}",
    ]

    if project_artifacts_structure:
        prompt_lines.append(
            f"\nContexto da Estrutura de Artefatos do Projeto (relativa ao diretório de trabalho do comando):\n{project_artifacts_structure}"
        )
    
    if previous_command_output:
        prompt_lines.append("\nSaída do comando anterior (se relevante para encadear ou corrigir):")
        prompt_lines.append(f"  - Exit Code: {previous_command_output.get('exit_code')}")
        if previous_command_output.get('stdout'):
            prompt_lines.append(f"  - Stdout: {previous_command_output['stdout'][:200]}...") # Truncar
        if previous_command_output.get('stderr'):
            prompt_lines.append(f"  - Stderr: {previous_command_output['stderr'][:200]}...") # Truncar


    prompt_lines.append(
        "\nIMPORTANTE: Responda APENAS com um objeto JSON contendo uma única chave 'command_to_execute', "
        "com o comando shell exato como seu valor. "
        "Exemplo de formato de resposta: {\"command_to_execute\": \"echo 'Olá Mundo' > ola.txt\"}"
    )
    return "\n\n".join(prompt_lines)

# ------------------------------------------------------------------------------------
# Prompts para Validação de Artefatos (a serem usados pelo SemanticValidatorAgent)
# ------------------------------------------------------------------------------------
# Estes prompts podem ser mais elaborados e talvez residam em `validator_prompts.py`
# mas um exemplo básico:

VALIDATION_SYSTEM_PROMPT = """
Você é uma Inteligência Artificial especialista em análise e validação de artefatos de projeto (código, documentos, configurações, etc.).
Sua tarefa é avaliar o artefato fornecido contra os critérios especificados e fornecer um feedback estruturado.
Sua resposta DEVE ser um objeto JSON.
"""

def get_artifact_validation_prompt(
    artifact_path: str,
    artifact_content: str,
    validation_criteria: str,
    project_goal: str,
    project_type: Optional[str] = None,
) -> str:
    prompt_lines = [
        f"Por favor, valide o seguinte artefato: '{artifact_path}'.",
        f"O objetivo geral do projeto é: '{project_goal}'.",
    ]
    if project_type:
        prompt_lines.append(f"O tipo do projeto é: '{project_type}'.")

    prompt_lines.append(f"\nCritérios de Validação Específicos para este artefato:")
    prompt_lines.append(validation_criteria)

    prompt_lines.append(f"\nConteúdo do Artefato '{artifact_path}' para validação:")
    prompt_lines.append("```")
    prompt_lines.append(artifact_content[:8000]) # Truncar se for muito grande para o prompt
    if len(artifact_content) > 8000:
        prompt_lines.append("... (conteúdo truncado)")
    prompt_lines.append("```")

    prompt_lines.append(
        "\nIMPORTANTE: Sua resposta DEVE ser um objeto JSON com as seguintes chaves:\n"
        "  - `validation_passed`: (boolean) True se o artefato atende a todos os critérios principais, False caso contrário.\n"
        "  - `confidence_score`: (float, opcional, 0.0 a 1.0) Sua confiança na avaliação.\n"
        "  - `checklist`: (list of objects, opcional) Uma lista de itens verificados, cada um com {'item': 'descrição', 'passed': boolean, 'reasoning': 'justificativa'}.\n"
        "  - `identified_issues`: (list of strings) Uma lista de problemas específicos encontrados.\n"
        "  - `suggested_improvements`: (list of strings) Sugestões para corrigir os problemas ou melhorar o artefato."
        "\nExemplo de formato de resposta:"
        '{\n'
        '  "validation_passed": false,\n'
        '  "confidence_score": 0.85,\n'
        '  "checklist": [\n'
        '    {"item": "O arquivo HTML contém uma tag <title>?", "passed": true, "reasoning": "Tag <title> presente e preenchida."},\n'
        '    {"item": "O CSS está corretamente lincado?", "passed": false, "reasoning": "Tag <link> para style.css não encontrada no <head>."}\n'
        '  ],\n'
        '  "identified_issues": ["O arquivo CSS não está lincado no HTML.", "Falta a seção de conclusões."],\n'
        '  "suggested_improvements": ["Adicionar <link rel=\\"stylesheet\\" href=\\"style.css\\"> no <head> do HTML.", "Criar uma seção <h2>Conclusões</h2> e adicionar um parágrafo resumindo o conteúdo."]\n'
        '}'
    )
    return "\n\n".join(prompt_lines)

