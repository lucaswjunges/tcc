# src/agents/planner_agent.py (VERSÃO CORRIGIDA)
import json
from src.services.llm_client import LLMClient
from src.services.observability_service import log
from src.models.project_context import ProjectContext
from src.agents.prompts import Prompts

class PlannerAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def create_initial_plan(self, context: ProjectContext) -> list[dict]:
        log.info("PlannerAgent: Creating initial project plan.", project_id=context.project_id)
        
        system_message = Prompts.get_system_prompt("planner")
        user_message = Prompts.get_user_prompt(
            "planner",
            goal=context.project_goal,
            tech_stack="",  # Podemos adicionar isso ao contexto no futuro
            project_type=context.project_type
        )
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        try:
            log.info("Invoking LLM.", model=context.config.model_mapping.planner, num_messages=len(messages))
            
            # --- A CORREÇÃO ESTÁ AQUI ---
            # Troquei .invoke() por .call_llm() para combinar com o nosso LLMClient
            response_text = self.llm_client.call_llm(
                model=context.config.model_mapping.planner,
                messages=messages
            )
            # ---------------------------

            log.info(f"PlannerAgent: Received plan from LLM.", raw_response=response_text)
            
            # Extrair o JSON do bloco de código
            json_block = response_text.strip().split("```json\n")[1].split("\n```")[0]
            plan = json.loads(json_block)
            
            log.info("PlannerAgent: Plan parsed successfully.", num_tasks=len(plan))
            return plan

        except (json.JSONDecodeError, IndexError) as e:
            log.error("PlannerAgent: Failed to parse plan from LLM response.", error_message=str(e), raw_response=response_text, exc_info=True)
            raise
        except Exception as e:
            log.error("PlannerAgent: An unexpected error occurred while creating a plan.", error_message=str(e), exc_info=True)
            raise

