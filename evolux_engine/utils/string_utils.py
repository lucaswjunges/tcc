# Conteúdo para: evolux_engine/utils/string_utils.py
import re

def extract_first_code_block(text: str, language: str = "python") -> str | None:
    """
    Extrai o primeiro bloco de código cercado por ```<language> ... ``` ou ``` ... ```.
    Se a linguagem for especificada, procura por ```<language>.
    Caso contrário, ou se não encontrar com linguagem, procura por ``` sem linguagem.
    """
    if not text:
        return None

    # Tenta primeiro com a linguagem especificada
    # Regex para ```python ... ``` (case insensitive para 'python')
    pattern_with_lang = rf"```{language}\s*([\s\S]*?)\s*```"
    match_with_lang = re.search(pattern_with_lang, text, re.IGNORECASE)
    if match_with_lang:
        return match_with_lang.group(1).strip()

    # Se não encontrou com linguagem, tenta qualquer bloco ``` ... ```
    pattern_any_lang = r"```([\s\S]*?)```"
    match_any_lang = re.search(pattern_any_lang, text)
    if match_any_lang:
        # Verifica se o conteúdo do bloco genérico não é apenas a linguagem
        # Ex: ```python ``` (apenas a palavra python dentro)
        content = match_any_lang.group(1).strip()
        # Se o conteúdo for igual à linguagem nome (ex: "python"), provavelmente é um falso positivo
        # Ou se o conteúdo é muito pequeno para ser código real
        if content.lower() == language.lower() and len(content) < 20: # Heurística
             return None # Ignora se for apenas o nome da linguagem dentro do ```
        if len(content) > 0 : # Garante que há algum conteúdo
            return content
        
    # Se o texto em si parece ser apenas código e não tem ```
    # (Isso é menos confiável e pode ser removido se causar problemas)
    # lines = text.strip().split('\n')
    # if len(lines) > 1 and (lines[0].startswith("def ") or lines[0].startswith("import ") or lines[0].startswith("class ")):
    #     # Heurística: se começa com palavras chave de Python e tem múltiplas linhas
    #     # E não contém "```" em nenhum lugar (para evitar pegar explicações que contenham código)
    #     if "```" not in text:
    #         return text.strip()
            
    return None
