from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
import uuid
from datetime import datetime
import os # Adicionado para o GlobalConfig

# --- Enumerações ---

class ProjectStatus(str, Enum):
    INITIALIZING = "initializing"
    PLANNING = "planning"
    PLANNED = "planned"  # Plano inicial gerado
    READY_TO_EXECUTE = "ready_to_execute" # Tarefas prontas para o orchestrator
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED_SUCCESSFULLY = "completed_successfully"
    COMPLETED_WITH_FAILURES = "completed_with_failures" # Terminou, mas algumas tarefas falharam ou validação final não passou
    FAILED = "failed" # Falha crítica que interrompeu
    PLANNING_FAILED = "planning_failed"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped" # Por exemplo, se uma dependência falhou criticamente
    WAITING_FOR_DEPENDENCIES = "waiting_for_dependencies"

class TaskType(str, Enum):
    """Define os tipos de tarefas que o Evolux Engine pode processar."""
    CREATE_FILE = "CREATE_FILE"
    MODIFY_FILE = "MODIFY_FILE"
    DELETE_FILE = "DELETE_FILE" # Adicionado para completude
    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    VALIDATE_ARTIFACT = "VALIDATE_ARTIFACT" # Validação semântica de um artefato ou estado
    ANALYZE_OUTPUT = "ANALYZE_OUTPUT" # Análise de stdout/stderr para extrair informações
    PLAN_SUB_TASKS = "PLAN_SUB_TASKS" # Para decomposição de tarefas complexas
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED" # Tarefa que pausa e pede input humano
    GENERIC_LLM_QUERY = "GENERIC_LLM_QUERY" # Para tarefas que são puramente uma consulta a LLM
    END_PROJECT = "END_PROJECT" # Uma tarefa especial para indicar o fim do projeto

class ArtifactChangeType(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    ACCESSED = "accessed" # Para casos onde um arquivo é lido mas não modificado

class LLMProvider(str, Enum):
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    # Adicionar outros provedores conforme necessário

# --- Schemas de Artefatos e Resultados ---

class ArtifactState(BaseModel):
    """Representa o estado de um único artefato no projeto."""
    path: str = Field(description="Caminho relativo do artefato dentro do workspace do projeto.")
    hash: Optional[str] = Field(None, description="Hash SHA256 do conteúdo do arquivo, se aplicável.")
    last_modified: Optional[datetime] = Field(None, description="Timestamp da última modificação.")
    summary: Optional[str] = Field(None, description="Breve resumo do conteúdo ou propósito do artefato.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais sobre o artefato.")

class ArtifactChange(BaseModel):
    """Descreve uma mudança em um artefato durante a execução de uma tarefa."""
    path: str = Field(description="Caminho relativo do artefato que mudou.")
    change_type: ArtifactChangeType = Field(description="Tipo de mudança ocorrida.")
    old_hash: Optional[str] = Field(None, description="Hash do arquivo antes da mudança, se aplicável.")
    new_hash: Optional[str] = Field(None, description="Hash do arquivo depois da mudança, se aplicável.")

class ResourceUsage(BaseModel):
    """Uso de recursos durante a execução de um comando."""
    cpu_percent_peak: Optional[float] = None
    memory_mb_peak: Optional[float] = None
    execution_time_ms: Optional[int] = None

class ExecutionResult(BaseModel):
    """Resultado da execução de um comando ou ação."""
    command_executed: Optional[str] = Field(None, description="O comando exato que foi executado (ou descrição da ação).")
    exit_code: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    resource_usage: Optional[ResourceUsage] = None
    artifacts_changed: List[ArtifactChange] = Field(default_factory=list)
    # Adicionar quaisquer outros campos relevantes, como 'success' booleano derivado do exit_code

    @property
    def success(self) -> bool:
        return self.exit_code == 0

class LLMCallMetrics(BaseModel):
    model_used: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None # Se puder ser calculado

class SemanticValidationChecklistItem(BaseModel):
    item: str = Field(description="Descrição do critério de validação.")
    passed: bool
    reasoning: Optional[str] = Field(None, description="Justificativa da IA para o status 'passed'.")

class ValidationResult(BaseModel):
    """Resultado da validação (geralmente semântica) de uma tarefa ou artefato."""
    validation_passed: bool
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiança da IA na validação.")
    checklist: Optional[List[SemanticValidationChecklistItem]] = Field(default_factory=list, description="Lista de critérios verificados.")
    identified_issues: List[str] = Field(default_factory=list, description="Problemas identificados.")
    suggested_improvements: List[str] = Field(default_factory=list, description="Sugestões para a próxima iteração.")
    llm_metrics: Optional[LLMCallMetrics] = None
    
    # Campos adicionais para sistema de refinamento iterativo
    quality_rating: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Nota de qualidade de 0-10")
    critical_problems: List[str] = Field(default_factory=list, description="Problemas críticos que impedem o progresso")
    reviewer_feedback: Optional[str] = Field(default=None, description="Feedback detalhado de revisor")
    requires_iteration: bool = Field(default=False, description="Indica se precisa de outra iteração")
    iteration_focus: Optional[str] = Field(default=None, description="Foco recomendado para próxima iteração")


# --- Schemas de Tarefas (Task) ---

class TaskDetails(BaseModel):
    """Classe base para os detalhes específicos de uma tarefa. Não deve ser instanciada diretamente."""
    pass

class TaskDetailsCreateFile(TaskDetails):
    file_path: str = Field(description="Caminho relativo (dentro de 'artifacts') onde o arquivo será criado.")
    content_guideline: str = Field(description="Instruções detalhadas para a IA gerar o conteúdo do arquivo.")
    overwrite: bool = Field(default=False, description="Se True, sobrescreve o arquivo se ele já existir.")

class TaskDetailsModifyFile(TaskDetails):
    file_path: str = Field(description="Caminho relativo do arquivo a ser modificado.")
    modification_guideline: str = Field(description="Instruções detalhadas para a IA modificar o arquivo.")
    expected_changes_summary: Optional[str] = Field(None, description="Um resumo do que se espera que mude no arquivo.")

class TaskDetailsDeleteFile(TaskDetails):
    file_path: str = Field(description="Caminho relativo do arquivo a ser deletado.")

class TaskDetailsExecuteCommand(TaskDetails):
    command_description: str = Field(description="Descrição em linguagem natural do que o comando deve fazer. A IA gerará o comando real.")
    expected_outcome: str = Field(description="O que se espera como resultado da execução do comando.")
    working_directory: Optional[str] = Field(None, description="Diretório de trabalho para o comando (relativo ao workspace/artifacts, ou absoluto se necessário).")
    timeout_seconds: int = Field(default=300, description="Tempo máximo para a execução do comando.")

class TaskDetailsValidateArtifact(TaskDetails):
    artifact_path: Optional[str] = Field(None, description="Caminho do artefato a ser validado (opcional se for validação de estado geral).")
    validation_criteria: str = Field(description="Critérios detalhados que o artefato/estado deve atender.")
    # Pode-se adicionar um campo para especificar o tipo de validador/LLM a ser usado

class TaskDetailsAnalyzeOutput(TaskDetails):
    source_task_id: str = Field(description="ID da tarefa cujo output (stdout/stderr) será analisado.")
    analysis_guideline: str = Field(description="O que extrair ou como interpretar o output.")
    expected_analysis_format: Optional[str] = Field(None, description="Formato esperado da análise (ex: JSON com chaves X, Y).")

class TaskDetailsPlanSubTasks(TaskDetails):
    complex_task_description: str = Field(description="Descrição da tarefa complexa que precisa ser decomposta.")
    parent_task_id: Optional[str] = Field(None, description="ID da tarefa original que está sendo decomposta.")
    context_summary: Optional[str] = Field(None, description="Resumo do contexto relevante para essa decomposição.")

class TaskDetailsHumanInterventionRequired(TaskDetails):
    intervention_prompt: str = Field(description="Pergunta ou instrução a ser apresentada ao usuário.")
    expected_input_format: Optional[str] = Field(None, description="Formato esperado da resposta do usuário.")

class TaskDetailsGenericLLMQuery(TaskDetails):
    query_goal: str = Field(description="Objetivo desta consulta específica à LLM.")
    query_prompt_template: Optional[str] = Field(None, description="Template de prompt a ser usado (se não for o padrão para este tipo de tarefa).")
    context_data_keys: List[str] = Field(default_factory=list, description="Chaves do ProjectContext a serem injetadas no prompt.")
    expected_response_format: str = Field(default="text", description="Formato esperado da resposta da LLM (text, json).")


# Union para o campo details em Task
AllTaskDetails = Union[
    TaskDetailsCreateFile,
    TaskDetailsModifyFile,
    TaskDetailsDeleteFile,
    TaskDetailsExecuteCommand,
    TaskDetailsValidateArtifact,
    TaskDetailsAnalyzeOutput,
    TaskDetailsPlanSubTasks,
    TaskDetailsHumanInterventionRequired,
    TaskDetailsGenericLLMQuery,
    TaskDetails, # Para tarefas genéricas ou tipos ainda não especificados
]

class Task(BaseModel):
    """Representa uma única tarefa no plano do projeto."""
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4()}")
    description: str
    type: TaskType
    details: Optional[AllTaskDetails] = None # Usando a Union
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    acceptance_criteria: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    retries: int = Field(default=0)
    max_retries: int = Field(default=3)
    replan_count: int = Field(default=0, description="Número de vezes que esta tarefa foi replanejada")
    assigned_agent_id: Optional[str] = None # Se diferentes agentes puderem pegar tarefas
    execution_history: List[ExecutionResult] = Field(default_factory=list, description="Histórico de tentativas de execução para esta tarefa.")
    validation_history: List[ValidationResult] = Field(default_factory=list, description="Histórico de validações para esta tarefa.")
    raw_llm_response_planning: Optional[Dict[str, Any]] = Field(None, description="A resposta JSON original da LLM que gerou esta tarefa (se aplicável).")
    # Adicionar 'priority' ou 'estimated_effort' futuramente?

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()

class TaskQueue(BaseModel):
    """Wrapper para a lista de tarefas, caso a LLM retorne um objeto com esta chave."""
    task_queue: List[Task]

# --- Schemas do Projeto e Iterações ---

class IterationLog(BaseModel):
    """Registra os detalhes de uma única iteração do ciclo de processamento de uma tarefa."""
    iteration_id: int # Sequencial dentro do projeto
    task_id: str
    attempt_number: int # Número da tentativa para esta tarefa específica
    timestamp_start: datetime = Field(default_factory=datetime.utcnow)
    timestamp_end: Optional[datetime] = None
    thought_process: Optional[str] = Field(None, description="Raciocínio do Orchestrator ou Agente para esta iteração.")
    
    planner_llm_call: Optional[LLMCallMetrics] = None # Se a iteração envolveu planejamento
    executor_llm_call: Optional[LLMCallMetrics] = None # Se a iteração envolveu geração de conteúdo/comando
    
    prompt_sent_to_llm: Optional[str] = Field(None, description="O prompt principal enviado (pode ser truncado para logs).") # Ou hash
    raw_llm_response: Optional[str] = Field(None, description="Resposta bruta da LLM (pode ser truncado).") # Ou hash

    execution_result: Optional[ExecutionResult] = None # Se a tarefa envolveu execução
    validation_result: Optional[ValidationResult] = None # Se a tarefa envolveu validação
    
    decision: Optional[str] = Field(None, description="Decisão do Orchestrator após esta iteração (ex: TASK_COMPLETED, RETRY_WITH_FEEDBACK).")
    error_summary: Optional[str] = None


class ProjectMetrics(BaseModel):
    """Métricas agregadas do projeto."""
    total_iterations: int = 0
    total_llm_calls: int = 0
    total_cost_usd: float = 0.0
    total_tokens_prompt: int = 0
    total_tokens_completion: int = 0
    total_execution_time_sec: float = 0.0
    error_count_execution: int = 0
    error_count_llm: int = 0
    error_count_validation: int = 0
    # Adicionar métricas de performance de modelos específicos se o ModelRouter for implementado
    model_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Ex: {'claude-3-opus': {'success_rate': 0.9, 'avg_latency_ms': 1500}}")

class EngineConfig(BaseModel):
    """Configurações do motor Evolux para este projeto específico."""
    max_iterations_per_task: int = Field(default=5, description="Máximo de tentativas para uma única tarefa antes de escalonar.")
    max_project_iterations: int = Field(default=100, description="Máximo de iterações totais para o projeto.")
    max_consecutive_planner_failures: int = Field(default=3, description="Máximo de falhas consecutivas do PlannerAgent antes de parar.")
    security_level: str = Field(default="strict", description="Nível de segurança para execução de comandos ('strict' ou 'permissive').")
    default_planner_model: Optional[str] = None
    default_executor_model: Optional[str] = None # Para geração de conteúdo/comando
    default_validator_model: Optional[str] = None # Para validação semântica
    # Outras configurações específicas do engine

class ProjectContext(BaseModel):
    """Schema principal para o context.json, a fonte da verdade do projeto."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: Optional[str] = None # Adicionado para fácil identificação
    project_goal: str
    project_type: Optional[str] = Field(None, description="Tipo de projeto (ex: 'code_project', 'research_paper', 'html_page'). Influencia o planejamento e validação.")
    final_artifacts_description: Optional[str] = Field(None, description="Descrição dos artefatos finais esperados.")
    
    status: ProjectStatus = Field(default=ProjectStatus.INITIALIZING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    task_queue: List[Task] = Field(default_factory=list)
    completed_tasks: List[Task] = Field(default_factory=list) # Poderia ser uma lista de task_ids ou os objetos Task completos
    failed_tasks: List[Task] = Field(default_factory=list) # Tarefas que falharam definitivamente
    
    iteration_history: List[IterationLog] = Field(default_factory=list)
    
    # Estado dos artefatos: caminho -> hash, resumo, etc.
    artifacts_state: Dict[str, ArtifactState] = Field(default_factory=dict)
    
    metrics: ProjectMetrics = Field(default_factory=ProjectMetrics)
    engine_config: EngineConfig = Field(default_factory=EngineConfig)
    
    # Campo para feedback de erro que pode ser usado pelo PlannerAgent ao replanejar
    current_error_feedback_for_planner: Optional[str] = None

    # Armazena o workspace_path para ser usado internamente, não precisa ser parte do JSON salvo
    # se for sempre derivável do PROJECT_BASE_DIR e project_id.
    # Mas para conveniência, podemos adicionar se o ContextManager o popula.
    # workspace_path: Optional[str] = Field(None, exclude=True) # exclude=True para não salvar no JSON


    @validator("last_updated", pre=True, always=True)
    def set_last_updated(cls, v):
        return datetime.utcnow()

    # Métodos utilitários podem ser adicionados aqui se fizer sentido,
    # ou mantidos no ContextManager.
    # Exemplo:
    # def get_task_by_id(self, task_id: str) -> Optional[Task]:
    #     for task in self.task_queue:
    #         if task.task_id == task_id:
    #             return task
    #     for task in self.completed_tasks:
    #         if task.task_id == task_id:
    #             return task
    #     return None

    # def update_task_status(self, task_id: str, new_status: TaskStatus):
    #     # ... lógica para encontrar e atualizar ...
    #     pass

    def get_artifacts_structure_summary(self, max_depth: int = 2, max_files_per_dir: int = 5) -> str:
        """Gera um resumo da estrutura de arquivos e diretórios para prompts."""
        if not self.artifacts_state:
            return "Nenhum artefato gerado ainda."

        # Esta é uma implementação simplificada. Poderia usar os.walk ou similar
        # se você tiver uma representação real da árvore de diretórios além do artifacts_state.
        # Por agora, vamos listar as chaves de artifacts_state.
        paths = sorted(list(self.artifacts_state.keys()))
        if not paths:
            return "Nenhum artefato registrado no estado."

        summary_lines = ["Estrutura de Artefatos Atual:"]
        # Tentar construir uma estrutura visual simples
        tree = {}
        for path_str in paths:
            parts = path_str.split('/')
            current_level = tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        
        def build_tree_str(current_level_dict: dict, prefix: str = "", depth: int = 0) -> None:
            if depth > max_depth:
                if current_level_dict: # Se há mais itens aninhados
                    summary_lines.append(f"{prefix}...")
                return

            items = list(current_level_dict.items())
            for i, (name, next_level_dict) in enumerate(items):
                connector = "├── " if i < len(items) - 1 else "└── "
                summary_lines.append(f"{prefix}{connector}{name}")
                if next_level_dict: # É um diretório com mais itens
                    new_prefix = prefix + ("│   " if i < len(items) - 1 else "    ")
                    build_tree_str(next_level_dict, new_prefix, depth + 1)
                if i >= max_files_per_dir -1 and len(items) > max_files_per_dir :
                    summary_lines.append(f"{prefix}    └── ... (mais {len(items) - max_files_per_dir} itens)")
                    break


        build_tree_str(tree)
        return "\n".join(summary_lines)

# --- Outros Schemas Úteis ---

class LLMClientConfig(BaseModel):
    """Configuração para um cliente LLM."""
    provider: LLMProvider
    api_key: Optional[str] = None # Pode vir de env var
    default_model: Optional[str] = None
    # Outros parâmetros específicos do provedor (temperature, top_p, etc.)
    api_base_url: Optional[str] = None # Para OpenAI ou compatíveis

class GlobalConfig(BaseSettings):
    """Configurações globais do Evolux Engine."""
    evolux_openrouter_api_key: Optional[str] = Field(None, alias="OPENROUTER_API_KEY", env="EVOLUX_OPENROUTER_API_KEY")
    evolux_openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY", env="EVOLUX_OPENAI_API_KEY")
    evolux_google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY", env="EVOLUX_GOOGLE_API_KEY")
    # Adicione outras chaves de API conforme necessário

    project_base_dir: str = Field(default=os.path.join(os.getcwd(), "project_workspaces"), env="EVOLUX_PROJECT_BASE_DIR")
    
    default_llm_provider: LLMProvider = Field(default=LLMProvider.OPENROUTER, env="EVOLUX_LLM_PROVIDER")
    
    # Modelos padrão para diferentes funções (usados se não especificados no ProjectContext.engine_config)
    default_model_planner: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", env="EVOLUX_MODEL_PLANNER")
    default_model_executor_content_gen: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", env="EVOLUX_MODEL_EXECUTOR_CONTENT_GEN")
    default_model_executor_command_gen: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", env="EVOLUX_MODEL_EXECUTOR_COMMAND_GEN")
    default_model_validator: str = Field(default="deepseek/deepseek-r1-0528-qwen3-8b:free", env="EVOLUX_MODEL_VALIDATOR")

    max_concurrent_tasks: int = Field(default=1, env="EVOLUX_MAX_CONCURRENT_TASKS") # Começar com 1 para simplicidade
    logging_level: str = Field(default="INFO", env="EVOLUX_LOGGING_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )