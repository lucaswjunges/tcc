# src/agents/planner.py
from src.services.llm_client import LLMClient
from src.models import ProjectContext
from src.schemas.contracts import Plan

# ... (outras importações)

class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _construct_prompt(self, goal: str) -> list:
        # ATUALIZE O PROMPT AQUI
        system_prompt = """
Você é um planejador especialista em um sistema de agentes de IA. Seu trabalho é pegar um objetivo de alto nível e quebrá-lo em um plano de tarefas detalhado e sequencial que pode ser executado por um agente Executor.

Regras:
1.  **Formato JSON:** Sua resposta DEVE ser um único bloco de código JSON, e nada mais.
2.  **Estrutura do JSON:** O JSON deve seguir o esquema { "goal": "...", "tasks": [...] }.
3.  **Tarefas:** Cada tarefa no array `tasks` deve ter `id`, `description`, `tool`, `parameters`, e `dependencies`.
4.  **Ferramentas Disponíveis:** O agente Executor tem acesso APENAS às seguintes ferramentas:
    *   `write_file(file_path: str, content: str)`: Escreve ou sobrescreve um arquivo no workspace.
    *   `read_file(file_path: str) -> str`: Lê o conteúdo de um arquivo.
    *   `list_files(sub_dir: str = ".") -> list[str]`: Lista arquivos em um subdiretório do workspace.
    *   `run_shell_command(command: str) -> str`: Executa um comando de shell no diretório do projeto. Essencial para instalar dependências (ex: `pip install -r requirements.txt`) e rodar scripts (ex: `python3 app.py`). A saída do comando será retornada.
    *   `finish()`: Finaliza o projeto. Use esta ferramenta como a ÚLTIMA tarefa do plano.
5.  **Pensamento Sequencial:** Crie tarefas pequenas e lógicas. Use o campo `dependencies` para garantir a ordem correta. Por exemplo, um arquivo deve ser criado antes de poder ser lido.
6.  **Conteúdo é Essencial:** Para a ferramenta `write_file`, sempre forneça o conteúdo completo no parâmetro `content`. Não crie arquivos vazios.
7.  **Ciclo de Desenvolvimento:** Um fluxo de trabalho típico é: 1. Escrever o código (`write_file`). 2. Escrever os requisitos (`write_file` para requirements.txt). 3. Instalar os requisitos (`run_shell_command` com pip). 4. Executar o código (`run_shell_command` com python).
"""
        user_prompt = f"Crie um plano JSON para atingir o seguinte objetivo: {goal}"
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    # O resto do arquivo permanece o mesmo...

    def create_plan(self, context: ProjectContext, model: str) -> Plan:
        log.info("Planner agent starting plan creation.", goal=context.goal)
        messages = self._construct_prompt(context.goal)
        
        raw_response = self.llm_client.chat_completion(model=model, messages=messages)
        log.info("Raw response from LLM received.", raw_response=raw_response)
        
        try:
            # Bug fix: a resposta do LLM pode estar dentro de um bloco de código JSON
            if "```json" in raw_response:
                clean_response = raw_response.split("```json\n")[1].split("```")[0]
            else:
                clean_response = raw_response

            plan_data = json.loads(clean_response)
            plan = Plan(**plan_data)
            log.info("Plan parsed and validated successfully.", plan_tasks=len(plan.tasks))
            return plan
        except (json.JSONDecodeError, TypeError, IndexError) as e:
            log.error("Failed to parse or validate plan from LLM response.", error=str(e), raw_response=raw_response)
            raise ValueError("Failed to create a valid plan from LLM response.")

