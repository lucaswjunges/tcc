# src/agents/planner_agent.py (VERSÃO CORRIGIDA)

import json
from src.schemas.contracts import ProjectContext, Task
from src.services.llm_client import LLMClient
from src.services.observability_service import log
from src.agents.prompts.planner_prompts import FORMAT_JSON_SCHEMA, PLANNING_PROMPT_TEMPLATE

class PlannerAgent:
    def __init__(self, llm_client: LLMClient, config):
        self.llm_client = llm_client
        self.config = config
        self.model = config.model_mapping.planner

    def create_initial_plan(self, context: ProjectContext) -> list[Task]:
        log.info("PlannerAgent: Creating initial project plan.", project_id=str(context.project_id))
        
        system_prompt = PLANNING_PROMPT_TEMPLATE.format(json_schema=FORMAT_JSON_SCHEMA)
        user_prompt = f"O objetivo do projeto é: \"{context.project_goal}\". Por favor, crie o plano de tarefas."

        system_message = [{"role": "system", "content": system_prompt}]
        user_message = [{"role": "user", "content": user_prompt}]
        
        try:
            # AQUI ESTÁ A CORREÇÃO PRINCIPAL:
            # 1. Chamamos o método correto: invoke()
            # 2. Pegamos a resposta completa e extraímos o conteúdo dela.
            response = self.llm_client.invoke(
                model=self.model,
                messages=system_message + user_message
            )
            response_json_str = response['choices'][0]['message']['content']

            # Tentamos limpar o JSON, caso a LLM o embrulhe em ```json ... ```
            if response_json_str.startswith("```json"):
                response_json_str = "\n".join(response_json_str.split('\n')[1:-1])

            task_data = json.loads(response_json_str)
            
            if "tasks" in task_data:
                task_list = [Task(**task) for task in task_data["tasks"]]
                log.info(f"PlannerAgent: Successfully created a plan with {len(task_list)} tasks.", num_tasks=len(task_list))
                return task_list
            else:
                 log.error("PlannerAgent: JSON response from LLM is missing the 'tasks' key.", response_data=task_data)
                 return []

        except json.JSONDecodeError as e:
            log.error("PlannerAgent: Failed to decode JSON from LLM response.", error=str(e), response_str=response_json_str)
            raise
        except Exception as e:
            log.error("PlannerAgent: An unexpected error occurred while creating a plan.", error=str(e), exc_info=True)
            raise
