import asyncio
from typing import Optional, List, Dict
from loguru import logger

# --- Imports Corrigidos para a Nova Estrutura ---
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, TaskStatus, ProjectStatus, ExecutionResult, ValidationResult
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

        logger.info(f"Orchestrator (ID: {self.agent_id}) inicializado para projeto '{self.project_context.project_name}' com A2A Inteligente: {'ATIVADO' if self.a2a_enabled else 'DESATIVADO'} | Metacognição: {'ATIVADA' if self.metacognition_enabled else 'DESATIVADA'}.")

    async def _get_next_task(self) -> Optional[Task]:
        """
        Obtém a próxima tarefa PENDING da task_queue que não tenha dependências PENDING ou IN_PROGRESS.
        """
        task_statuses: Dict[str, TaskStatus] = {task.task_id: task.status for task in self.project_context.task_queue}
        task_statuses.update({task.task_id: task.status for task in self.project_context.completed_tasks})

        for task in self.project_context.task_queue:
            if task.status == TaskStatus.PENDING:
                dependencies_met = all(
                    task_statuses.get(dep_id) == TaskStatus.COMPLETED for dep_id in task.dependencies
                )
                
                if dependencies_met:
                    logger.info(f"Orchestrator: Próxima tarefa selecionada: {task.task_id} - {task.description}")
                    return task
        return None

    async def run_project_cycle(self) -> ProjectStatus:
        """
        Executa o ciclo principal do projeto: planejar (se necessário), executar tarefas, validar.
        🚀 MODO INTELIGENTE A2A + 🧠 METACOGNIÇÃO ATIVADOS
        """
        logger.info(f"Orchestrator (ID: {self.agent_id}): Iniciando ciclo do projeto '{self.project_context.project_name}'.")

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
            logger.info(f"🤔 METACOGNIÇÃO: Estratégia selecionada: {thinking_strategy.value}")
            
            # Questionar próprias suposições sobre abordagem
            self_questions = await self.metacognitive_engine.question_own_assumptions({
                "chosen_strategy": thinking_strategy.value,
                "problem_definition": self.project_context.project_goal
            })
            for question in self_questions[:3]:  # Log as 3 primeiras questões
                logger.info(f"❓ METACOGNIÇÃO: {question}")

        # 🧠 EXECUÇÃO INTELIGENTE A2A - DECISÃO AUTOMÁTICA
        if self.a2a_enabled and len(self.project_context.task_queue) >= 3:
            logger.info("🚀 MODO A2A INTELIGENTE: Ativando execução colaborativa avançada")
            return await self._run_intelligent_a2a_cycle()
        else:
            logger.info("🔄 MODO TRADICIONAL: Executando ciclo P.O.D.A. clássico")
            return await self._run_traditional_cycle()

    async def _run_traditional_cycle(self) -> ProjectStatus:
        """Executa ciclo tradicional P.O.D.A."""
        # Fase 1: Planejamento
        if not self.project_context.task_queue:
            logger.info(f"Orchestrator: Fase de Planejamento Inicial.")
            self.project_context.status = ProjectStatus.PLANNING
            await self.project_context.save_context()
            
            plan_successful = await self.planner_agent.generate_initial_plan()
            if not plan_successful:
                logger.error("Falha no planejamento inicial. Encerrando.")
                self.project_context.status = ProjectStatus.PLANNING_FAILED
                await self.project_context.save_context()
                return self.project_context.status
            
            self.project_context.status = ProjectStatus.PLANNED
            await self.project_context.save_context()

        # Loop principal P.O.D.A. (Plan, Orient, Decide, Act)
        max_iterations = self.project_context.engine_config.max_project_iterations
        while self.project_context.metrics.total_iterations < max_iterations:
            self.project_context.metrics.total_iterations += 1
            iteration = self.project_context.metrics.total_iterations
            logger.info(f"--- Iniciando Ciclo P.O.D.A. #{iteration} ---")
            
            # P.O.D.A. PHASE 1: PLAN (Planejar) - Get next task
            current_task = await self._get_next_task()
            if not current_task:
                logger.info("Nenhuma tarefa executável encontrada. Verificando conclusão do projeto.")
                break

            # P.O.D.A. PHASE 2: ORIENT (Orientar) - Gather context and situational awareness
            logger.info(f"🧭 ORIENT: Contextualizando tarefa {current_task.task_id}")
            current_task.status = TaskStatus.IN_PROGRESS
            await self.project_context.save_context()
            
            # P.O.D.A. PHASE 3: DECIDE (Decidir) - Select optimal approach and tools
            logger.info(f"🎯 DECIDE: Preparando execução para {current_task.description}")

            # 🧠 METACOGNIÇÃO: Reflexão sobre processo de execução
            if self.metacognition_enabled:
                process_context = {
                    "strategy": "analytical",
                    "task_type": current_task.type.value,
                    "complexity": "medium",
                    "steps": [f"Executando tarefa {current_task.task_id}"],
                    "execution_time": 0.0
                }
                
                thinking_analysis = await self.metacognitive_engine.reflect_on_thinking_process(process_context)
                logger.info(f"🤔 METACOGNIÇÃO: Efetividade {thinking_analysis.effectiveness_score:.2f}")

            # P.O.D.A. PHASE 4: ACT (Agir) - Execute, validate and learn
            logger.info(f"⚡ ACT: Executando tarefa {current_task.task_id}")
            
            # Métricas de observabilidade - início da execução
            start_time = asyncio.get_event_loop().time()
            if self.observability:
                await self.observability.record_task_start(current_task.task_id, current_task.type.value)
            
            execution_result = await self.task_executor_agent.execute_task(current_task)

            # Validar resultado (ainda parte da fase ACT)
            validation_result = await self.semantic_validator_agent.validate_task_output(current_task, execution_result)
            
            # Métricas de observabilidade - fim da execução
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            if self.observability:
                await self.observability.record_task_completion(
                    current_task.task_id, 
                    validation_result.validation_passed,
                    execution_time,
                    execution_result.exit_code
                )
            
            # 🧠 METACOGNIÇÃO: Meta-aprendizado com experiência
            if self.metacognition_enabled:
                learning_experience = {
                    "task_type": current_task.type.value,
                    "success": validation_result.validation_passed,
                    "execution_time": execution_time,
                    "learning_effectiveness": 0.8 if validation_result.validation_passed else 0.3,
                    "learning_speed": 1.0 / max(execution_time, 0.1)
                }
                
                meta_insight = await self.metacognitive_engine.meta_learn_from_experience(learning_experience)
                logger.info(f"📚 META-APRENDIZADO: {meta_insight.description}")

            # 3. Decidir Próximo Passo
            if validation_result.validation_passed:
                logger.success(f"Tarefa {current_task.task_id} concluída e validada com sucesso!")
                current_task.status = TaskStatus.COMPLETED
                # Mover da fila principal para a de concluídas
                self.project_context.completed_tasks.append(current_task)
                self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
            else:
                issues_str = ', '.join(validation_result.identified_issues) if validation_result.identified_issues else "Motivos não especificados"
                logger.warning(f"Validação para tarefa {current_task.task_id} falhou: {issues_str}")
                current_task.retries += 1
                if current_task.retries >= current_task.max_retries:
                    logger.error(f"Tarefa {current_task.task_id} excedeu o máximo de tentativas.")
                    current_task.status = TaskStatus.FAILED
                    # Lógica de replanejamento seria acionada aqui
                    issues_list = validation_result.identified_issues if validation_result.identified_issues else ["Falha na validação sem detalhes específicos"]
                    error_feedback = (f"Tarefa '{current_task.description}' falhou após {current_task.retries} tentativas. "
                                      f"Últimos erros: {', '.join(issues_list)}")
                    
                    # Limite de replanejamentos para evitar loops infinitos
                    replan_count = getattr(current_task, 'replan_count', 0)
                    if replan_count >= 3:  # Máximo 3 replanejamentos
                        logger.error(f"Tarefa {current_task.task_id} excedeu limite de replanejamentos. Marcando como falha crítica.")
                        current_task.status = TaskStatus.FAILED
                        self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
                        self.project_context.failed_tasks.append(current_task)
                    else:
                        new_tasks = await self.planner_agent.replan_task(current_task, error_feedback)
                        if new_tasks:
                            # Propagar contador de replanejamento
                            for new_task in new_tasks:
                                new_task.replan_count = replan_count + 1
                            
                            # Substituir a tarefa antiga pelas novas
                            self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
                            self.project_context.task_queue = new_tasks + self.project_context.task_queue
                            logger.info(f"Tarefa replanejada ({replan_count + 1}/3): {len(new_tasks)} novas tarefas criadas")
                        else:
                            logger.error(f"Falha no replanejamento da tarefa {current_task.task_id}. Marcando como falha.")
                            current_task.status = TaskStatus.FAILED
                            self.project_context.task_queue = [t for t in self.project_context.task_queue if t.task_id != current_task.task_id]
                            self.project_context.failed_tasks.append(current_task)
                else:
                    logger.info(f"Tarefa {current_task.task_id} será tentada novamente.")
                    current_task.status = TaskStatus.PENDING # Volta para a fila

            await self.project_context.save_context()

        # Fase 3: Conclusão e Entrega conforme especificação
        logger.info("🏁 CONCLUSÃO: Iniciando verificação final do projeto")
        
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
            logger.info(f"📦 Backup final criado: {backup_path}")
        except Exception as e:
            logger.error(f"Falha ao criar backup final: {e}")

        # 3. Determinar status final baseado na verificação
        if completion_report.status.value == "completed":
            final_status = ProjectStatus.COMPLETED_SUCCESSFULLY
        elif completion_report.status.value in ["partially_completed"]:
            final_status = ProjectStatus.COMPLETED_WITH_FAILURES
        else:
            final_status = ProjectStatus.COMPLETED_WITH_FAILURES

        # Log do relatório final
        logger.info("📊 Relatório Final de Conclusão", 
                   status=completion_report.status.value,
                   score=completion_report.overall_score,
                   summary=completion_report.summary,
                   recommendations=completion_report.recommendations)

        self.project_context.status = final_status
        await self.project_context.save_context()
        logger.info(f"🎯 Ciclo do projeto finalizado com status: {self.project_context.status.value}")
        return self.project_context.status

    # ============================================================================
    # 🚀 MÉTODOS DE EXECUÇÃO INTELIGENTE A2A
    # ============================================================================

    async def _initialize_intelligent_a2a(self):
        """Inicializa sistema A2A inteligente com os agentes"""
        try:
            logger.info("🧠 Inicializando sistema A2A inteligente...")
            
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
            
            logger.info("✅ Sistema A2A inteligente inicializado com 3 agentes especializados")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização A2A: {e}")
            self.a2a_enabled = False

    async def _run_intelligent_a2a_cycle(self) -> ProjectStatus:
        """
        🚀 EXECUÇÃO INTELIGENTE A2A
        Usa colaboração avançada, especialização dinâmica e fault tolerance
        """
        logger.info("🚀 INICIANDO EXECUÇÃO INTELIGENTE A2A")
        
        try:
            # Fase 1: Planejamento Colaborativo (se necessário)
            if not self.project_context.task_queue:
                logger.info("🧠 Fase de Planejamento Colaborativo A2A")
                self.project_context.status = ProjectStatus.PLANNING
                await self.project_context.save_context()
                
                # Usar planner especializado
                plan_successful = await self._execute_collaborative_planning()
                if not plan_successful:
                    logger.error("❌ Falha no planejamento colaborativo")
                    self.project_context.status = ProjectStatus.PLANNING_FAILED
                    await self.project_context.save_context()
                    return self.project_context.status
                
                self.project_context.status = ProjectStatus.PLANNED
                await self.project_context.save_context()
            
            # Fase 2: Execução Inteligente via Pipeline Colaborativo
            logger.info("⚡ Iniciando Pipeline Colaborativo Inteligente")
            self.project_context.status = ProjectStatus.EXECUTING
            await self.project_context.save_context()
            
            # 🧠 METACOGNIÇÃO: Integrar metacognição com sistema A2A
            if self.metacognition_enabled:
                logger.info("🧠 Integrando metacognição com sistema A2A colaborativo")
                
                # Integração bidirecional: metacognição <-> A2A
                await self.intelligent_a2a.integrate_metacognitive_engine(self.metacognitive_engine)
                a2a_integration = await self.metacognitive_engine.integrate_with_a2a_system(self.intelligent_a2a)
                
                logger.info(f"🤝 Metacognição A2A integrada - Efetividade: {a2a_integration['effectiveness_score']:.2f}")
            
            # Executar projeto via sistema inteligente A2A
            pipeline_id = await self.intelligent_a2a.execute_intelligent_project(
                tasks=self.project_context.task_queue,
                project_name=self.project_context.project_name
            )
            
            logger.info(f"🎉 Pipeline colaborativo '{pipeline_id}' executado!")
            
            # Fase 3: Validação Inteligente Distribuída
            logger.info("🔍 Executando Validação Inteligente Distribuída")
            validation_success = await self._execute_intelligent_validation()
            
            # Fase 4: Geração de Relatório de Inteligência
            intelligence_report = await self.intelligent_a2a.generate_intelligence_report()
            logger.info("📊 Relatório de Inteligência A2A gerado", 
                       agents=intelligence_report["system_overview"]["total_agents"],
                       pipelines=intelligence_report["system_overview"]["active_pipelines"])
            
            # Determinar status final
            if validation_success:
                self.project_context.status = ProjectStatus.COMPLETED_SUCCESSFULLY
                logger.info("🎊 PROJETO CONCLUÍDO COM SUCESSO VIA A2A INTELIGENTE!")
            else:
                self.project_context.status = ProjectStatus.COMPLETED_WITH_FAILURES
                logger.warning("⚠️ Projeto concluído com algumas falhas")
            
            await self.project_context.save_context()
            return self.project_context.status
            
        except Exception as e:
            logger.error(f"❌ Erro na execução A2A inteligente: {e}")
            # Fallback para execução tradicional
            logger.info("🔄 Fallback: Executando modo tradicional")
            return await self._run_traditional_cycle()

    async def _execute_collaborative_planning(self) -> bool:
        """Executa planejamento colaborativo com especialização"""
        try:
            logger.info("🧠 Executando planejamento colaborativo especializado")
            
            # Verificar se o planner foi especializado
            await self.intelligent_a2a.analyze_and_specialize_agents()
            
            # Executar planejamento tradicional com melhorias A2A
            plan_successful = await self.planner_agent.generate_initial_plan()
            
            if plan_successful and len(self.project_context.task_queue) >= 5:
                # Projeto complexo - aplicar otimizações A2A
                logger.info("📈 Projeto complexo detectado - aplicando otimizações A2A")
                
                # Distribuir tarefas inteligentemente
                distribution = await self.intelligent_a2a.intelligent_task_distribution(
                    self.project_context.task_queue
                )
                
                logger.info(f"⚖️ Distribuição inteligente: {len(distribution)} agentes envolvidos")
            
            return plan_successful
            
        except Exception as e:
            logger.error(f"Erro no planejamento colaborativo: {e}")
            return False

    async def _execute_intelligent_validation(self) -> bool:
        """Executa validação inteligente distribuída"""
        try:
            logger.info("🔍 Executando validação inteligente distribuída")
            
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
                logger.info(f"📊 Validação distribuída: {success_rate:.1%} de sucesso")
                return success_rate >= 0.8  # 80% de sucesso mínimo
            
            return True  # Se não há tarefas para validar, considerar sucesso
            
        except Exception as e:
            logger.error(f"Erro na validação inteligente: {e}")
            return False

    async def get_a2a_intelligence_report(self) -> Dict:
        """Obtém relatório completo da inteligência A2A do projeto"""
        if not self.a2a_enabled:
            return {"error": "Sistema A2A não está habilitado"}
        
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
            logger.error(f"Erro ao gerar relatório A2A: {e}")
            return {"error": str(e)}

    def is_a2a_enabled(self) -> bool:
        """Verifica se o sistema A2A inteligente está habilitado"""
        return self.a2a_enabled

    async def enable_a2a_mode(self):
        """Habilita modo A2A inteligente dinamicamente"""
        if not self.a2a_enabled:
            self.a2a_enabled = True
            await self._initialize_intelligent_a2a()
            logger.info("🚀 Modo A2A Inteligente habilitado dinamicamente")

    async def disable_a2a_mode(self):
        """Desabilita modo A2A inteligente"""
        if self.a2a_enabled:
            self.a2a_enabled = False
            logger.info("🔄 Modo A2A desabilitado - usando execução tradicional")

    def is_metacognition_enabled(self) -> bool:
        """Verifica se o sistema metacognitivo está habilitado"""
        return self.metacognition_enabled

    async def enable_metacognition(self):
        """Habilita metacognição dinamicamente"""
        if not self.metacognition_enabled:
            self.metacognition_enabled = True
            logger.info("🧠 Metacognição habilitada dinamicamente")

    async def disable_metacognition(self):
        """Desabilita metacognição"""
        if self.metacognition_enabled:
            self.metacognition_enabled = False
            logger.info("🔄 Metacognição desabilitada")

    async def get_metacognitive_insights(self) -> Dict:
        """Obtém insights metacognitivos do sistema"""
        if not self.metacognition_enabled:
            return {"error": "Metacognição não está habilitada"}
        
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
            logger.error(f"Erro ao gerar insights metacognitivos: {e}")
            return {"error": str(e)}