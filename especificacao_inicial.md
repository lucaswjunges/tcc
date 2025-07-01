Esta versão foi meticulosamente projetada para ser o mais robusta e à prova de falhas possível. A arquitetura foi refinada para máxima modularidade, as interfaces são definidas como contratos rígidos e os mecanismos de segurança, resiliência e observabilidade foram detalhados para garantir um funcionamento autônomo e confiável.

O objetivo deste documento é servir como um **blueprint inequívoco**, permitindo que uma IA como a Claude 4 Opus o interprete e implemente todo o sistema em Python com o mínimo de ambiguidade e o máximo de qualidade.

---

# Especificação Canônica e Definitiva Inicial do Evolux Engine

## 1. Visão Geral

### 1.1. Missão
O **Evolux Engine** é um sistema de orquestração de Inteligência Artificial autônomo, projetado para operar como um **"cérebro de engenharia de software"** digital. Sua missão é transformar um objetivo de projeto de alto nível (e.g., "criar uma API de análise de sentimentos em Python com documentação e testes") em um produto final robusto, validado e pronto para entrega, de forma iterativa, autossuficiente e sem supervisão humana contínua.

### 1.2. Princípios Fundamentais de Arquitetura

1.  **Cognição Cíclica (Ciclo P.O.D.A.):** O sistema opera em um loop perpétuo de **Planejar** (decompor o objetivo), **Orientar** (contextualizar a tarefa), **Decidir** (selecionar ferramentas e gerar o comando) e **Agir** (executar, validar e aprender).
2.  **Modularidade por Contrato Estrito:** Cada componente é um "agente" especializado com responsabilidades únicas. A comunicação ocorre exclusivamente através de interfaces (contratos) JSON com schemas rigorosamente definidos, garantindo desacoplamento total e intercambialidade.
3.  **Segurança em Profundidade (Defense-in-Depth):** A segurança é uma série de barreiras em cascata: sanitização de entrada, validação de intenção por IA, verificação de comando em listas de permissão/bloqueio, e execução em ambiente sandbox com recursos limitados.
4.  **Resiliência Proativa e Auto-reparação:** O sistema não apenas reage a falhas, mas as antecipa e aprende com elas. Possui estratégias de fallback multicamadas, ciclos de depuração automáticos e a capacidade de reformular abordagens problemáticas.
5.  **Observabilidade Absoluta:** Todas as decisões, ações, estados e métricas são registrados em formato de log estruturado (JSON), permitindo auditoria completa, análise de performance, cálculo de custos e depuração pós-morte.
6.  **Estado como Única Fonte da Verdade:** Um único e abrangente objeto de contexto (`ProjectContext`) centraliza todo o estado, histórico e conhecimento do projeto, garantindo consistência, reprodutibilidade e a capacidade de pausar e resumir a operação.

## 2. Arquitetura do Sistema

O Evolux Engine é composto por um **Orquestrador Central** que gerencia o fluxo de execução e coordena um coletivo de módulos-agentes especializados.

```mermaid
graph TD
    subgraph "Orquestração e Controle"
        A[Orchestrator]
    end

    subgraph "Núcleo Cognitivo (Planejamento e Decisão)"
        B[PlannerAgent]
        C[PromptEngine]
        D[ModelRouter]
        E[LLMGateway]
    end

    subgraph "Núcleo de Ação (Execução e Feedback)"
        F[SecurityGateway]
        G[SecureExecutor]
        H[SemanticValidator]
    end

    subgraph "Subsistemas de Suporte"
        I[ContextManager]
        J[CriteriaEngine]
        K[ObservabilityService]
        L[BackupSystem]
    end

    %% Fluxo Principal de Execução Cognitiva
    A -->|1. Iniciar Ciclo| I
    I -->|2. Fornecer Estado Atual| A
    A -->|3. Definir Próxima Tarefa| B
    B -->|4. Gerar Plano de Ação| A
    A -->|5. Solicitar Prompt| C
    C -->|6. Construir Prompt Contextual| D
    D -->|7. Selecionar Modelo de IA| E
    E -->|8. Obter Resposta da IA (JSON)| A
    A -->|9. Enviar Comando para Validação| F
    F -->|10. Aprovar Comando Seguro| G
    G -->|11. Obter Resultado da Execução| H
    H -->|12. Produzir Análise de Validação| A
    A -->|13. Persistir Resultados e Aprendizado| I

    %% Fluxos de Controle e Suporte
    A -->|Verificar Conclusão| J
    J -->|Status de Conclusão| A
    A -- Eventos --> K
    B -- Eventos --> K
    E -- Eventos --> K
    G -- Eventos --> K
    H -- Eventos --> K
    A -->|Acionar Backup Periódico/Final| L
```

## 3. Fluxo de Execução Detalhado

O ciclo de vida de um projeto é gerenciado em três fases distintas.

### Fase 1: Inicialização e Planejamento Estratégico

1.  **Configuração (`SetupWizard`):** Se não houver configuração, um wizard interativo coleta o objetivo do projeto (`project_goal`), o tipo (`project_type`), os artefatos finais desejados (`final_artifacts`), e as credenciais (`OPENROUTER_API_KEY`, etc.). As configurações são salvas em `config/user_config.yaml`.
2.  **Criação do Contexto (`ContextManager`):** Um `ProjectContext` é inicializado, contendo um ID de projeto único (UUID) e o estado inicial.
3.  **Planejamento Inicial (`PlannerAgent`):** O `Orchestrator` invoca o `PlannerAgent` com o `project_goal`. O `PlannerAgent` usa um modelo de IA de raciocínio avançado (ex: Claude 3 Opus) para decompor o objetivo em uma **fila de tarefas interdependentes** (`task_queue`), que é salva no `ProjectContext`. Cada tarefa possui uma descrição, dependências e critérios de aceitação.

### Fase 2: Ciclo Cognitivo Iterativo (Coração do Sistema)

O `Orchestrator` executa este ciclo para cada tarefa na `task_queue`.

1.  **Orientação (Obter Tarefa e Contexto):** A próxima tarefa pendente é retirada da `task_queue`. O `ContextManager` fornece o estado completo do projeto.
2.  **Decisão (Formular o Prompt):**
    *   O `PromptEngine` constrói um prompt otimizado para a tarefa, injetando dinamicamente:
        *   Descrição da tarefa e critérios de aceitação.
        *   Estado atual dos artefatos (e.g., código existente, estrutura de arquivos).
        *   Histórico relevante de erros e sucessos de tarefas semelhantes.
        *   Feedback da última iteração (se for uma tentativa de correção).
        *   Uma instrução explícita para a IA responder em um formato JSON específico.
    *   O `ModelRouter` analisa o tipo de tarefa (`code_generation`, `validation`, `shell_command`) e seleciona o modelo de IA mais eficiente (custo vs. performance) com base em métricas históricas de performance armazenadas no `ProjectContext`.
3.  **Ação (Consultar IA e Executar):**
    *   O `LLMGateway` envia o prompt ao modelo selecionado, gerenciando a autenticação, novas tentativas (com backoff exponencial) e o parsing da resposta JSON. A resposta deve conter campos como `command`, `explanation`, e `thought_process`.
    *   O `SecurityGateway` intercepta o `command` e o submete a uma pipeline de verificação rigorosa (detalhada na Seção 6). Se o comando for reprovado, o ciclo é reiniciado com um feedback de falha de segurança.
    *   O `SecureExecutor` executa o comando aprovado em um ambiente sandbox (Docker), capturando `stdout`, `stderr`, código de saída, duração e uso de recursos.
4.  **Aprendizagem (Validar e Atualizar Estado):**
    *   O `SemanticValidator` realiza uma análise dupla:
        *   **Validação Sintática:** Verifica se a execução foi bem-sucedida (código de saída 0).
        *   **Validação Semântica:** Usa uma IA de raciocínio para avaliar se a *saída* (artefatos modificados, `stdout`) realmente cumpre a intenção da tarefa. Gera um `ValidationResult` detalhado.
    *   O `ContextManager` é invocado para registrar um `IterationLog` completo e atômico no `ProjectContext`, atualizando métricas, estado dos artefatos e histórico.
    *   O `Orchestrator` analisa o `ValidationResult`:
        *   **Sucesso:** A tarefa é marcada como concluída. O `Orchestrator` passa para a próxima tarefa da fila.
        *   **Falha:** A tarefa é mantida na fila. O `ValidationResult` (com os problemas identificados) é usado como feedback para a próxima tentativa no passo 2.
        *   **Falha Crítica (Looping):** Se a mesma tarefa falhar múltiplas vezes, o `Orchestrator` eleva o problema ao `PlannerAgent` para tentar uma abordagem estratégica diferente.

### Fase 3: Conclusão e Entrega

1.  **Verificação Final (`CriteriaEngine`):** Quando a `task_queue` está vazia, o `CriteriaEngine` executa uma verificação holística do projeto contra os `final_artifacts` e critérios de qualidade definidos na configuração (e.g., cobertura de testes > 80%, documentação completa).
2.  **Relatório e Backup (`BackupSystem`):** Um relatório final é gerado com o resumo do projeto, métricas de custo e performance. Um backup final e completo de todo o espaço de trabalho do projeto é criado.
3.  **Encerramento:** Recursos temporários são limpos e o sistema termina.

## 4. Módulos e Interfaces (Contratos)

Cada módulo é uma classe Python com responsabilidades claras e interfaces definidas por `TypedDict` ou `pydantic` para garantir a conformidade do contrato.

| Módulo                 | Responsabilidade Principal                                                                        | Interfaces Chave (Entrada -> Saída)                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Orchestrator**       | Conduz o ciclo de vida do projeto, coordenando todos os agentes.                                  | -                                                                                                        |
| **ContextManager**     | Gerencia o estado persistente e atômico do projeto (`ProjectContext`).                            | `update(payload: dict) -> bool` <br> `get() -> ProjectContext`                                           |
| **PlannerAgent**       | Decompõe objetivos em planos de tarefas acionáveis e reformula estratégias.                       | `plan(goal: str) -> TaskQueue` <br> `replan(failed_task: Task, context: ProjectContext) -> TaskQueue`     |
| **PromptEngine**       | Constrói prompts otimizados e contextualizados.                                                   | `build(task: Task, context: ProjectContext) -> str`                                                      |
| **ModelRouter**        | Seleciona dinamicamente o modelo de IA ótimo para a tarefa.                                       | `select(task_type: str, context: ProjectContext) -> ModelInfo`                                           |
| **LLMGateway**         | Abstrai chamadas de API, retries e parsing de resposta.                                           | `query(model: ModelInfo, prompt: str) -> LLMResponse`                                                    |
| **SecurityGateway**    | Valida a segurança de um comando antes da execução.                                               | `validate(command: str) -> SecurityValidationResult`                                                     |
| **SecureExecutor**     | Executa comandos em um ambiente isolado e monitorado (Docker).                                    | `run(command: str, dir: str, timeout: int) -> ExecutionResult`                                           |
| **SemanticValidator**  | Avalia se o resultado da execução cumpre a intenção da tarefa.                                    | `validate(task: Task, result: ExecutionResult, context: ProjectContext) -> ValidationResult`           |
| **CriteriaEngine**     | Determina se o projeto como um todo atingiu os critérios de conclusão.                             | `check_completion(context: ProjectContext) -> CompletionStatus`                                          |
| **ObservabilityService** | Centraliza a coleta de logs estruturados e métricas.                                              | `log_event(source: str, level: str, payload: dict)`                                                      |
| **BackupSystem**       | Gerencia snapshots e recuperação do estado do projeto.                                            | `create_snapshot(context: ProjectContext, artifacts_dir: str) -> str (path)`                             |

## 5. Tratamento de Falhas e Resiliência

O sistema é projetado para lidar com falhas em múltiplos níveis, de forma automática.

| Nível de Falha           | Gatilho                                          | Exemplo Comum                                    | Estratégia de Mitigação Imediata                                                                                                            |
| ------------------------ | ------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nível 1: Transitória** | Erro de rede na API, timeout de IA, flake-test   | Resposta 503 da API, `TimeoutError`              | **Retry Automático:** `LLMGateway` ou `SecureExecutor` tentam novamente com backoff exponencial (até 3 vezes).                               |
| **Nível 2: Formato**     | Resposta da IA em formato inválido               | Resposta em prosa em vez de JSON                 | **Auto-Correção de Prompt:** `Orchestrator` reenvia o prompt com uma instrução adicional: "ATENÇÃO: Sua resposta DEVE ser um JSON válido." |
| **Nível 3: Execução**    | Comando falha (exit code != 0), erro de sintaxe  | `python script.py` resulta em `SyntaxError`, `ImportError` | **Ciclo de Depuração:** O `stderr` completo é capturado e enviado como feedback para o `PromptEngine`. A IA é instruída a corrigir o erro.     |
| **Nível 4: Semântica**   | `SemanticValidator` retorna `passed: false`      | O código funciona, mas não implementa o requisito. | **Refinamento por Feedback:** O `ValidationResult` (com as issues) é usado para gerar um novo prompt, mais específico, para a mesma tarefa.    |
| **Nível 5: Estratégica** | A mesma tarefa falha > N vezes (e.g., 3)         | A IA entra em um loop tentando a mesma solução.    | **Escalonamento para o Planner:** `Orchestrator` pausa a tarefa e invoca o `PlannerAgent` para gerar uma nova abordagem estratégica.         |

## 6. Segurança em Profundidade

A segurança é um pilar não-negociável, implementado em camadas.

1.  **Gestão de Credenciais:** As chaves de API são carregadas exclusivamente de variáveis de ambiente ou de um arquivo de configuração com permissões restritas (`chmod 600`).
2.  **`SecurityGateway` Pipeline:** Todo comando gerado pela IA passa obrigatoriamente por esta pipeline antes da execução:
    a.  **Sanitização:** Remove caracteres de controle e normaliza espaços.
    b.  **Validação por IA:** Uma IA especializada em segurança (e.g., um modelo fine-tuned para análise de `bash`) avalia a **intenção** do comando, classificando o risco.
    c.  **Análise Estática:** O comando é verificado contra:
        *   **Whitelist (Permissão Estrita):** Uma lista de executáveis permitidos (`python`, `pip`, `git`, `mkdir`, `ls`, `cat`, etc.). Se o comando base não estiver na lista, é rejeitado.
        *   **Blacklist (Padrões Perigosos):** Uma lista de expressões regulares que bloqueiam padrões perigosos (`rm -rf /`, `sudo`, `chmod .* 777`, `mkfs`, acesso a `/dev/*`).
3.  **Execução em Sandbox (`SecureExecutor`):**
    *   **Isolamento Total:** Cada comando é executado em um **contêiner Docker efêmero**, criado sob demanda. O contêiner tem um filesystem isolado montado no diretório de trabalho do projeto.
    *   **Rede Restrita:** O acesso à rede é desabilitado por padrão e só pode ser habilitado para tarefas específicas que o exijam (e.g., `pip install`).
    *   **Recursos Limitados:** `cgroups` são usados para impor limites estritos de CPU, memória e tempo de execução (`timeout`), prevenindo ataques de negação de serviço.
    *   **Privilégios Mínimos:** O processo dentro do contêiner roda como um usuário não-root.
4.  **Auditoria Constante:** Todos os comandos (tentados, aprovados e bloqueados) e seus resultados são registrados imutavelmente pelo `ObservabilityService`.

## 7. Especificações Técnicas

*   **Linguagem:** Python 3.11+
*   **Dependências Chave:**
    *   `pydantic[dotenv]`: Para validação rigorosa de schemas e carga de configuração.
    *   `httpx`: Para chamadas de API assíncronas e robustas.
    *   `docker`: Para interação programática com o Docker daemon.
    *   `structlog`: Para logging estruturado de alta performance.
    *   `PyYAML`: Para arquivos de configuração legíveis.
*   **Estrutura de Diretórios do Projeto:**
    ```
    evolux_engine/
    ├── project_workspaces/
    │   └── <project_id>/
    │       ├── artifacts/      # Arquivos e código gerado pelo projeto
    │       ├── context.json    # O estado vivo do projeto
    │       └── logs/           # Logs específicos da execução
    │       └── backups/        # Backups/snapshots do projeto
    ├── config/
    │   ├── default_config.yaml # Configurações padrão do sistema
    │   └── user_config.yaml    # Configurações do usuário (sobrescreve o padrão)
    ├── src/
    │   ├── main.py
    │   └── agents/             # Módulos-agentes com lógica de negócio
    │   └── services/           # Módulos de suporte (Observability, Backup)
    │   └── schemas/            # Definições Pydantic para todos os contratos
    └── tests/
    ```

## 8. Formato dos Dados (Schemas de Contrato)

Estes schemas (a serem implementados com `pydantic`) são a espinha dorsal da comunicação entre módulos.

### ProjectContext
```json
{
  "project_id": "string (UUID)",
  "project_goal": "string",
  "project_type": "string ('code_project', 'academic_paper', etc.)",
  "status": "string ('initializing', 'planning', 'running', 'paused', 'completed', 'failed')",
  "task_queue": [/* Array de objetos Task */],
  "completed_tasks": [/* Array de objetos Task */],
  "iteration_history": [/* Array de objetos IterationLog */],
  "artifacts_state": {
    /* Dicionário representando o estado dos arquivos no diretório de artefatos.
       e.g., {"src/main.py": {"hash": "sha256...", "last_modified": "timestamp"}} */
  },
  "metrics": {
    "total_iterations": "integer",
    "total_cost_usd": "float",
    "total_tokens": {"prompt": "integer", "completion": "integer"},
    "model_performance": {
      "claude-3-opus-20240229": {"success_rate": 0.95, "avg_latency_ms": 1200}
    },
    "error_count": "integer",
    "last_updated": "string (ISO 8601 Timestamp)"
  },
  "engine_config": {
    "max_iterations_per_task": "integer",
    "security_level": "string ('strict', 'permissive')"
  }
}
```

### Task
```json
{
  "task_id": "string (UUID)",
  "description": "string (Descrição clara e acionável da tarefa)",
  "type": "string ('generate_code', 'run_tests', 'refactor', 'write_documentation')",
  "dependencies": ["array of task_ids"],
  "status": "string ('pending', 'in_progress', 'completed', 'failed')",
  "expected_artifacts": [{"name": "string", "type": "'file' | 'directory'"}],
  "acceptance_criteria": "string (Critérios objetivos para considerar a tarefa concluída)"
}
```

### ExecutionResult
```json
{
  "command_executed": "string",
  "exit_code": "integer",
  "stdout": "string",
  "stderr": "string",
  "execution_time_ms": "integer",
  "resource_usage": {"cpu_percent_peak": "float", "memory_mb_peak": "float"},
  "artifacts_changed": [
    {"path": "string", "change_type": "'created' | 'modified' | 'deleted'"}
  ]
}
```

### ValidationResult
```json
{
  "validation_passed": "boolean",
  "confidence_score": "float (0.0 to 1.0)",
  "checklist": {
    "correctness": "boolean",
    "completeness": "boolean",
    "efficiency": "boolean"
  },
  "identified_issues": ["array of strings"],
  "suggested_improvements": ["array of strings (feedback para a próxima iteração)"]
}
```

### IterationLog (Um item em `iteration_history`)
```json
{
  "iteration_id": "integer",
  "task_id": "string (UUID)",
  "attempt_number": "integer",
  "timestamp": "string (ISO 8601 Timestamp)",
  "thought_process": "string (O 'porquê' da decisão do Orchestrator)",
  "llm_request": {
    "model_used": "string",
    "prompt_hash": "string (SHA256 do prompt)"
  },
  "llm_response": "dict",
  "execution_result": "ExecutionResult (ou null)",
  "validation_result": "ValidationResult (ou null)",
  "decision": "string ('TASK_COMPLETED', 'RETRY_WITH_FEEDBACK', 'ESCALATE_TO_PLANNER')"
}
```