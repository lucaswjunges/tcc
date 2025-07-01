from typing import List, Dict, Set, Optional
from evolux_engine.schemas.contracts import Task, TaskStatus

class DependencyGraph:
    """
    Gerencia o grafo de dependências entre tarefas, permitindo
    a execução paralela e a análise do fluxo de trabalho.
    """
    def __init__(self):
        self.nodes: Dict[str, Task] = {}
        self.dependencies: Dict[str, Set[str]] = {}  # task_id -> set of dependency_ids
        self.dependents: Dict[str, Set[str]] = {}   # dependency_id -> set of task_ids

    def add_task(self, task: Task):
        """Adiciona uma tarefa (nó) ao grafo."""
        if task.task_id in self.nodes:
            return  # Evita duplicatas
        
        self.nodes[task.task_id] = task
        self.dependencies[task.task_id] = set(task.dependencies)
        self.dependents.setdefault(task.task_id, set())

        for dep_id in task.dependencies:
            self.dependents.setdefault(dep_id, set()).add(task.task_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retorna uma tarefa pelo seu ID."""
        return self.nodes.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Retorna todas as tarefas no grafo."""
        return list(self.nodes.values())

    def get_runnable_tasks(self) -> List[Task]:
        """
        Retorna uma lista de todas as tarefas que estão prontas para serem executadas,
        ou seja, estão com status PENDING e todas as suas dependências estão COMPLETED.
        """
        runnable = []
        for task_id, task in self.nodes.items():
            if task.status == TaskStatus.PENDING:
                if self.are_dependencies_met(task_id):
                    runnable.append(task)
        return runnable

    def are_dependencies_met(self, task_id: str) -> bool:
        """Verifica se todas as dependências de uma tarefa foram concluídas."""
        if task_id not in self.dependencies:
            return False  # Tarefa não existe no grafo

        for dep_id in self.dependencies[task_id]:
            dep_task = self.nodes.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def update_task_status(self, task_id: str, status: TaskStatus):
        """Atualiza o status de uma tarefa no grafo."""
        if task_id in self.nodes:
            self.nodes[task_id].status = status
        else:
            raise ValueError(f"Tarefa com ID '{task_id}' não encontrada no grafo.")

    def is_completed(self) -> bool:
        """Verifica se todas as tarefas no grafo estão concluídas ou falharam."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for task in self.nodes.values()
        )

    def to_mermaid(self) -> str:
        """Gera uma representação do grafo em formato Mermaid para visualização."""
        mermaid_str = "graph TD\n"
        for task_id, task in self.nodes.items():
            # Usar descrição curta e ID para o nó
            description = task.description.replace('"', "'").split('\n')[0]
            label = f"{task_id[:8]}[{description[:30]}...]"
            mermaid_str += f"    {label}\n"
            
            # Adicionar estilo baseado no status
            if task.status == TaskStatus.COMPLETED:
                mermaid_str += f"    style {task_id[:8]} fill:#d4edda,stroke:#c3e6cb\n"
            elif task.status == TaskStatus.IN_PROGRESS:
                mermaid_str += f"    style {task_id[:8]} fill:#fff3cd,stroke:#ffeeba\n"
            elif task.status == TaskStatus.FAILED:
                mermaid_str += f"    style {task_id[:8]} fill:#f8d7da,stroke:#f5c6cb\n"

        for task_id, deps in self.dependencies.items():
            for dep_id in deps:
                mermaid_str += f"    {dep_id[:8]} --> {task_id[:8]}\n"
        
        return mermaid_str
