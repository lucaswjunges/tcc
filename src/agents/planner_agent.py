# src/agents/planner_agent.py (VERSÃO CORRETA COM LÓGICA DE PÓS-PROCESSAMENTO)

import uuid
import json

from src.schemas.contracts import SystemConfig, ProjectContext, Task
from src.services.llm_client import LLMClient
from src.services.observability_service import log
from src.agents.prompts import planner_prompts

class PlannerAgent:
    def __init__(self, llm_client: LLMClient, config: SystemConfig):
        self.llm_client = llm_client
        self.model = config.model_mapping.planner

    def create_initial_plan(self, context: ProjectContext) -> list[Task]:
        log.info(f"PlannerAgent: Creating initial project plan.", project_id=str(context.project_id))
        
        system_message = [{"role": "system", "content": planner_prompts.SYSTEM_PROMPT}]
        user_message = [{"role": "user", "content": planner_prompts.USER_PROMPT.format(goal=context.project_goal)}]
        
        try:
            log.info("Invoking LLM.", model=self.model, num_messages=len(system_message + user_message))
            response = self.llm_client.invoke(
                model=self.model,
                messages=system_message + user_message
            )
            log.info("LLM invocation successful.", model=self.model)

            response_json = response.json()
            llm_response_content = response_json["choices"][0]["message"]["content"]
            task_data = json.loads(llm_response_content)

            # =========================================================================
            # LÓGICA DE PÓS-PROCESSAMENTO PARA GARANTIR VALIDAÇÃO
            # =========================================================================
            processed_tasks = []
            previous_task_id = None
            
            for task_dict in task_data["tasks"]:
                new_id = uuid.uuid4()
                dependencies = [previous_task_id] if previous_task_id else []

                processed_task = Task(
                    id=new_id,
                    description=task_dict.get("description", "No description provided"),
                    type=task_dict.get("type", "unknown"),
                    dependencies=dependencies,
                    acceptance_criteria=task_dict.get("acceptance_criteria", [])
                )
                processed_tasks.append(processed_task)
                
                previous_task_id = new_id
            # =========================================================================

            if not processed_tasks:
                log.warning("LLM returned a plan with no tasks.")
                return []
                
            return processed_tasks

        except Exception as e:
            log.error(f"PlannerAgent: An unexpected error occurred while creating a plan.", error=str(e), exc_info=True)
            raise e
