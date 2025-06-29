import re

def extract_first_code_block(text: str, language: str = "python") -> str | None:
    """
    Extrai o primeiro bloco de código delimitado por ```language ... ``` ou ``` ... ``` de uma string.

    Args:
        text: A string da qual extrair o bloco de código.
        language: O especificador de linguagem opcional (padrão "python").
                  Se None ou "", procurará blocos de código genéricos ``` ... ```.

    Returns:
        O conteúdo do primeiro bloco de código encontrado, ou None se nenhum bloco for encontrado.
    """
    if language:
        # Tenta encontrar blocos de código com especificador de linguagem (ex: ```python)
        # O padrão considera variações como ```python\n ou ```python \n
        # (?s) permite que . corresponda a novas linhas
        match = re.search(rf"```{language}\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Se nenhum bloco específico da linguagem for encontrado ou language não for fornecido,
    # tenta encontrar um bloco de código genérico (```\n ... \n```)
    match = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Se nenhum dos anteriores, tenta encontrar blocos que começam e terminam com ```
    # sem necessariamente ter a linguagem ou a nova linha após o ``` inicial.
    # Isso é menos específico e pode pegar mais coisas, use com cautela.
    match = re.search(r"```(.*?)```", text, re.DOTALL)
    if match:
        # Remove os delimitadores e qualquer nome de linguagem que possa estar na primeira linha
        content = match.group(1)
        lines = content.splitlines()
        if lines and lines[0].strip().lower() == language.lower(): # Remove a linha da linguagem, se for o caso
            return "\n".join(lines[1:]).strip()
        return content.strip()
        
    return None

def extract_code_blocks(text: str) -> list[tuple[str | None, str]]:
    """
    Extrai todos os blocos de código de uma string.
    Um bloco de código é definido como qualquer coisa entre ```língua\n e \n``` ou ```\n e \n```.
    Retorna uma lista de tuplas (linguagem, código).
    Onde 'linguagem' pode ser None se não especificado.
    """
    # Padrão regex para encontrar blocos de código com ou sem especificador de linguagem
    # ```(?:([\w+-]+)\s*)?\n(.*?)```
    # 1. ```
    # 2. (?:([\w+-]+)\s*)? : Grupo opcional não capturador para a linguagem
    #    ([\w+-]+)         : Grupo capturador 1: nome da linguagem (letras, números, _, +, -)
    #    \s*               : Zero ou mais espaços após a linguagem
    # 3. \n                   : Nova linha
    # 4. (.*?)               : Grupo capturador 2: o código em si (não guloso)
    # 5. \n```                : Nova linha e delimitador final
    # re.DOTALL faz com que . corresponda a novas linhas também
    pattern = re.compile(r"```(?:([\w+-]+)\s*)?\n(.*?)\n```", re.DOTALL)
    matches = pattern.findall(text)
    
    # Se não encontrar o padrão acima, tenta um mais simples sem a necessidade da nova linha
    # após o ``` inicial para o conteúdo, e que pode não ter linguagem
    if not matches:
        pattern_simple = re.compile(r"```(?:([\w+-]+)\s*)?(.*?)```", re.DOTALL)
        raw_matches = pattern_simple.findall(text)
        # Para o padrão simples, precisamos limpar o conteúdo do código
        # se a primeira linha for a linguagem
        cleaned_matches = []
        for lang, code_block in raw_matches:
            code_lines = code_block.strip().splitlines()
            if lang and code_lines and code_lines[0].strip().lower() == lang.lower():
                actual_code = "\n".join(code_lines[1:]).strip()
            else:
                actual_code = code_block.strip()
            cleaned_matches.append((lang if lang else None, actual_code))
        return cleaned_matches

    return [(lang if lang else None, code.strip()) for lang, code in matches]

def extract_json_from_llm_response(text: str) -> str | None:
    """
    Extrai JSON de uma resposta de LLM que pode conter texto adicional.
    Procura por padrões comuns de JSON em respostas de LLM.
    
    Args:
        text: Texto da resposta do LLM
        
    Returns:
        String JSON extraída ou None se não encontrar
    """
    # Remove espaços em branco extras
    text = text.strip()
    
    # Primeiro, tenta encontrar JSON em blocos de código
    json_block = extract_first_code_block(text, "json")
    if json_block:
        return json_block
    
    # Procura por JSON sem delimitadores de código
    # Encontra o primeiro { e o último } que fecham
    start_index = text.find("{")
    if start_index == -1:
        return None
        
    # Conta chaves abertas e fechadas para encontrar o JSON completo
    brace_count = 0
    for i, char in enumerate(text[start_index:], start_index):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return text[start_index:i+1]
    
    return None

def extract_content_from_json_response(text: str, key: str = "file_content") -> str | None:
    """
    Extrai conteúdo específico de uma resposta JSON do LLM, lidando com casos especiais
    como markdown dentro de strings JSON.
    
    Args:
        text: Texto da resposta do LLM
        key: Chave para extrair do JSON
        
    Returns:
        Conteúdo extraído ou None se não encontrar
    """
    import json
    
    # Primeiro tenta extrair JSON normal
    json_str = extract_json_from_llm_response(text)
    if json_str:
        try:
            parsed = json.loads(json_str)
            if key in parsed:
                return parsed[key]
        except json.JSONDecodeError:
            pass
    
    # Se não funcionou, tenta extrair usando regex para casos problemáticos
    # Procura por padrões como "file_content": "..."
    import re
    
    # Padrão para encontrar a chave e seu valor
    # Lida com aspas escapadas e conteúdo multilinha
    pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)\"'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        content = match.group(1)
        # Decodifica escapes JSON básicos
        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        return content
    
    # Tenta um padrão mais flexível para blocos de código dentro de JSON
    pattern = rf'"{key}"\s*:\s*"```\w*\n(.*?)\n```"'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Último recurso: tenta extrair entre as primeiras aspas após a chave
    pattern = rf'"{key}"\s*:\s*"([^"]*(?:\\"[^"]*)*)"'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1)
        content = content.replace('\\"', '"')
        return content
    
    return None

def sanitize_llm_response(text: str) -> str:
    """
    Sanitiza resposta de LLM removendo caracteres problemáticos.
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Remove caracteres de controle exceto \n, \r, \t
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normaliza quebras de linha
    sanitized = re.sub(r'\r\n|\r', '\n', sanitized)
    
    # Remove espaços no final das linhas
    sanitized = re.sub(r'[ \t]+$', '', sanitized, flags=re.MULTILINE)
    
    return sanitized

def truncate_text_safely(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Trunca texto de forma segura, evitando quebrar no meio de palavras.
    
    Args:
        text: Texto a ser truncado
        max_length: Comprimento máximo
        suffix: Sufixo a ser adicionado quando truncado
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    if max_length <= len(suffix):
        return suffix[:max_length]
    
    truncated_length = max_length - len(suffix)
    truncated = text[:truncated_length]
    
    # Procura pelo último espaço para não quebrar no meio de uma palavra
    last_space = truncated.rfind(' ')
    if last_space > truncated_length * 0.8:  # Se o espaço estiver nos últimos 20%
        truncated = truncated[:last_space]
    
    return truncated + suffix