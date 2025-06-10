# Conteúdo para: evolux_engine/utils/string_utils.py
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


# Exemplo de uso (pode ser removido ou colocado em um bloco if __name__ == "__main__":)
if __name__ == '__main__':
    sample_text_python = """
    Aqui está algum texto.
    ```python
    def hello():
        print("Olá, Python!")
    ```
    Mais texto.
    """
    sample_text_generic = """
    Bloco genérico:
    ```
    print("Olá, mundo genérico!")
    ```
    """
    sample_text_no_newline = "```python\nprint('Test')\n```"
    sample_text_inline_lang = "```python print('Inline lang')\n```" # Este não seria pego pelo primeiro regex
    sample_text_complex = """
    Some intro.
    ```python
    # Bloco 1 Python
    x = 10
    print(f"X is {x}")
    ```
    Some middle text.
    ```javascript
    // Bloco Javascript
    console.log("Hello JS");
    ```
    E um bloco genérico:
    ```
    Este é texto puro.
    Pode ter múltiplas linhas.
    ```
    Fim.
    """

    print(f"Python block: {extract_first_code_block(sample_text_python, 'python')}")
    print(f"Generic block (lang=python): {extract_first_code_block(sample_text_generic, 'python')}") # Não deve encontrar
    print(f"Generic block (lang=''): {extract_first_code_block(sample_text_generic, '')}")
    print(f"Generic block (lang=None): {extract_first_code_block(sample_text_generic, None)}")
    print(f"Python block (no newline): {extract_first_code_block(sample_text_no_newline, 'python')}")
    print(f"Generic block (no newline, lang=''): {extract_first_code_block(sample_text_no_newline, '')}")
    print(f"Python block (inline lang): {extract_first_code_block(sample_text_inline_lang, 'python')}")

    print("\n--- Todos os Blocos ---")
    all_blocks = extract_code_blocks(sample_text_complex)
    for lang, code in all_blocks:
        print(f"Linguagem: {lang}, Código:\n---\n{code}\n---")

