import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

from loguru import logger

from evolux_engine.agents.orchestrator import Orchestrator
from evolux_engine.models.project_context import ProjectContext, ProjectStatus
from evolux_engine.schemas.contracts import EngineConfig # Para configurar o projeto
from evolux_engine.services.config_manager import ConfigManager

# --- Configuração do Logging com Loguru ---
def setup_logging(logging_level: str = "INFO", project_id: Optional[str] = None):
    """Configura o Loguru com base no nível de logging e opcionalmente um arquivo por projeto."""
    logger.remove() # Remove o handler padrão para evitar duplicação se o script for re-executado
    
    # Log para console
    logger.add(
        sys.stderr,
        level=logging_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # (Opcional) Log para um arquivo geral do engine
    # logger.add(
    #     "logs/evolux_engine.log",
    #     rotation="10 MB", # Rotaciona o arquivo quando atinge 10MB
    #     retention="7 days", # Mantém logs por 7 dias
    #     level="DEBUG", # Captura mais detalhes no arquivo
    #     format="{time} | {level} | {message}"
    # )

    if project_id:
        # (Opcional) Log específico para o projeto, se o ProjectContext ainda não for usado para isso
        # O ProjectContext.get_log_path() seria o ideal, mas precisamos do context antes.
        # Por agora, podemos deixar os logs do projeto serem gerenciados pelo próprio context ou orquestrador.
        pass

    logger.info(f"Logging configurado para nível: {logging_level.upper()}")


# --- Funções Helper para Gerenciamento de Contexto (Simplificado) ---
# Idealmente, isso estaria em um ProjectContextManager mais robusto.

async def load_or_create_project_context(
    config: ConfigManager,
    project_id: Optional[str] = None,
    project_goal: Optional[str] = None,
    project_name: Optional[str] = None,
    project_type: Optional[str] = None,
    final_artifacts_desc: Optional[str] = None,
    engine_config_overrides: Optional[dict] = None,
) -> ProjectContext:
    """
    Carrega um ProjectContext existente ou cria um novo.
    """
    base_dir = Path(config.project_base_directory)
    
    if project_id:
        logger.info(f"Tentando carregar projeto existente com ID: {project_id}")
        context = ProjectContext.load_from_file(project_id, base_dir)
        if context:
            # Garante que o workspace_path está atualizado se o base_dir mudou
            context.workspace_path = base_dir / project_id
            # Atualizar engine_config se houver overrides
            if engine_config_overrides:
                context.engine_config = EngineConfig(**{**context.engine_config.model_dump(), **engine_config_overrides})
                await context.save_context() # Salva se engine_config mudou
            return context
        else:
            logger.warning(f"Projeto com ID '{project_id}' não encontrado. Um novo será criado se um objetivo for fornecido.")
            # Se o objetivo não for fornecido junto com um ID não encontrado, é um erro.
            if not project_goal:
                 raise ValueError(f"ID de projeto '{project_id}' não encontrado e nenhum objetivo foi fornecido para criar um novo projeto.")
    
    # Criar um novo projeto
    if not project_goal:
        raise ValueError("Um objetivo ('--goal') é necessário para criar um novo projeto.")

    new_project_id = project_id or f"proj_{uuid.uuid4().hex[:8]}"
    logger.info(f"Criando novo projeto com ID: {new_project_id} e Objetivo: '{project_goal}'")

    workspace = base_dir / new_project_id
    workspace.mkdir(parents=True, exist_ok=True)

    initial_engine_config_data = {}
    if engine_config_overrides:
        initial_engine_config_data.update(engine_config_overrides)
    
    context = ProjectContext(
        project_id=new_project_id,
        project_goal=project_goal,
        project_name=project_name or new_project_id,
        project_type=project_type,
        final_artifacts_description=final_artifacts_desc,
        engine_config=EngineConfig(**initial_engine_config_data) # Aplica overrides na criação
    )
    context.workspace_path = workspace # Essencial definir antes do primeiro save!
    await context.save_context() # Salva o context.json inicial
    logger.info(f"Novo projeto '{context.project_name}' (ID: {context.project_id}) criado em: {context.workspace_path}")
    return context


# --- Função Principal ---
async def main():
    parser = argparse.ArgumentParser(description="Evolux Engine - Automação de Desenvolvimento e Tarefas com IA.")
    
    # Argumentos para identificar/criar o projeto
    group_project = parser.add_argument_group('Identificação ou Criação de Projeto')
    group_project.add_argument(
        "--id", 
        type=str, 
        help="ID de um projeto existente para continuar ou o ID a ser usado para um novo projeto."
    )
    group_project.add_argument(
        "--goal", 
        type=str, 
        help="O objetivo principal do projeto (necessário se um novo projeto for criado)."
    )
    group_project.add_argument(
        "--name", 
        type=str, 
        help="Nome para o projeto (usado se um novo projeto for criado)."
    )
    group_project.add_argument(
        "--type", 
        type=str,
        default="generic_project",
        help="Tipo de projeto (ex: 'python_cli_app', 'html_landing_page', 'research_summary'). Ajuda no planejamento."
    )
    group_project.add_argument(
        "--artifacts-desc",
        type=str,
        help="Descrição dos artefatos finais esperados para o projeto."
    )

    # Argumentos para configurar o engine para esta execução
    group_engine = parser.add_argument_group('Configurações do Engine (Overrides)')
    group_engine.add_argument(
        "--max-task-iterations",
        type=int,
        help="Override: Máximo de tentativas para uma única tarefa."
    )
    group_engine.add_argument(
        "--max-project-iterations",
        type=int,
        help="Override: Máximo de iterações totais para o projeto."
    )
    group_engine.add_argument(
        "--planner-model", type=str, help="Override: Modelo LLM para o PlannerAgent."
    )
    group_engine.add_argument(
        "--executor-model", type=str, help="Override: Modelo LLM para o TaskExecutorAgent (geração de conteúdo/comando)."
    )
    group_engine.add_argument(
        "--validator-model", type=str, help="Override: Modelo LLM para o SemanticValidatorAgent."
    )
    
    # Outros argumentos
    parser.add_argument(
        "--log-level", 
        type=str, 
        default=os.getenv("EVOLUX_LOGGING_LEVEL", "INFO"), 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Nível de logging para a console."
    )

    args = parser.parse_args()

    # Setup inicial do logging (sem ID de projeto ainda)
    setup_logging(args.log_level)

    try:
        config_manager = ConfigManager()
        logger.info("ConfigManager carregado.")
        
        # Coletar overrides de EngineConfig dos argumentos
        engine_cfg_overrides = {}
        if args.max_task_iterations is not None:
            engine_cfg_overrides["max_iterations_per_task"] = args.max_task_iterations
        if args.max_project_iterations is not None:
            engine_cfg_overrides["max_project_iterations"] = args.max_project_iterations
        if args.planner_model:
            engine_cfg_overrides["default_planner_model"] = args.planner_model
        if args.executor_model:
            engine_cfg_overrides["default_executor_model"] = args.executor_model # TaskExecutor usará este
        if args.validator_model:
            engine_cfg_overrides["default_validator_model"] = args.validator_model

        # Carregar ou criar o contexto do projeto
        project_context = await load_or_create_project_context(
            config=config_manager,
            project_id=args.id,
            project_goal=args.goal,
            project_name=args.name,
            project_type=args.type,
            final_artifacts_desc=args.artifacts_desc,
            engine_config_overrides=engine_cfg_overrides if engine_cfg_overrides else None
        )

        # (Opcional) Reconfigurar logging para incluir ID do projeto se desejado
        # setup_logging(args.log_level, project_id=project_context.project_id)

        logger.info(f"Iniciando Orchestrator para o projeto: '{project_context.project_name}' (ID: {project_context.project_id})")
        logger.info(f"Objetivo do Projeto: {project_context.project_goal}")
        logger.info(f"Configurações do Engine para este projeto: {project_context.engine_config.model_dump()}")

        # Inicializar e executar o Orchestrator
        orchestrator = Orchestrator(
            project_context=project_context,
            config_manager=config_manager
            # Outros serviços globais seriam passados aqui (Observability, etc.)
        )
        
        final_status = await orchestrator.run_project_cycle()

        logger.info(f"--- Ciclo do Projeto Concluído ---")
        logger.info(f"Projeto: '{project_context.project_name}' (ID: {project_context.project_id})")
        logger.info(f"Status Final: {final_status.value}")
        logger.info(f"Caminho do Workspace: {project_context.workspace_path}")
        logger.info(f"Métricas Finais: {project_context.metrics.model_dump_json(indent=2)}")
        
        if final_status == ProjectStatus.COMPLETED_SUCCESSFULLY:
            logger.info("Projeto concluído com sucesso!")
        elif final_status == ProjectStatus.COMPLETED_WITH_FAILURES:
            logger.warning("Projeto concluído, mas algumas tarefas falharam ou a validação final não passou.")
        else:
            logger.error(f"Projeto finalizado com status de falha: {final_status.value}")

    except ValueError as ve:
        logger.error(f"Erro de configuração ou argumento: {ve}")
        sys.exit(1)
    except Exception as e:
        logger.opt(exception=True).critical(f"Erro não tratado durante a execução do Evolux Engine: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
