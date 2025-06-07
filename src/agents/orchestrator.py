# src/agents/orchestrator.py (VERSÃO FINAL COM FASE DE EXECUÇÃO)

import uuid

from src.schemas.contracts import SystemConfig, ProjectContext, ProjectState, Task
from src.services.context_manager import ContextManager
from src.services.llm_client import LLMClient
from src.services.toolbelt import Toolbelt
from src.services.observability_service import log

from src.agents.planner_agent import PlannerAgent
from src.agents.executor_agent import ExecutorAgent

class Orchestrator:
    def __init__(self,
                 project_id: uuid.UUID,
                 config: SystemConfig,
                 context_manager: ContextManager,
                 llm_client: LLMClient,
                 toolbelt: Toolbelt,
                ):
        self.project_id = project_id
        self.config = config
        self.context_manager = context_manager
        self.llm_client = llm_client
        self.toolbelt = toolbelt
        
        self.planner = PlannerAgent(llm_client, config)
        self.executor = ExecutorAgent(llm_client, toolbelt, config)
        
        log.info("Orchestrator initialized.", project_id=str(project_id))
    
    def run(self):
        log.info("Orchestrator run loop started.", project_id=str(self.project_id))
        try:
            context = self.context_manager.get_context()
            
            while context.current_state not in [ProjectState.completed, ProjectState.failed]:
                if context.current_state == ProjectState.planning:
                    self._execute_planning_phase()
                
                elif context.current_state == ProjectState.executing: # <-- NOVO BLOCO
                    self._execute_execution_phase()
                
                # Recarrega o contexto para obter o estado mais recente após uma fase.
                context = self.context_manager.get_context()

            log.info("Orchestrator run loop finished.")
            
        except Exception as e:
            log.critical("Orchestrator run failed. Halting execution.", error=str(e), exc_info=True)
            context = self.context_manager.get_context()
            context.current_state = ProjectState.failed
            log.info("Updating project status to 'failed'.")
        finally:
            # Salva o estado final do contexto, seja qual for.
            self.context_manager.save_context(self.context_manager.get_context())

    def _execute_planning_phase(self):
        context = self.context_manager.get_context()
        log.info("Project is in 'planning' state. Invoking PlannerAgent.")
        
        task_list : list[Task] = self.planner.create_initial_plan(context)
        
        if task_list:
            context.tasks = task_list
            context.current_state = ProjectState.executing # <-- MUDANÇA CRÍTICA
            log.info(f"Successfully planned {len(task_list)} tasks. Moving to state 'executing'.")
        else:
            log.warning("PlannerAgent returned no tasks. The project may be too simple or already complete.")
            context.current_state = ProjectState.completed # Se não há tarefas, o projeto acaba.
        
        self.context_manager.save_context(context)

    def _execute_execution_phase(self): # <-- FUNÇÃO INTEIRAMENTE NOVA
        context = self.context_manager.get_context()
        log.info("Project is in 'executing' state. Invoking ExecutorAgent.")
        
        # Encontra a próxima tarefa
        next_task = self.executor.find_next_task(context)

        if next_task:
            # Se encontrou uma tarefa, executa
            self.executor.execute_task(context, next_task)
            self.context_manager.save_context(context) # Salva o progresso
        else:
            # Se não há mais tarefas para executar, o projeto foi concluído
            log.info("All tasks have been completed. Moving to state 'completed'.")
            context.current_state = ProjectState.completed
            self.context_manager.save_context(context)

