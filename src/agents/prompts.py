# src/agents/prompts.py

class Prompts:
    @staticmethod
    def get_system_prompt(agent_type: str) -> str:
        if agent_type == "planner":
            return """
Você é um planejador de projetos de software experiente. Sua função é quebrar um objetivo de alto nível em uma lista de tarefas sequenciais, claras e acionáveis.

REGRAS DE SAÍDA:
1.  Sua resposta DEVE ser um bloco de código JSON e NADA MAIS.
2.  O JSON deve ser uma lista de objetos.
3.  Cada objeto representa uma tarefa e deve ter os seguintes campos:
    - "description": (string) Uma descrição clara e concisa do que a tarefa faz.
    - "tool_name": (string) O nome da ferramenta a ser usada para executar a tarefa. As ferramentas disponíveis são: "file_writer", "command_executor".
    - "tool_args": (object) Um objeto com os argumentos para a ferramenta.
        - Para "file_writer": precisa de "filename" e "content".
        - Para "command_executor": precisa de "command".
4.  As tarefas devem ser lógicas e sequenciais para construir o projeto passo a passo.
"""
        return ""

    @staticmethod
    def get_user_prompt(agent_type: str, **kwargs) -> str:
        if agent_type == "planner":
            return f"""
O objetivo do projeto é: "{kwargs.get('goal', '')}"

Por favor, crie um plano de tarefas em formato JSON para atingir este objetivo.

Exemplo de saída para um projeto simples:
```json
[
  {{
    "description": "Criar o arquivo principal da aplicação Flask.",
    "tool_name": "file_writer",
    "tool_args": {{
      "filename": "app.py",
      "content": "from flask import Flask\\n\\napp = Flask(__name__)\\n\\n@app.route('/hello')\\ndef hello():\\n    return \\"Hello, World!\\"\\n\\nif __name__ == '__main__':\\n    app.run(debug=True)\\n"
    }}
  }},
  {{
    "description": "Criar um arquivo requirements.txt com as dependências.",
    "tool_name": "file_writer",
    "tool_args": {{
      "filename": "requirements.txt",
      "content": "Flask\\n"
    }}
  }},
  {{
    "description": "Instalar as dependências do projeto.",
    "tool_name": "command_executor",
    "tool_args": {{
      "command": "pip install -r requirements.txt"
    }}
  }}
]
"""
        return ""

