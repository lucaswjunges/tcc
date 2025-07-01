import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
import os
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

# Removido logging.basicConfig para evitar conflitos
# logger = logging.getLogger(__name__)
from evolux_engine.utils.logging_utils import get_structured_logger
logger = get_structured_logger("planner")

# Imports from contracts
from evolux_engine.schemas.contracts import (
    Task, TaskType, TaskStatus,
    TaskDetailsCreateFile, TaskDetailsModifyFile, TaskDetailsExecuteCommand
)
from evolux_engine.core.dependency_graph import DependencyGraph
from evolux_engine.core.evolux_a2a_integration import A2ACapableMixin, auto_register_agent, handoff_capable


@auto_register_agent("planner", ["handle_context_transfer", "handle_task_delegation", "handle_knowledge_share"])
@handoff_capable("context_transfer", "task_delegation", "knowledge_share")
class PlannerAgent(A2ACapableMixin):
    """Classe responsável por gerenciar a criação e o fluxo de tarefas com capacidades A2A"""
    def __init__(self, context_manager, task_db, artifact_store, project_context=None, llm_client=None):
        # Inicializar A2A primeiro
        super().__init__()
        
        self.context_manager = context_manager
        self.task_db = task_db
        self.artifact_store = artifact_store
        self.project_context = project_context
        self.llm_client = llm_client  # Para análise semântica
        self.active_tasks = {}
        self.next_task_id = self._generate_next_id()
        self.failure_history = {}  # Track failures for recovery
        self.recovery_strategies = {}  # Store recovery strategies
        self.max_recovery_attempts = 3  # Maximum recovery attempts per task
        
        # A2A specific attributes
        self.delegated_tasks = {}  # Tarefas delegadas para outros agentes
        self.received_contexts = {}  # Contextos recebidos de outros agentes
        
        logger.info("PlannerAgent inicializado com componentes necessários e capacidades A2A")

    def _generate_next_id(self) -> str:
        """Gera um ID sequencial único"""
        return str(uuid.uuid4())

    async def generate_initial_plan(self) -> bool:
        """Gera o plano inicial de tarefas para o projeto e o estrutura como um DependencyGraph."""
        try:
            logger.info("Gerando plano inicial de tarefas...")
            project_goal = self.project_context.project_goal if self.project_context else "projeto genérico"
            logger.info(f"Planejando para objetivo: {project_goal}")

            # O DependencyGraph será a fonte da verdade para a estrutura do plano
            dependency_graph = await self._generate_dynamic_plan(project_goal)
            
            # Popular a task_queue do contexto do projeto a partir do grafo
            if self.project_context:
                all_tasks = dependency_graph.get_all_tasks()
                self.project_context.task_queue = all_tasks
                await self.project_context.save_context()
                logger.info(f"Plano inicial criado com {len(all_tasks)} tarefas e salvo no contexto.")
                # Opcional: Logar a estrutura do grafo para depuração
                # logger.debug(f"Grafo de dependências gerado:\n{dependency_graph.to_mermaid()}")
            else:
                # Fallback para ambientes sem project_context
                self.active_tasks = {task.task_id: task for task in dependency_graph.get_all_tasks()}

            return True
            
        except Exception as e:
            logger.opt(exception=True).error("Erro ao gerar plano inicial")
            return False

    async def _generate_dynamic_plan(self, project_goal: str) -> DependencyGraph:
        """Gera um plano dinâmico de tarefas e o retorna como um DependencyGraph."""
        graph = DependencyGraph()
        project_analysis = await self._analyze_project_semantically(project_goal)
        
        # Tarefas básicas que todo projeto precisa (sem dependências)
        readme_task = Task(
            task_id=self._generate_next_id(),
            description="Criar documentação do projeto",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="README.md", content_guideline=f"Criar documentação completa para: {project_goal}."),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="README.md específico e completo para o projeto"
        )
        graph.add_task(readme_task)

        reqs_task = Task(
            task_id=self._generate_next_id(),
            description="Criar arquivo de dependências",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="requirements.txt", content_guideline=f"Listar dependências Python para: {project_goal}."),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="requirements.txt com dependências específicas do projeto"
        )
        graph.add_task(reqs_task)
        
        # Gerar tarefas específicas do domínio e adicioná-las ao grafo
        await self._generate_domain_specific_tasks(
            graph,
            project_analysis['project_type'], 
            project_goal,
            project_analysis['complexity']
        )
        
        # Adicionar tarefas de qualidade (que podem depender de outras)
        if project_analysis['complexity'] >= 7:
            self._get_enterprise_quality_tasks(graph)
        elif project_analysis['complexity'] >= 5:
            self._get_professional_quality_tasks(graph)
        
        return graph

    async def _analyze_project_semantically(self, goal: str) -> Dict[str, Any]:
        """Analisa semanticamente o objetivo do projeto usando LLM"""
        try:
            # Se tiver LLM client disponível, usar análise semântica
            if hasattr(self, 'llm_client') and self.llm_client:
                analysis_prompt = f"""
                Analise este objetivo de projeto e determine:
                1. Tipo de aplicação (web_app, api, desktop, mobile, data_science, game, etc.)
                2. Complexidade (1-10 onde 1=simples, 10=enterprise)
                3. Tecnologias necessárias
                4. Componentes principais
                5. Funcionalidades essenciais

                Objetivo: {goal}

                Retorne JSON estruturado:
                {{
                    "project_type": "tipo",
                    "complexity": número,
                    "technologies": ["tech1", "tech2"],
                    "components": ["comp1", "comp2"],
                    "features": ["feat1", "feat2"]
                }}
                """
                
                try:
                    response = await self.llm_client.generate_response(analysis_prompt)
                    import json
                    return json.loads(response)
                except Exception as e:
                    logger.warning(f"Erro na análise semântica: {e}. Usando fallback.")
            
            # Fallback para análise básica por palavras-chave
            return self._analyze_project_basic(goal)
            
        except Exception as e:
            logger.error(f"Erro na análise semântica: {e}")
            return self._analyze_project_basic(goal)

    def _analyze_project_basic(self, goal: str) -> Dict[str, Any]:
        """Análise básica por palavras-chave como fallback"""
        goal_lower = goal.lower()
        
        # Determinar tipo de projeto
        if any(keyword in goal_lower for keyword in ["blog", "cms", "artigo", "post", "conteúdo"]):
            project_type = "blog"
            complexity = 6
        elif any(keyword in goal_lower for keyword in ["api", "rest", "microserviço", "microservice"]):
            project_type = "api"
            complexity = 5
        elif any(keyword in goal_lower for keyword in ["ecommerce", "loja", "vendas", "produto", "cart"]):
            project_type = "ecommerce"
            complexity = 8
        elif any(keyword in goal_lower for keyword in ["dashboard", "admin", "gestão", "gerenciamento"]):
            project_type = "dashboard"
            complexity = 7
        elif any(keyword in goal_lower for keyword in ["chatbot", "chat", "bot", "assistente"]):
            project_type = "chatbot"
            complexity = 6
        elif any(keyword in goal_lower for keyword in ["análise", "data", "dados", "relatório", "gráfico"]):
            project_type = "data_science"
            complexity = 7
        elif any(keyword in goal_lower for keyword in ["flask", "django", "web", "site"]):
            project_type = "web_app"
            complexity = 5
        else:
            project_type = "generic"
            complexity = 4
            
        # Ajustar complexidade baseada em palavras-chave adicionais
        if any(keyword in goal_lower for keyword in ["autenticação", "login", "usuário", "auth"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["banco", "database", "db", "dados"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["testes", "test", "ci", "deploy"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["docker", "kubernetes", "cloud"]):
            complexity += 2
            
        complexity = min(complexity, 10)  # Máximo 10
        
        return {
            "project_type": project_type,
            "complexity": complexity,
            "technologies": ["python", "flask"],
            "components": ["main", "config", "requirements"],
            "features": ["basic_functionality"]
        }

    async def _generate_domain_specific_tasks(self, graph: DependencyGraph, project_type: str, goal: str, complexity: int):
        """Gera tarefas específicas do domínio e as adiciona diretamente ao grafo."""
        
        # A lógica de contagem de tarefas pode ser mantida para guiar a geração
        logger.info(f"Gerando tarefas de domínio para projeto tipo '{project_type}' com complexidade {complexity}")
        
        # Gerar tarefas específicas por tipo e adicioná-las ao grafo
        if project_type == "blog":
            self._get_blog_tasks(graph)
        elif project_type == "api":
            self._get_enhanced_api_tasks(graph, complexity)
        elif project_type == "ecommerce":
            self._get_enhanced_ecommerce_tasks(graph, complexity)
        elif project_type == "dashboard":
            self._get_enhanced_dashboard_tasks(graph, complexity)
        elif project_type == "web_app":
            self._get_enhanced_web_app_tasks(graph, complexity)
        else:
            self._get_enhanced_generic_tasks(graph, complexity)

    def _get_enhanced_api_tasks(self, graph: DependencyGraph, complexity: int):
        """Adiciona tarefas aprimoradas para APIs diretamente ao grafo."""
        models_task = Task(
            task_id=self._generate_next_id(),
            description="Criar modelos de dados da API",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="models.py", content_guideline="Modelos SQLAlchemy com relacionamentos, validações e métodos de serialização"),
            dependencies=[],
            acceptance_criteria="Modelos de dados implementados com relacionamentos corretos"
        )
        graph.add_task(models_task)

        schemas_task = Task(
            task_id=self._generate_next_id(),
            description="Criar schemas de validação",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="schemas.py", content_guideline="Schemas Marshmallow para validação e serialização de dados da API"),
            dependencies=[models_task.task_id],
            acceptance_criteria="Schemas de validação implementados"
        )
        graph.add_task(schemas_task)

        api_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar API REST principal",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="api.py", content_guideline="API REST com Flask-RESTX, endpoints CRUD, documentação Swagger automática"),
            dependencies=[schemas_task.task_id],
            acceptance_criteria="API REST com documentação implementada"
        )
        graph.add_task(api_task)
        
        last_task_id = api_task.task_id
        if complexity >= 5:
            auth_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar autenticação JWT",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(file_path="auth.py", content_guideline="Sistema de autenticação com JWT, registro e login de usuários"),
                dependencies=[api_task.task_id],
                acceptance_criteria="Sistema de autenticação JWT implementado"
            )
            graph.add_task(auth_task)
            last_task_id = auth_task.task_id
            
        if complexity >= 6:
            test_task = Task(
                task_id=self._generate_next_id(),
                description="Criar testes automatizados",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(file_path="test_api.py", content_guideline="Testes pytest para todos os endpoints da API com cobertura de casos de uso"),
                dependencies=[last_task_id],
                acceptance_criteria="Suite de testes automatizados implementada"
            )
            graph.add_task(test_task)
            last_task_id = test_task.task_id
            
        if complexity >= 7:
            dockerfile_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar containerização Docker",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(file_path="Dockerfile", content_guideline="Dockerfile multi-stage para produção com otimizações de segurança e performance"),
                dependencies=[last_task_id],
                acceptance_criteria="Dockerfile de produção criado"
            )
            graph.add_task(dockerfile_task)
            
            compose_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar docker-compose",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(file_path="docker-compose.yml", content_guideline="Docker-compose com API, banco de dados, Redis e proxy reverso"),
                dependencies=[dockerfile_task.task_id],
                acceptance_criteria="Orquestração Docker configurada"
            )
            graph.add_task(compose_task)

    def _get_enhanced_web_app_tasks(self, complexity: int) -> List[Task]:
        """Tarefas aprimoradas para aplicações web"""
        tasks = []
        
        # Tarefas básicas sempre incluídas
        tasks.extend([
            Task(
                task_id=self._generate_next_id(),
                description="Criar aplicação Flask principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="app.py",
                    content_guideline="Aplicação Flask com estrutura MVC, rotas organizadas e configuração adequada"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Aplicação Flask estruturada implementada"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Criar templates base",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="templates/base.html",
                    content_guideline="Template base com Bootstrap, navbar responsiva e sistema de mensagens"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Sistema de templates base criado"
            )
        ])
        
        # Tarefas baseadas na complexidade
        if complexity >= 5:
            tasks.extend([
                Task(
                    task_id=self._generate_next_id(),
                    description="Implementar sistema de usuários",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="models.py",
                        content_guideline="Modelos User com autenticação, perfis e sistema de permissões"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Sistema de usuários implementado"
                ),
                Task(
                    task_id=self._generate_next_id(),
                    description="Criar formulários de autenticação",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="forms.py",
                        content_guideline="Formulários WTF para login, registro e edição de perfil com validações"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Formulários de autenticação criados"
                )
            ])
            
        if complexity >= 7:
            tasks.extend([
                Task(
                    task_id=self._generate_next_id(),
                    description="Implementar painel administrativo",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="admin.py",
                        content_guideline="Painel administrativo com gestão de usuários, conteúdo e métricas"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Painel administrativo implementado"
                ),
                Task(
                    task_id=self._generate_next_id(),
                    description="Configurar deployment",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="deploy.py",
                        content_guideline="Script de deployment com configurações de produção e CI/CD"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Sistema de deployment configurado"
                )
            ])
            
        return tasks

    def _get_enhanced_generic_tasks(self, complexity: int) -> List[Task]:
        """Tarefas aprimoradas para projetos genéricos"""
        tasks = []
        
        # Tarefas básicas
        tasks.extend([
            Task(
                task_id=self._generate_next_id(),
                description="Criar aplicação principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="main.py",
                    content_guideline="Aplicação principal com arquitetura limpa, logging e tratamento de erros"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Aplicação principal implementada"
            )
        ])
        
        # Tarefas baseadas na complexidade
        if complexity >= 5:
            tasks.extend([
                Task(
                    task_id=self._generate_next_id(),
                    description="Criar sistema de configuração",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="config.py",
                        content_guideline="Sistema de configuração com variáveis de ambiente e validações"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Sistema de configuração implementado"
                ),
                Task(
                    task_id=self._generate_next_id(),
                    description="Implementar sistema de logging",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="logger.py",
                        content_guideline="Sistema de logging estruturado com diferentes níveis e outputs"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Sistema de logging implementado"
                )
            ])
            
        if complexity >= 7:
            tasks.append(Task(
                task_id=self._generate_next_id(),
                description="Criar testes unitários",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="tests.py",
                    content_guideline="Suite de testes unitários com pytest e cobertura adequada"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Testes unitários implementados"
            ))
            
        return tasks

    def _get_professional_quality_tasks(self, graph: DependencyGraph):
        """Adiciona tarefas de qualidade profissional diretamente ao grafo."""
        # Encontrar a última tarefa adicionada para criar dependência
        # Esta é uma heurística simples; uma abordagem melhor poderia ser mais específica.
        last_task_id = None
        if graph.nodes:
            # Tenta encontrar uma tarefa principal como 'api.py' ou 'app.py'
            main_app_tasks = [t for t in graph.get_all_tasks() if t.details and ('app.py' in getattr(t.details, 'file_path', '') or 'api.py' in getattr(t.details, 'file_path', ''))]
            if main_app_tasks:
                last_task_id = main_app_tasks[0].task_id
            else:
                # Fallback para a última tarefa adicionada
                last_task_id = list(graph.nodes.keys())[-1]

        linting_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar linting e formatação",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path=".pre-commit-config.yaml",
                    content_guideline="Configuração pre-commit com black, flake8, isort e mypy"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id] if last_task_id else [],
                acceptance_criteria="Linting e formatação configurados"
            )
        graph.add_task(linting_task)

        docs_task = Task(
                task_id=self._generate_next_id(),
                description="Criar documentação técnica",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="docs/ARCHITECTURE.md",
                    content_guideline="Documentação da arquitetura, decisões técnicas e guias de desenvolvimento"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id] if last_task_id else [],
                acceptance_criteria="Documentação técnica criada"
            )
        graph.add_task(docs_task)


    def _get_enterprise_quality_tasks(self, graph: DependencyGraph):
        """Adiciona tarefas de nível enterprise diretamente ao grafo."""
        last_task_id = None
        if graph.nodes:
            last_task_id = list(graph.nodes.keys())[-1]

        monitoring_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar monitoramento e métricas",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="monitoring.py",
                    content_guideline="Sistema de monitoramento com Prometheus, health checks e alertas"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id] if last_task_id else [],
                acceptance_criteria="Sistema de monitoramento implementado"
            )
        graph.add_task(monitoring_task)

        cicd_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar pipeline CI/CD",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path=".github/workflows/ci.yml",
                    content_guideline="Pipeline CI/CD com testes, build, security scan e deploy automático"
                ),
                status=TaskStatus.PENDING,
                dependencies=[monitoring_task.task_id],
                acceptance_criteria="Pipeline CI/CD configurado"
            )
        graph.add_task(cicd_task)

        security_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar configuração de segurança",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="security.py",
                    content_guideline="Configurações de segurança com HTTPS, CORS, rate limiting e validações"
                ),
                status=TaskStatus.PENDING,
                dependencies=[cicd_task.task_id],
                acceptance_criteria="Configurações de segurança implementadas"
            )
        graph.add_task(security_task)

    def _get_blog_tasks(self, graph: DependencyGraph):
        """Adiciona tarefas de blog diretamente ao grafo com dependências explícitas."""
        
        models_task = Task(
            task_id=self._generate_next_id(),
            description="Criar modelos de dados para blog (User, Post, Comment)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="models.py", content_guideline="Modelos Flask-SQLAlchemy para User, Post, Comment com relacionamentos."),
            dependencies=[],
            acceptance_criteria="Modelos User, Post, Comment definidos com relacionamentos corretos"
        )
        graph.add_task(models_task)
        
        forms_task = Task(
            task_id=self._generate_next_id(),
            description="Criar formulários de autenticação e post",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="forms.py", content_guideline="Formulários Flask-WTF para login, registro, post e comentário."),
            dependencies=[],
            acceptance_criteria="Formulários WTF para autenticação e posts criados"
        )
        graph.add_task(forms_task)
        
        app_task = Task(
            task_id=self._generate_next_id(),
            description="Criar aplicação Flask principal com rotas",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="app.py", content_guideline="Aplicação Flask com rotas de autenticação e CRUD de posts, usando os modelos e formulários."),
            dependencies=[models_task.task_id, forms_task.task_id],
            acceptance_criteria="Aplicação Flask com autenticação e CRUD de posts funcionando"
        )
        graph.add_task(app_task)
        
        base_template_task = Task(
            task_id=self._generate_next_id(),
            description="Criar template base HTML com navbar",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="templates/base.html", content_guideline="Template base com Bootstrap, navbar, flash messages e block content."),
            dependencies=[],
            acceptance_criteria="Template base com navbar e sistema de mensagens criado"
        )
        graph.add_task(base_template_task)
        
        index_template_task = Task(
            task_id=self._generate_next_id(),
            description="Criar página inicial do blog (index.html)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="templates/index.html", content_guideline="Página que estende base.html e lista todos os posts."),
            dependencies=[base_template_task.task_id, app_task.task_id],
            acceptance_criteria="Página inicial listando posts criada"
        )
        graph.add_task(index_template_task)
        
        post_template_task = Task(
            task_id=self._generate_next_id(),
            description="Criar página de visualização de post (post.html)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="templates/post.html", content_guideline="Página que exibe um post e seus comentários."),
            dependencies=[base_template_task.task_id, app_task.task_id],
            acceptance_criteria="Página de post individual com comentários criada"
        )
        graph.add_task(post_template_task)
        
        init_db_task = Task(
            task_id=self._generate_next_id(),
            description="Criar script de inicialização do banco de dados",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="init_db.py", content_guideline="Script para criar tabelas e popular com dados de exemplo."),
            dependencies=[app_task.task_id],
            acceptance_criteria="Script de inicialização que cria DB e dados exemplo"
        )
        graph.add_task(init_db_task)

    def _get_api_tasks(self) -> List[Task]:
        """Tarefas específicas para APIs REST"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar API REST",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="api.py",
                    content_guideline="API REST com endpoints CRUD, autenticação, validação e documentação"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="API REST funcional implementada"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Criar schemas de validação",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="schemas.py",
                    content_guideline="Schemas Marshmallow/Pydantic para validação de dados da API"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Schemas de validação implementados"
            )
        ]

    def _get_ecommerce_tasks(self) -> List[Task]:
        """Tarefas específicas para e-commerce (mantendo a lógica existente)"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar modelos de e-commerce",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="models.py",
                    content_guideline="Modelos para e-commerce: Product, Category, Order, Cart, User, Review"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Modelos de e-commerce implementados"
            )
        ]

    def _get_dashboard_tasks(self) -> List[Task]:
        """Tarefas específicas para dashboards"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar dashboard principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="dashboard.py",
                    content_guideline="Dashboard com gráficos, métricas, filtros e navegação"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Dashboard funcional implementado"
            )
        ]

    def _get_chatbot_tasks(self) -> List[Task]:
        """Tarefas específicas para chatbots"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar lógica do chatbot",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="bot.py",
                    content_guideline="Chatbot com processamento de linguagem natural, respostas automáticas e integração"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Chatbot funcional implementado"
            )
        ]

    def _get_analytics_tasks(self) -> List[Task]:
        """Tarefas específicas para análise de dados"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar pipeline de análise",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="analytics.py",
                    content_guideline="Pipeline de análise de dados com visualizações, relatórios e métricas"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Pipeline de análise implementado"
            )
        ]

    def _get_generic_tasks(self) -> List[Task]:
        """Tarefas para projetos genéricos"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Criar aplicação principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="main.py",
                    content_guideline="Aplicação principal com estrutura básica e funcionalidades core"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Aplicação principal implementada"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Criar configurações",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="config.py",
                    content_guideline="Configurações do projeto com variáveis de ambiente e settings"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Configurações implementadas"
            )
        ]

    async def replan_task(self, failed_task: Task, error_feedback: str) -> List[Task]:
        """Replanneja uma tarefa que falhou com análise inteligente"""
        try:
            # Detectar loop infinito de correção
            if "Corrigir erro na tarefa:" in failed_task.description:
                logger.warning(f"Detectado loop de correção para tarefa {failed_task.task_id}. Tentando abordagem alternativa.")
                
                # Extrair descrição original removendo prefixos de correção
                original_description = failed_task.description
                while "Corrigir erro na tarefa:" in original_description:
                    original_description = original_description.replace("Corrigir erro na tarefa:", "").strip()
                
                # Se ainda está vazio, falhar graciosamente
                if not original_description:
                    logger.error("Não foi possível extrair descrição original da tarefa. Cancelando replanejamento.")
                    return []
                
                # Criar tarefa alternativa com abordagem diferente
                alternative_task = Task(
                    task_id=self._generate_next_id(),
                    description=f"Implementar alternativa para: {original_description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria=f"Abordagem alternativa para: {failed_task.acceptance_criteria}",
                    max_retries=2  # Limite menor para evitar loops
                )
                
                return [alternative_task]
            
            # Analisar tipo de erro para replanejamento inteligente
            logger.info(f"Replanejando tarefa {failed_task.task_id} devido a erro: {error_feedback[:200]}...")
            
            # Determinar estratégia baseada no tipo de erro
            if "validação semântica" in error_feedback.lower():
                # Problema de validação - simplificar tarefa
                simplified_task = Task(
                    task_id=self._generate_next_id(),
                    description=f"Versão simplificada: {failed_task.description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria=f"Versão simplificada de: {failed_task.acceptance_criteria}",
                    max_retries=2
                )
                return [simplified_task]
            
            elif "timeout" in error_feedback.lower() or "tempo" in error_feedback.lower():
                # Problema de performance - dividir tarefa
                subtask1 = Task(
                    task_id=self._generate_next_id(),
                    description=f"Parte 1 de: {failed_task.description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria=f"Primeira parte de: {failed_task.acceptance_criteria}",
                    max_retries=2
                )
                
                subtask2 = Task(
                    task_id=self._generate_next_id(),
                    description=f"Parte 2 de: {failed_task.description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[subtask1.task_id],
                    acceptance_criteria=f"Segunda parte de: {failed_task.acceptance_criteria}",
                    max_retries=2
                )
                
                return [subtask1, subtask2]
            
            else:
                # Erro genérico - tentar com ajustes mínimos
                adjusted_task = Task(
                    task_id=self._generate_next_id(),
                    description=f"Revisão: {failed_task.description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria=f"Versão revisada de: {failed_task.acceptance_criteria}",
                    max_retries=1  # Apenas uma tentativa para evitar loops
                )
                
                return [adjusted_task]
            
        except Exception as e:
            logger.error(f"Erro ao replanejar tarefa: {e}")
            return []

    async def generate_tasks_from_blueprint(self, blueprint_name: str) -> List[Task]:
        """Baseado em um blueprint, gera um conjunto de tarefas"""
        if not self.context_manager:
            logger.warning("Context manager não disponível para blueprint")
            return []
            
        # Exemplo simplificado
        tasks = []
        task = Task(
            task_id=self._generate_next_id(),
            description=f"Criar estrutura inicial para {blueprint_name}",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="src/project_structure.json",
                content_guideline="Definir estrutura base conforme blueprint solicitado"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Estrutura inicial do projeto criada conforme blueprint"
        )
        tasks.append(task)
        
        return tasks

    def get_pending_tasks(self) -> List[Task]:
        """Retorna todas as tarefas pendentes"""
        pending = [task for task_id, task in self.active_tasks.items() if task.status == TaskStatus.PENDING]
        return sorted(pending, key=lambda t: t.description)

    def get_completed_tasks(self) -> List[Task]:
        """Retorna todas as tarefas concluídas"""
        return [task for task_id, task in self.active_tasks.items() if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]

    def _resolve_dependency_chain(self, task_id: str) -> bool:
        """Verifica se todas as dependências de uma task estão concluídas"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        for dep in task.dependencies:
            if dep.depends_on not in self.active_tasks:
                continue
            if self.active_tasks[dep.depends_on].status != TaskStatus.COMPLETED:
                return False
        return True

    async def execute_task(self, task_id: str) -> Union[bool, Exception]:
        """Executa uma tarefa específica e atualiza seu status"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False, ValueError("Tarefa não encontrada")

        logger.info(f"Executando tarefa {task_id}: {task.description}")
        task.start_time = datetime.now()

        try:
            if task.type == TaskType.CREATE_FILE:
                await self._execute_create_file_task(task)
            elif task.type == TaskType.MODIFY_FILE:
                await self._execute_modify_file_task(task)
            # ... outros tipos similarmente

            task.status = TaskStatus.COMPLETED
            return True, None
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            return False, e

    async def manage_workflow(self) -> Tuple[bool, str]:
        """Gera e gerencia o fluxo de trabalho através das tarefas"""
        active_context = self.context_manager.get_active_context()
        if not active_context:
            logger.error("Nenhum contexto ativo encontrado para planejamento")
            return False, "Contexto não configurado"

        tasks_to_run = self.get_pending_tasks()
        if not tasks_to_run:
            logger.info("Nenhuma tarefa pendente disponível")
            return False, "Nenhuma tarefa para executar"

        # Executa todas as tarefas pendentes
        success_count = 0
        for task in tasks_to_run:
            task_id = task.task_id
            success, error = await self.execute_task(task_id)
            if not success:
                logger.error(f"Falha na execução de {task_id}: {str(error)}")
                # Gera tarefa de fallback
                await self.recover_problematic_task(task, str(error))
            else:
                success_count += 1

        return True, f"{success_count}/{len(tasks_to_run)} tarefas concluídas"

    async def recover_problematic_task(self, original_task: Task, error_details: str) -> bool:
        """Recupera problemas identificados durante a execução de uma tarefa"""
        recovery_prompt = f"""
        Contexto: Tarefa falhou com o seguinte erro:
        {error_details}

        Por favor, sugira as ações necessárias para corrigir este problema.
        Você pode:
        - Propor uma nova tarefa específica para correção
        - Identificar dependência faltante
        - Sugerir modificação em tarefa existente
        """

        response = await self.get_ai_suggestion(recovery_prompt)
        if "nova_tarefa" in response.lower():
            # Processar sugestão de nova tarefa
            return self.create_recovery_task(response, error_details)
        elif "dependência" in response.lower():
            # Processar dependência faltante
            return self.fix_dependency_error(original_task.task_id)
        # ... outros casos...

    async def get_ai_suggestion(self, context: str) -> str:
        """Utiliza IA para obter sugestões de recuperação baseadas no contexto"""
        # Implementação para chamar API de IA ou service externo
        return "Sugestão de recuperação baseada na análise do erro"

    async def create_recovery_task(self, suggestion: str, error: str) -> bool:
        """Cria uma tarefa específica para rejuvenescer o contexto atual"""
        task_id = self.next_task_id()
        
        # Analisa a sugestão para determinar o tipo de tarefa
        task_type = self._identify_task_type_from_suggestion(suggestion)
        
        # Cria estrutura de details com base no tipo
        details = self._create_task_details_from_suggestion(task_type, error, suggestion)
        
        # Cria uma nova tarefa de recuperação
        recovery_task = Task(
            task_id=task_id,
            description=f"Recuperação automática de erro: {error[:50]}...",
            type=task_type,
            details=details,
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria=f"Erro corrigido: {error[:50]}..."
        )
        
        self.active_tasks[task_id] = recovery_task
        logger.info(f"Tarefa de recuperação criada: {recovery_task.task_id}")
        return True

    def _identify_task_type_from_suggestion(self, suggestion: str) -> TaskType:
        """Determina o tipo de task baseado na sugestão de recuperação"""
        # Lógica para mapear palavras-chave na sugestão para tipos específicos
        if any(word in suggestion.lower() for word in ["corrigir", "reparar", "corrigir"]):
            return TaskType.MODIFY_FILE
        elif "criar" in suggestion.lower() or "novo" in suggestion.lower():
            return TaskType.CREATE_FILE
        else:
            return TaskType.EXECUTE_COMMAND

    def _create_task_details_from_suggestion(self, task_type: TaskType, error: str, suggestion: str):
        """Cria um objeto de detalhes de task baseado na sugestão e erro"""
        # Baseado no tipo de task identificado, cria os detalhes específicos
        if task_type == TaskType.CREATE_FILE:
            return TaskDetailsCreateFile(
                file_path=self._define_recovery_path(error),
                content_guideline=f" Corrigir o erro: {error[:80]}"
            )
        elif task_type == TaskType.MODIFY_FILE:
            return TaskDetailsModifyFile(
                file_path=self._define_recovery_path(error),
                modification_guideline=f"Corrigir o erro: {error[:80]}"
            )
        else:
            return TaskDetailsExecuteCommand(
                command_description=f"Executar correção para: {error[:80]}",
                expected_outcome="Correção do erro identificado"
            )

    def _define_recovery_path(self, error: str) -> str:
        """Determina o caminho do arquivo para ação de recuperação"""
        # Lógica para identificar o arquivo relevante para recuperação
        return "src/recovery.patch"

    async def analyze_failure_patterns(self, task_id: str, error_info: dict) -> dict:
        """
        Analisa padrões de falha para identificar problemas recorrentes
        e sugerir melhorias proativas.
        """
        if task_id not in self.failure_history:
            self.failure_history[task_id] = []
        
        self.failure_history[task_id].append({
            'timestamp': datetime.now().isoformat(),
            'error_info': error_info,
            'attempt_number': len(self.failure_history[task_id]) + 1
        })
        
        # Analisa padrões se há múltiplas falhas
        if len(self.failure_history[task_id]) >= 2:
            patterns = self._extract_failure_patterns(self.failure_history[task_id])
            recovery_strategy = self._generate_recovery_strategy(patterns)
            self.recovery_strategies[task_id] = recovery_strategy
            
            logger.warning(f"Padrão de falha detectado para tarefa {task_id}: {patterns}")
            return {
                'pattern_detected': True,
                'patterns': patterns,
                'recovery_strategy': recovery_strategy
            }
        
        return {'pattern_detected': False}

    def _extract_failure_patterns(self, failure_history: List[dict]) -> dict:
        """Extrai padrões comuns das falhas históricas"""
        patterns = {
            'common_errors': [],
            'failure_frequency': len(failure_history),
            'error_types': []
        }
        
        for failure in failure_history:
            error_info = failure.get('error_info', {})
            error_type = error_info.get('type', 'unknown')
            error_message = error_info.get('message', '')
            
            patterns['error_types'].append(error_type)
            
            # Identifica erros comuns
            if 'permission' in error_message.lower():
                patterns['common_errors'].append('permission_issues')
            elif 'not found' in error_message.lower():
                patterns['common_errors'].append('missing_dependencies')
            elif 'syntax' in error_message.lower():
                patterns['common_errors'].append('syntax_errors')
            elif 'timeout' in error_message.lower():
                patterns['common_errors'].append('timeout_issues')
        
        return patterns

    def _generate_recovery_strategy(self, patterns: dict) -> dict:
        """Gera estratégia de recuperação baseada nos padrões identificados"""
        strategy = {
            'approach': 'adaptive',
            'actions': [],
            'priority': 'high' if patterns['failure_frequency'] > 3 else 'medium'
        }
        
        common_errors = patterns.get('common_errors', [])
        
        if 'permission_issues' in common_errors:
            strategy['actions'].append({
                'type': 'fix_permissions',
                'description': 'Corrigir problemas de permissão de arquivos'
            })
        
        if 'missing_dependencies' in common_errors:
            strategy['actions'].append({
                'type': 'install_dependencies',
                'description': 'Instalar dependências faltantes'
            })
        
        if 'syntax_errors' in common_errors:
            strategy['actions'].append({
                'type': 'code_review',
                'description': 'Revisar código para corrigir erros de sintaxe'
            })
        
        if 'timeout_issues' in common_errors:
            strategy['actions'].append({
                'type': 'optimize_performance',
                'description': 'Otimizar performance para evitar timeouts'
            })
        
        # Se padrão não identificado, usa estratégia genérica
        if not strategy['actions']:
            strategy['actions'].append({
                'type': 'generic_retry',
                'description': 'Tentar abordagem alternativa'
            })
        
        return strategy

    async def apply_recovery_strategy(self, task_id: str, failed_task: Task) -> List[Task]:
        """
        Aplica estratégia de recuperação específica para uma tarefa falha
        """
        if task_id not in self.recovery_strategies:
            logger.info(f"Nenhuma estratégia específica para {task_id}, usando abordagem padrão")
            return await self.replan_task(failed_task, "Falha genérica")
        
        strategy = self.recovery_strategies[task_id]
        recovery_tasks = []
        
        for action in strategy['actions']:
            recovery_task = self._create_recovery_task_from_action(action, failed_task)
            if recovery_task:
                recovery_tasks.append(recovery_task)
        
        logger.info(f"Aplicando estratégia de recuperação para {task_id}: {len(recovery_tasks)} tarefas criadas")
        return recovery_tasks

    def _create_recovery_task_from_action(self, action: dict, original_task: Task) -> Optional[Task]:
        """Cria tarefa de recuperação baseada na ação especificada"""
        action_type = action.get('type')
        description = action.get('description')
        
        if action_type == 'fix_permissions':
            return Task(
                task_id=self._generate_next_id(),
                description=f"Corrigir permissões: {description}",
                type=TaskType.EXECUTE_COMMAND,
                details=TaskDetailsExecuteCommand(
                    command_description="Corrigir permissões de arquivos e diretórios",
                    expected_outcome="Permissões adequadas configuradas"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Permissões corrigidas com sucesso"
            )
        
        elif action_type == 'install_dependencies':
            return Task(
                task_id=self._generate_next_id(),
                description=f"Instalar dependências: {description}",
                type=TaskType.EXECUTE_COMMAND,
                details=TaskDetailsExecuteCommand(
                    command_description="Instalar todas as dependências necessárias",
                    expected_outcome="Dependências instaladas e funcionais"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Dependências instaladas com sucesso"
            )
        
        elif action_type == 'code_review':
            return Task(
                task_id=self._generate_next_id(),
                description=f"Revisar código: {description}",
                type=TaskType.MODIFY_FILE,
                details=TaskDetailsModifyFile(
                    file_path=getattr(original_task.details, 'file_path', 'src/main.py'),
                    modification_guideline="Revisar e corrigir erros de sintaxe e lógica"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Código revisado e corrigido"
            )
        
        elif action_type == 'optimize_performance':
            return Task(
                task_id=self._generate_next_id(),
                description=f"Otimizar performance: {description}",
                type=TaskType.MODIFY_FILE,
                details=TaskDetailsModifyFile(
                    file_path=getattr(original_task.details, 'file_path', 'src/main.py'),
                    modification_guideline="Otimizar código para melhor performance e evitar timeouts"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Performance otimizada"
            )
        
        else:  # generic_retry
            return Task(
                task_id=self._generate_next_id(),
                description=f"Retry genérico: {original_task.description}",
                type=original_task.type,
                details=original_task.details,
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria=f"Retry bem-sucedido: {original_task.acceptance_criteria}"
            )
        
        return None

    def get_failure_statistics(self) -> dict:
        """Retorna estatísticas de falhas para análise"""
        total_failures = sum(len(failures) for failures in self.failure_history.values())
        failed_tasks = len(self.failure_history)
        
        if failed_tasks == 0:
            return {'total_failures': 0, 'failed_tasks': 0, 'average_failures_per_task': 0}
        
        return {
            'total_failures': total_failures,
            'failed_tasks': failed_tasks,
            'average_failures_per_task': total_failures / failed_tasks,
            'most_problematic_tasks': self._get_most_problematic_tasks()
        }

    def _get_most_problematic_tasks(self) -> List[dict]:
        """Identifica as tarefas mais problemáticas"""
        problematic = []
        for task_id, failures in self.failure_history.items():
            if len(failures) > 2:  # Mais de 2 falhas
                problematic.append({
                    'task_id': task_id,
                    'failure_count': len(failures),
                    'last_failure': failures[-1]['timestamp']
                })
        
        return sorted(problematic, key=lambda x: x['failure_count'], reverse=True)

    # ============================================================================
    # MÉTODOS A2A (Agent-to-Agent) - Parallel Handoff
    # ============================================================================
    
    async def _process_received_handoff(self, request):
        """Processa handoff recebido - implementação específica do PlannerAgent"""
        from evolux_engine.core.agent_handoff import HandoffType
        
        if request.handoff_type == HandoffType.CONTEXT_TRANSFER:
            await self._handle_context_transfer(request)
        elif request.handoff_type == HandoffType.TASK_DELEGATION:
            await self._handle_task_delegation(request)
        elif request.handoff_type == HandoffType.KNOWLEDGE_SHARE:
            await self._handle_knowledge_share(request)
        else:
            logger.warning(f"PlannerAgent: Tipo de handoff não suportado: {request.handoff_type}")
    
    async def _handle_context_transfer(self, request):
        """Processa transferência de contexto de outro agente"""
        context_data = request.data_payload.get('project_context', {})
        
        logger.info(f"PlannerAgent: Recebendo contexto do projeto {context_data.get('project_id')}")
        
        # Armazenar contexto recebido
        self.received_contexts[request.handoff_id] = {
            'context': context_data,
            'sender': request.sender_agent_id,
            'received_at': datetime.utcnow()
        }
        
        # Se incluir task_queue, mesclar com tarefas existentes
        if 'task_queue' in request.data_payload:
            received_tasks = request.data_payload['task_queue']
            logger.info(f"PlannerAgent: Recebendo {len(received_tasks)} tarefas do agente {request.sender_agent_id}")
            
            # Converter de dict para Task objects se necessário
            for task_dict in received_tasks:
                if isinstance(task_dict, dict):
                    # Reconstruir objeto Task
                    task = Task(
                        task_id=task_dict.get('task_id'),
                        description=task_dict.get('description'),
                        type=TaskType(task_dict.get('type')) if task_dict.get('type') else TaskType.CREATE_FILE,
                        status=TaskStatus(task_dict.get('status')) if task_dict.get('status') else TaskStatus.PENDING,
                        details=None,  # Simplificado por ora
                        dependencies=task_dict.get('dependencies', []),
                        acceptance_criteria=task_dict.get('acceptance_criteria', '')
                    )
                    
                    # Adicionar à fila se não existe
                    if not any(t.task_id == task.task_id for t in self.project_context.task_queue):
                        self.project_context.task_queue.append(task)
                        logger.info(f"PlannerAgent: Tarefa {task.task_id} adicionada à fila local")
    
    async def _handle_task_delegation(self, request):
        """Processa delegação de tarefa de outro agente"""
        task_data = request.data_payload.get('task', {})
        execution_context = request.data_payload.get('execution_context', {})
        
        logger.info(f"PlannerAgent: Recebendo delegação da tarefa {task_data.get('task_id')}")
        
        # Reconstruir objeto Task
        delegated_task = Task(
            task_id=task_data.get('task_id'),
            description=task_data.get('description'),
            type=TaskType(task_data.get('type')) if task_data.get('type') else TaskType.CREATE_FILE,
            status=TaskStatus.PENDING,  # Reset para pending
            details=None,  # Simplificado
            dependencies=task_data.get('dependencies', []),
            acceptance_criteria=task_data.get('acceptance_criteria', '')
        )
        
        # Adicionar à fila de tarefas
        if self.project_context:
            self.project_context.task_queue.append(delegated_task)
            await self.project_context.save_context()
        else:
            self.active_tasks[delegated_task.task_id] = delegated_task
        
        # Armazenar informações da delegação
        self.delegated_tasks[delegated_task.task_id] = {
            'delegated_by': request.sender_agent_id,
            'execution_context': execution_context,
            'received_at': datetime.utcnow(),
            'handoff_id': request.handoff_id
        }
        
        logger.info(f"PlannerAgent: Tarefa {delegated_task.task_id} aceita para execução")
    
    async def _handle_knowledge_share(self, request):
        """Processa compartilhamento de conhecimento de outro agente"""
        knowledge_data = request.data_payload.get('knowledge', {})
        knowledge_type = request.data_payload.get('knowledge_type', 'general')
        source_agent = request.data_payload.get('source_agent')
        
        logger.info(f"PlannerAgent: Recebendo conhecimento '{knowledge_type}' do agente {source_agent}")
        
        # Processar conhecimento baseado no tipo
        if knowledge_type == 'planning_patterns':
            await self._integrate_planning_patterns(knowledge_data)
        elif knowledge_type == 'failure_patterns':
            await self._integrate_failure_patterns(knowledge_data)
        elif knowledge_type == 'task_templates':
            await self._integrate_task_templates(knowledge_data)
        else:
            # Armazenar conhecimento genérico
            if not hasattr(self, 'shared_knowledge'):
                self.shared_knowledge = {}
            self.shared_knowledge[knowledge_type] = {
                'data': knowledge_data,
                'source': source_agent,
                'received_at': datetime.utcnow()
            }
        
        logger.info(f"PlannerAgent: Conhecimento '{knowledge_type}' integrado com sucesso")
    
    async def _integrate_planning_patterns(self, patterns_data):
        """Integra padrões de planejamento recebidos"""
        # Exemplo: integrar novos templates de tarefas ou estratégias de planejamento
        if 'task_generation_strategies' in patterns_data:
            strategies = patterns_data['task_generation_strategies']
            logger.info(f"PlannerAgent: Integrando {len(strategies)} estratégias de geração de tarefas")
            # Implementar integração específica
    
    async def _integrate_failure_patterns(self, failure_data):
        """Integra padrões de falha recebidos"""
        if 'common_failures' in failure_data:
            failures = failure_data['common_failures']
            for failure_pattern in failures:
                # Adicionar ao histórico local de falhas para aprendizado
                pattern_id = failure_pattern.get('pattern_id', 'unknown')
                if pattern_id not in self.recovery_strategies:
                    self.recovery_strategies[pattern_id] = failure_pattern.get('recovery_strategy', {})
                    logger.info(f"PlannerAgent: Nova estratégia de recuperação adicionada: {pattern_id}")
    
    async def _integrate_task_templates(self, templates_data):
        """Integra templates de tarefas recebidos"""
        if 'templates' in templates_data:
            templates = templates_data['templates']
            logger.info(f"PlannerAgent: Integrando {len(templates)} templates de tarefas")
            # Implementar integração de templates
    
    async def delegate_complex_planning(self, target_agent: str, planning_context: dict) -> bool:
        """Delega planejamento complexo para outro agente especializado"""
        try:
            response = await self.a2a_integration.delegate_task(
                sender_agent_id="planner",
                receiver_agent_id=target_agent,
                task=Task(
                    task_id=self._generate_next_id(),
                    description="Planejamento complexo especializado",
                    type=TaskType.EXECUTE_COMMAND,
                    status=TaskStatus.PENDING,
                    details=None,
                    dependencies=[],
                    acceptance_criteria="Plano detalhado gerado"
                ),
                execution_context=planning_context,
                priority=8
            )
            
            return response.status.value == "completed"
            
        except Exception:
            logger.exception("Erro ao gerar plano inicial")
            return False
    
    async def share_planning_knowledge(self, target_agents: List[str]):
        """Compartilha conhecimento de planejamento com outros agentes"""
        planning_knowledge = {
            'successful_patterns': self._extract_successful_patterns(),
            'failure_recovery': dict(self.recovery_strategies),
            'task_generation_metrics': await self._get_planning_metrics()
        }
        
        try:
            responses = await self.a2a_integration.share_knowledge(
                sender_agent_id="planner",
                receiver_agents=target_agents,
                knowledge_data=planning_knowledge,
                knowledge_type="planning_patterns"
            )
            
            successful_shares = sum(1 for r in responses if hasattr(r, 'status') and r.status.value == "completed")
            logger.info(f"PlannerAgent: Conhecimento compartilhado com {successful_shares}/{len(target_agents)} agentes")
            
        except Exception as e:
            logger.error(f"Erro no compartilhamento de conhecimento: {e}")
    
    def _extract_successful_patterns(self) -> dict:
        """Extrai padrões de planejamento bem-sucedidos"""
        # Implementar análise de padrões de sucesso
        return {
            'high_success_types': ['api', 'web_app'],
            'optimal_task_counts': {'simple': 4, 'complex': 12},
            'effective_dependencies': []
        }
    
    async def _get_planning_metrics(self) -> dict:
        """Obtém métricas de planejamento"""
        return {
            'total_plans_generated': len(self.active_tasks) + (len(self.project_context.task_queue) if self.project_context else 0),
            'average_tasks_per_plan': 8,  # Calculado dinamicamente
            'success_rate': 0.85,  # Calculado baseado no histórico
            'most_used_task_types': ['CREATE_FILE', 'EXECUTE_COMMAND']
        }
