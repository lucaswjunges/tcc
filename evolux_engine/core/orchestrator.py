import asyncio
from typing import Optional, List, Dict
from loguru import logger

# --- Imports Corrigidos para a Nova Estrutura ---
from evolux_engine.core.dependency_graph import DependencyGraph
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, TaskType, TaskStatus, ProjectStatus, ExecutionResult, ValidationResult
from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.llms.model_router import ModelRouter, TaskCategory
from evolux_engine.prompts.prompt_engine import PromptEngine
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService
from evolux_engine.services.backup_system import BackupSystem
from evolux_engine.services.criteria_engine import CriteriaEngine
from evolux_engine.security.security_gateway import SecurityGateway
from evolux_engine.execution.secure_executor import SecureExecutor
from evolux_engine.services.enterprise_observability import EnterpriseObservabilityService
from .planner import PlannerAgent
from .executor import TaskExecutorAgent
from .validator import SemanticValidatorAgent
from .critic import CriticAgent
from .intelligent_a2a_system import get_intelligent_a2a_system, IntelligentA2ASystem
from .metacognitive_engine import get_metacognitive_engine, MetaCognitiveEngine

class Orchestrator:
    """
    O Orchestrator gerencia o ciclo de vida completo de um projeto,
    coordenando os diferentes agentes (Planner, Executor, Validator)
    para alcançar o objetivo do projeto de forma iterativa.
    """

    def __init__(self, project_context: ProjectContext, config_manager: ConfigManager):
        self.project_context = project_context
        self.config_manager = config_manager
        self.agent_id = f"orchestrator-{self.project_context.project_id}"
        self.dependency_graph = DependencyGraph()

        # --- Bloco de Inicialização Corrigido ---
        provider = self.config_manager.get_global_setting("default_llm_provider", "openrouter")
        api_key = self.config_manager.get_api_key(provider)

        # Validação para garantir que a chave de API foi carregada
        if not api_key:
            raise ValueError(f"API Key para o provedor '{provider}' não foi encontrada. Verifique seu arquivo .env.")

        self.planner_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("planner")
        )
        self.executor_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("executor_content_gen")
        )
        self.validator_llm_client = LLMClient(
            provider=provider, 
            api_key=api_key, 
            model_name=self.config_manager.get_default_model_for("validator")
        )

        # O workspace path agora é um objeto Path no ProjectContext
        workspace_dir = self.project_context.workspace_path
        self.file_service = FileService(workspace_path=str(workspace_dir))
        self.shell_service = ShellService(workspace_path=str(workspace_dir))
        
        # Inicializar componentes conforme especificação
        self.model_router = ModelRouter()
        self.prompt_engine = PromptEngine()
        self.backup_system = BackupSystem()
        self.criteria_engine = CriteriaEngine()
        
        # Inicializar componentes de segurança e observabilidade
        from evolux_engine.security.security_gateway import SecurityLevel
        security_level_str = self.config_manager.get_global_setting("security_level", "strict")
        security_level = SecurityLevel(security_level_str)  # Convert string to enum
        self.security_gateway = SecurityGateway(security_level=security_level)
        self.secure_executor = SecureExecutor(security_gateway=self.security_gateway)
        # Precisamos de uma instância do AdvancedSystemConfig para o observability
        from evolux_engine.config.advanced_config import AdvancedSystemConfig
        advanced_config = AdvancedSystemConfig()
        self.observability = EnterpriseObservabilityService(config=advanced_config)
        
        # Passando o project_context para o planner agent
        self.planner_agent = PlannerAgent(
            context_manager=None,
            task_db=None,
            artifact_store=None,
            project_context=self.project_context
        )
        self.task_executor_agent = TaskExecutorAgent(
            executor_llm_client=self.executor_llm_client,
            project_context=self.project_context,
            file_service=self.file_service,
            shell_service=self.shell_service,
            security_gateway=self.security_gateway,
            secure_executor=self.secure_executor,
            model_router=self.model_router,
            agent_id=f"executor-{self.project_context.project_id}"
        )
        self.semantic_validator_agent = SemanticValidatorAgent(
            validator_llm_client=self.validator_llm_client,
            project_context=self.project_context,
            file_service=self.file_service
        )
        self.critic_agent = CriticAgent(
            critic_llm_client=self.validator_llm_client, # Reutilizando o LLM do validador por eficiência
            project_context=self.project_context
        )
        # --- Fim do Bloco de Inicialização Corrigido ---
        
        # 🚀 INICIALIZAR SISTEMA A2A INTELIGENTE
        self.intelligent_a2a = get_intelligent_a2a_system()
        self.a2a_enabled = self.config_manager.get_global_setting("enable_intelligent_a2a", True)
        
        # 🧠 INICIALIZAR MOTOR METACOGNITIVO
        self.metacognitive_engine = get_metacognitive_engine()
        self.metacognition_enabled = self.config_manager.get_global_setting("enable_metacognition", True)
        
        # Registrar agentes no sistema A2A inteligente
        if self.a2a_enabled:
            asyncio.create_task(self._initialize_intelligent_a2a())

        logger.info(f"Orchestrator (ID: {self.agent_id}) initialized for project '{self.project_context.project_name}' with Intelligent A2A: {'ENABLED' if self.a2a_enabled else 'DISABLED'} | Metacognition: {'ENABLED' if self.metacognition_enabled else 'DISABLED'}.")

    async def _get_runnable_tasks(self) -> List[Task]:
        """
        Obtém todas as tarefas PENDING cujas dependências foram concluídas,
        utilizando o grafo de dependências.
        """
        runnable_tasks = self.dependency_graph.get_runnable_tasks()
        if runnable_tasks:
            logger.info(f"Orchestrator: {len(runnable_tasks)} tasks ready for parallel execution from the graph.")
        return runnable_tasks

    async def run_project_cycle(self) -> ProjectStatus:
        """
        Executa o ciclo principal do projeto: planejar (se necessário), executar tarefas, validar.
        🚀 MODO INTELIGENTE A2A + 🧠 METACOGNIÇÃO ATIVADOS
        """
        logger.info(f"Orchestrator (ID: {self.agent_id}): Starting project cycle for '{self.project_context.project_name}'.")

        # 🧠 METACOGNIÇÃO: Auto-reflexão sobre estratégia de execução
        if self.metacognition_enabled:
            execution_context = {
                "project_complexity": len(self.project_context.task_queue),
                "problem_type": "software_engineering",
                "available_agents": 3 if self.a2a_enabled else 1,
                "resources": {"a2a_agents": 3 if self.a2a_enabled else 0}
            }
            
            # Escolher estratégia de pensamento baseada em auto-reflexão
            thinking_strategy = await self.metacognitive_engine.adapt_thinking_strategy(execution_context)
            logger.info(f"🤔 METACOGNITION: Selected strategy: {thinking_strategy.value}")
            
            # Questionar próprias suposições sobre abordagem
            self_questions = await self.metacognitive_engine.question_own_assumptions({
                "chosen_strategy": thinking_strategy.value,
                "problem_definition": self.project_context.project_goal
            })
            for question in self_questions[:3]:  # Log as 3 primeiras questões
                logger.info(f"❓ METACOGNITION: {question}")

        # 🧠 EXECUÇÃO INTELIGENTE A2A - DECISÃO AUTOMÁTICA
        if self.a2a_enabled and len(self.project_context.task_queue) >= 3:
            logger.info("🚀 INTELLIGENT A2A MODE: Activating advanced collaborative execution")
            return await self._run_intelligent_a2a_cycle()
        else:
            logger.info("🔄 TRADITIONAL MODE: Executing classic P.O.D.A. cycle")
            return await self._run_traditional_cycle()

    async def _run_traditional_cycle(self) -> ProjectStatus:
        """Executa ciclo tradicional P.O.D.A."""
        # Fase 1: Planejamento e Revisão Crítica
        if not self.project_context.task_queue:
            logger.info("Orchestrator: Initial Planning Phase.")
            self.project_context.status = ProjectStatus.PLANNING
            await self.project_context.save_context()

            plan_successful = await self.planner_agent.generate_initial_plan()
            if not plan_successful:
                logger.error("Initial planning failed. Aborting.")
                self.project_context.status = ProjectStatus.PLANNING_FAILED
                await self.project_context.save_context()
                return self.project_context.status

            # A revisão do plano agora é um passo bloqueante e crítico
            logger.info("Orchestrator: Critical Plan Review Phase.")
            plan_review_report = await self.critic_agent.review_plan(self.project_context.task_queue)
            logger.info(f"🕵️ Plan Review Completed: Score={plan_review_report['score']:.2f}, Approved={plan_review_report['is_approved']}")

            if not plan_review_report['is_approved']:
                logger.error(f"Plan rejected by CriticAgent. Issues: {plan_review_report['potential_issues']}. Aborting execution.")
                # Idealmente, aqui deveria haver um ciclo de replanejamento com o feedback.
                # Por agora, vamos falhar para evitar a execução de um plano ruim.
                self.project_context.status = ProjectStatus.PLANNING_FAILED
                await self.project_context.save_context()
                return self.project_context.status

            logger.success("Plan approved by CriticAgent. Proceeding to execution.")
            self.project_context.status = ProjectStatus.PLANNED
            await self.project_context.save_context()

        # Construir o grafo de dependências a partir da task_queue do projeto
        for task in self.project_context.task_queue:
            self.dependency_graph.add_task(task)
        
        # Loop principal P.O.D.A. (Plan, Orient, Decide, Act)
        max_iterations = self.project_context.engine_config.max_project_iterations
        while not self.dependency_graph.is_completed() and self.project_context.metrics.total_iterations < max_iterations:
            self.project_context.metrics.total_iterations += 1
            iteration = self.project_context.metrics.total_iterations
            logger.info(f"--- Starting P.O.D.A. Cycle #{iteration} ---")
            
            # P.O.D.A. PHASE 1 & 2: PLAN & ORIENT (Planejar e Orientar)
            # Obter todas as tarefas prontas para execução paralela
            runnable_tasks = await self._get_runnable_tasks()
            if not runnable_tasks:
                logger.info("No runnable tasks found. Checking for project completion.")
                break

            # Marcar todas as tarefas como IN_PROGRESS no grafo e no contexto
            for task in runnable_tasks:
                self.dependency_graph.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
            await self.project_context.save_context() # Salva o estado geral

            # P.O.D.A. PHASE 3 & 4: DECIDE & ACT (Decidir e Agir)
            # Criar e executar as corrotinas de execução de tarefas em paralelo
            execution_coroutines = [self._execute_and_process_task(task) for task in runnable_tasks]
            results = await asyncio.gather(*execution_coroutines, return_exceptions=True)

            # Processar resultados e atualizar o contexto
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Unexpected error during parallel task execution: {result}")
                    # Aqui, precisaríamos de uma forma de mapear o erro de volta para a tarefa
                    # Por enquanto, vamos logar e continuar. Uma implementação mais robusta
                    # retornaria uma tupla (task_id, result) de _execute_and_process_task.
                # O processamento do resultado da tarefa (sucesso/falha) já é feito dentro de _execute_and_process_task
            
            await self.project_context.save_context()

        # Fase 3: Conclusão e Entrega conforme especificação
        logger.info("🏁 CONCLUSION: Starting final project verification")
        
        # 1. Verificação Final (CriteriaEngine)
        completion_report = self.criteria_engine.check_completion(self.project_context)
        
        # 2. Relatório e Backup (BackupSystem)
        artifacts_dir = str(self.project_context.workspace_path / "artifacts")
        backup_description = f"Backup final - Status: {completion_report.status.value}"
        try:
            backup_path = self.backup_system.create_snapshot(
                self.project_context, 
                artifacts_dir, 
                backup_description
            )
            logger.info(f"📦 Final backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create final backup: {e}")

        # 3. Determinar status final baseado na verificação
        if completion_report.status.value == "completed":
            final_status = ProjectStatus.COMPLETED_SUCCESSFULLY
        elif completion_report.status.value in ["partially_completed"]:
            final_status = ProjectStatus.COMPLETED_WITH_FAILURES
        else:
            final_status = ProjectStatus.COMPLETED_WITH_FAILURES

        # Log do relatório final
        logger.info(f"📊 Final Completion Report: status={completion_report.status.value}, score={completion_report.overall_score}, summary={completion_report.summary}, recommendations={completion_report.recommendations}")

        self.project_context.status = final_status
        await self.project_context.save_context()
        logger.info(f"🎯 Project cycle finished with status: {self.project_context.status.value}")
        return self.project_context.status

    async def _execute_and_process_task(self, task: Task):
        """
        Encapsula a lógica completa de execução e processamento de uma única tarefa.
        """
        logger.info(f"⚡ ACT: Starting execution of task {task.task_id}: {task.description}")
        
        # Métricas de observabilidade
        start_time = asyncio.get_event_loop().time()
        if self.observability:
            await self.observability.record_task_start(task.task_id, task.type.value)

        # Executar a tarefa
        execution_result = await self.task_executor_agent.execute_task(task)

        # Validar o resultado
        validation_result = await self.semantic_validator_agent.validate_task_output(task, execution_result)
        
        # Métricas de observabilidade
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        if self.observability:
            await self.observability.record_task_completion(
                task.task_id, 
                validation_result.validation_passed,
                execution_time,
                execution_result.exit_code
            )

        # Processar o resultado da validação e decidir o próximo passo para a tarefa
        if validation_result.validation_passed:
            logger.success(f"Task {task.task_id} completed and validated successfully!")
            self.dependency_graph.update_task_status(task.task_id, TaskStatus.COMPLETED)
            task.status = TaskStatus.COMPLETED
            self.project_context.completed_tasks.append(task)

            # Se a tarefa foi criar ou modificar um arquivo, disparar a revisão do código
            if task.type in [TaskType.CREATE_FILE, TaskType.MODIFY_FILE] and hasattr(task.details, 'file_path'):
                asyncio.create_task(self.run_code_review(task))
        else:
            issues_str = ', '.join(validation_result.identified_issues) if validation_result.identified_issues else "Unspecified reasons"
            logger.warning(f"Validation for task {task.task_id} failed: {issues_str}")
            task.retries += 1
            if task.retries >= task.max_retries:
                logger.error(f"Task {task.task_id} exceeded maximum retries. Triggering replanning.")
                
                # Coletar feedback de erro para o planejador
                error_feedback = (
                    f"A tarefa '{task.description}' falhou após {task.max_retries} tentativas. "
                    f"Últimos erros: {', '.join(validation_result.identified_issues)}"
                )

                # Invocar o planejador para obter um novo plano para a tarefa falha
                new_tasks = await self.planner_agent.replan_task(task, error_feedback)
                
                if new_tasks:
                    logger.info(f"Replanning generated {len(new_tasks)} new task(s).")
                    # Marcar a tarefa antiga como falha e removê-la do grafo ativo
                    self.dependency_graph.update_task_status(task.task_id, TaskStatus.FAILED)
                    task.status = TaskStatus.FAILED
                    self.project_context.failed_tasks.append(task)
                    
                    # Adicionar as novas tarefas ao grafo e ao contexto do projeto
                    for new_task in new_tasks:
                        self.dependency_graph.add_task(new_task)
                        self.project_context.task_queue.append(new_task)
                else:
                    logger.error(f"Replanning for task {task.task_id} failed. Marking as critical failure.")
                    self.dependency_graph.update_task_status(task.task_id, TaskStatus.FAILED)
                    task.status = TaskStatus.FAILED
                    self.project_context.failed_tasks.append(task)
            else:
                logger.info(f"Task {task.task_id} will be retried (attempt {task.retries}/{task.max_retries}).")
                self.dependency_graph.update_task_status(task.task_id, TaskStatus.PENDING)
                task.status = TaskStatus.PENDING
        
        # Sincronizar a task_queue principal
        self.project_context.task_queue = [
            t for t in self.project_context.task_queue 
            if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]

    # ============================================================================
    # 🕵️ MÉTODOS DE REVISÃO CRÍTICA (CRITIC AGENT)
    # ============================================================================

    async def run_plan_review(self):
        """Executa a revisão do plano inicial em segundo plano."""
        logger.info("🕵️ CriticAgent: Starting plan review in the background...")
        report = await self.critic_agent.review_plan(self.project_context.task_queue)
        logger.info(f"🕵️ Plan Review Completed: Score={report['score']:.2f}, Approved={report['is_approved']}")
        if not report['is_approved']:
            logger.warning(f"Issues identified in the plan by CriticAgent: {report['potential_issues']}")
        # O feedback poderia ser armazenado no ProjectContext para o Planner usar no futuro.

    async def run_code_review(self, task: Task):
        """Executa a revisão de um artefato de código em segundo plano."""
        logger.info(f"🕵️ CriticAgent: Starting code review for task {task.task_id}...")
        file_path = task.details.file_path
        relative_file_path = f"artifacts/{file_path}"
        
        try:
            content = self.file_service.read_file(relative_file_path)
            artifact_state = self.project_context.artifacts_state.get(relative_file_path)
            if content and artifact_state:
                report = await self.critic_agent.review_code_artifact(artifact_state, content)
                logger.info(f"🕵️ Code Review Completed ({file_path}): Score={report['score']:.2f}, Approved={report['is_approved']}")
                if not report['is_approved']:
                    logger.warning(f"Issues in the code of '{file_path}': {report['potential_issues']}")
                # Armazenar o feedback para refinamento futuro
            else:
                logger.warning(f"Could not read content or artifact state for review: {file_path}")
        except Exception as e:
            logger.error(f"Error during code review for {file_path}: {e}")


    # ============================================================================
    # 🚀 MÉTODOS DE EXECUÇÃO INTELIGENTE A2A
    # ============================================================================

    async def _initialize_intelligent_a2a(self):
        """Inicializa sistema A2A inteligente com os agentes"""
        try:
            logger.info("🧠 Initializing intelligent A2A system...")
            
            # Registrar agentes principais no sistema inteligente
            await self.intelligent_a2a.register_intelligent_agent(
                agent_id=f"planner_{self.project_context.project_id}",
                initial_capabilities={
                    "performance_metrics": {"planning_speed": 1.0, "plan_quality": 0.9},
                    "max_concurrent_tasks": 3,
                    "expertise_level": {"CREATE_FILE": 0.9, "EXECUTE_COMMAND": 0.7}
                }
            )
            
            await self.intelligent_a2a.register_intelligent_agent(
                agent_id=f"executor_{self.project_context.project_id}",
                initial_capabilities={
                    "performance_metrics": {"execution_speed": 1.2, "success_rate": 0.95},
                    "max_concurrent_tasks": 5,
                    "expertise_level": {"CREATE_FILE": 0.95, "EXECUTE_COMMAND": 0.9}
                }
            )
            
            await self.intelligent_a2a.register_intelligent_agent(
                agent_id=f"validator_{self.project_context.project_id}",
                initial_capabilities={
                    "performance_metrics": {"validation_accuracy": 0.98, "response_time": 0.8},
                    "max_concurrent_tasks": 4,
                    "expertise_level": {"CREATE_FILE": 0.8, "EXECUTE_COMMAND": 0.85}
                }
            )
            
            logger.info("✅ Intelligent A2A system initialized with 3 specialized agents")
            
        except Exception as e:
            logger.error(f"❌ Error in A2A initialization: {e}")
            self.a2a_enabled = False

    async def _run_intelligent_a2a_cycle(self) -> ProjectStatus:
        """
        🚀 EXECUÇÃO INTELIGENTE A2A
        Usa colaboração avançada, especialização dinâmica e fault tolerance
        """
        logger.info("🚀 STARTING INTELLIGENT A2A EXECUTION")
        
        try:
            # Fase 1: Planejamento Colaborativo (se necessário)
            if not self.project_context.task_queue:
                logger.info("🧠 Collaborative Planning Phase A2A")
                self.project_context.status = ProjectStatus.PLANNING
                await self.project_context.save_context()
                
                # Usar planner especializado
                plan_successful = await self._execute_collaborative_planning()
                if not plan_successful:
                    logger.error("❌ Collaborative planning failed")
                    self.project_context.status = ProjectStatus.PLANNING_FAILED
                    await self.project_context.save_context()
                    return self.project_context.status
                
                self.project_context.status = ProjectStatus.PLANNED
                await self.project_context.save_context()
            
            # Fase 2: Execução Inteligente via Pipeline Colaborativo
            logger.info("⚡ Starting Intelligent Collaborative Pipeline")
            self.project_context.status = ProjectStatus.EXECUTING
            await self.project_context.save_context()
            
            # 🧠 METACOGNIÇÃO: Integrar metacognição com sistema A2A
            if self.metacognition_enabled:
                logger.info("🧠 Integrating metacognition with collaborative A2A system")
                
                # Integração bidirecional: metacognição <-> A2A
                await self.intelligent_a2a.integrate_metacognitive_engine(self.metacognitive_engine)
                a2a_integration = await self.metacognitive_engine.integrate_with_a2a_system(self.intelligent_a2a)
                
                logger.info(f"🤝 A2A metacognition integrated - Effectiveness: {a2a_integration['effectiveness_score']:.2f}")
            
            # Executar projeto via sistema inteligente A2A
            pipeline_id = await self.intelligent_a2a.execute_intelligent_project(
                tasks=self.project_context.task_queue,
                project_name=self.project_context.project_name
            )
            
            logger.info(f"🎉 Collaborative pipeline '{pipeline_id}' executed!")
            
            # Fase 3: Validação Inteligente Distribuída
            logger.info("🔍 Executing Distributed Intelligent Validation")
            validation_success = await self._execute_intelligent_validation()
            
            # Fase 4: Geração de Relatório de Inteligência
            intelligence_report = await self.intelligent_a2a.generate_intelligence_report()
            logger.info(f"📊 A2A Intelligence Report generated, agents: {intelligence_report['system_overview']['total_agents']}, pipelines: {intelligence_report['system_overview']['active_pipelines']}")
            
            # Determinar status final
            if validation_success:
                self.project_context.status = ProjectStatus.COMPLETED_SUCCESSFULLY
                logger.info("🎊 PROJECT COMPLETED SUCCESSFULLY VIA INTELLIGENT A2A!")
            else:
                self.project_context.status = ProjectStatus.COMPLETED_WITH_FAILURES
                logger.warning("⚠️ Project completed with some failures")
            
            await self.project_context.save_context()
            return self.project_context.status
            
        except Exception as e:
            logger.error(f"❌ Error in intelligent A2A execution: {e}")
            # Fallback para execução tradicional
            logger.info("🔄 Fallback: Executing traditional mode")
            return await self._run_traditional_cycle()

    async def _execute_collaborative_planning(self) -> bool:
        """Executa planejamento colaborativo com especialização"""
        try:
            logger.info("🧠 Executing specialized collaborative planning")
            
            # Verificar se o planner foi especializado
            await self.intelligent_a2a.analyze_and_specialize_agents()
            
            # Executar planejamento tradicional com melhorias A2A
            plan_successful = await self.planner_agent.generate_initial_plan()
            
            if plan_successful and len(self.project_context.task_queue) >= 5:
                # Projeto complexo - aplicar otimizações A2A
                logger.info("📈 Complex project detected - applying A2A optimizations")
                
                # Distribuir tarefas inteligentemente
                distribution = await self.intelligent_a2a.intelligent_task_distribution(
                    self.project_context.task_queue
                )
                
                logger.info(f"⚖️ Intelligent distribution: {len(distribution)} agents involved")
            
            return plan_successful
            
        except Exception as e:
            logger.error(f"Error in collaborative planning: {e}")
            return False

    async def _execute_intelligent_validation(self) -> bool:
        """Executa validação inteligente distribuída"""
        try:
            logger.info("🔍 Executing distributed intelligent validation")
            
            # Simular validação distribuída (implementação completa usaria validação real)
            validation_tasks = []
            
            # Validar cada tarefa completada
            for task in self.project_context.completed_tasks:
                if task.status == TaskStatus.COMPLETED:
                    # Executar validação com fault tolerance
                    validation_result = await self.intelligent_a2a.ensure_fault_tolerant_execution(
                        task=task,
                        primary_agent=f"validator_{self.project_context.project_id}"
                    )
                    validation_tasks.append(validation_result)
            
            # Calcular taxa de sucesso
            if validation_tasks:
                success_rate = sum(validation_tasks) / len(validation_tasks)
                logger.info(f"📊 Distributed validation: {success_rate:.1%} success rate")
                return success_rate >= 0.8  # 80% de sucesso mínimo
            
            return True  # Se não há tarefas para validar, considerar sucesso
            
        except Exception as e:
            logger.error(f"Error in intelligent validation: {e}")
            return False

    async def get_a2a_intelligence_report(self) -> Dict:
        """Obtém relatório completo da inteligência A2A do projeto"""
        if not self.a2a_enabled:
            return {"error": "A2A system is not enabled"}
        
        try:
            # Gerar relatório de inteligência
            intelligence_report = await self.intelligent_a2a.generate_intelligence_report()
            
            # 🧠 ADICIONAR INSIGHTS METACOGNITIVOS AO RELATÓRIO
            if self.metacognition_enabled:
                # Gerar modelo de auto-consciência
                self_model = await self.metacognitive_engine.generate_self_model()
                
                # Avaliar capacidades cognitivas
                cognitive_profile = await self.metacognitive_engine.evaluate_own_capabilities()
                
                intelligence_report["metacognitive_insights"] = {
                    "self_awareness_model": self_model,
                    "cognitive_capabilities": {
                        "analytical_strength": cognitive_profile.analytical_strength,
                        "creative_strength": cognitive_profile.creative_strength,
                        "collaborative_ability": cognitive_profile.collaborative_ability,
                        "meta_awareness": cognitive_profile.meta_awareness
                    },
                    "identified_limitations": [limit.value for limit in cognitive_profile.identified_limits],
                    "strength_areas": cognitive_profile.strength_areas,
                    "improvement_areas": cognitive_profile.improvement_areas
                }
            
            # Adicionar métricas específicas do projeto
            project_metrics = {
                "project_id": self.project_context.project_id,
                "project_name": self.project_context.project_name,
                "total_tasks": len(self.project_context.task_queue) + len(self.project_context.completed_tasks),
                "completed_tasks": len(self.project_context.completed_tasks),
                "project_status": self.project_context.status.value,
                "execution_mode": "INTELLIGENT_A2A" + (" + METACOGNITION" if self.metacognition_enabled else "")
            }
            
            intelligence_report["project_metrics"] = project_metrics
            
            return intelligence_report
            
        except Exception as e:
            logger.error(f"Error generating A2A report: {e}")
            return {"error": str(e)}

    def is_a2a_enabled(self) -> bool:
        """Verifica se o sistema A2A inteligente está habilitado"""
        return self.a2a_enabled

    async def enable_a2a_mode(self):
        """Habilita modo A2A inteligente dinamicamente"""
        if not self.a2a_enabled:
            self.a2a_enabled = True
            await self._initialize_intelligent_a2a()
            logger.info("🚀 Intelligent A2A mode enabled dynamically")

    async def disable_a2a_mode(self):
        """Desabilita modo A2A inteligente"""
        if self.a2a_enabled:
            self.a2a_enabled = False
            logger.info("🔄 A2A mode disabled - using traditional execution")

    def is_metacognition_enabled(self) -> bool:
        """Verifica se o sistema metacognitivo está habilitado"""
        return self.metacognition_enabled

    async def enable_metacognition(self):
        """Habilita metacognição dinamicamente"""
        if not self.metacognition_enabled:
            self.metacognition_enabled = True
            logger.info("🧠 Metacognition enabled dynamically")

    async def disable_metacognition(self):
        """Desabilita metacognição"""
        if self.metacognition_enabled:
            self.metacognition_enabled = False
            logger.info("🔄 Metacognition disabled")

    async def get_metacognitive_insights(self) -> Dict:
        """Obtém insights metacognitivos do sistema"""
        if not self.metacognition_enabled:
            return {"error": "Metacognition is not enabled"}
        
        try:
            # Gerar modelo de auto-consciência
            self_model = await self.metacognitive_engine.generate_self_model()
            
            # Avaliar capacidades cognitivas
            cognitive_profile = await self.metacognitive_engine.evaluate_own_capabilities()
            
            # Questionar próprias suposições sobre projeto atual
            project_questions = await self.metacognitive_engine.question_own_assumptions({
                "problem_definition": self.project_context.project_goal,
                "current_approach": "software_development"
            })
            
            return {
                "self_awareness_model": self_model,
                "cognitive_profile": {
                    "analytical_strength": cognitive_profile.analytical_strength,
                    "creative_strength": cognitive_profile.creative_strength,
                    "collaborative_ability": cognitive_profile.collaborative_ability,
                    "meta_awareness": cognitive_profile.meta_awareness,
                    "identified_limits": [limit.value for limit in cognitive_profile.identified_limits],
                    "strength_areas": cognitive_profile.strength_areas,
                    "improvement_areas": cognitive_profile.improvement_areas
                },
                "self_reflection_questions": project_questions,
                "thinking_process_analyses": len(self.metacognitive_engine.process_analyses),
                "meta_insights_count": len(self.metacognitive_engine.insights)
            }
            
        except Exception as e:
            logger.error(f"Error generating metacognitive insights: {e}")
            return {"error": str(e)}
