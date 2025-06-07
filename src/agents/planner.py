# src/agents/planner.py

import json
from ..services.llm_client import LLMClient
from ..services.observability_service import log
from ..schemas.contracts import Plan
from .planner_prompts import PLANNER_SYSTEM_PROMPT

class Planner:
    """
    O Agente Planner é responsável por receber um objetivo de alto nível
    e decompô-lo em um plano de tarefas executáveis passo a passo em formato JSON.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def create_plan(self, goal: str, model: str) -> Plan:
        log.info("Planner agent starting plan creation.", goal=goal)
        
        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": f"O objetivo final do projeto é: {goal}"}
        ]
        
        try:
            response_text = self.llm_client.chat_completion(
                model=model,
                messages=messages
            )
            
            # Limpeza básica para garantir que estamos lidando com um objeto JSON
            # O LLM às vezes envolve o JSON em blocos de código markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            log.info("Raw response from LLM received.", raw_response=response_text)
            
            plan_data = json.loads(response_text)
            plan = Plan(**plan_data)
            
            log.info("Plan parsed and validated successfully.", plan_tasks=len(plan.tasks))
            return plan

        except json.JSONDecodeError as e:
            log.error("Failed to decode JSON from LLM response.", error=str(e), raw_response=response_text)
            raise ValueError(f"Planner response could not be decoded: {e}")
        except Exception as e:
            log.error("An unexpected error occurred during plan creation.", error=str(e), exc_info=True)
            raise
