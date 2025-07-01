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


class PlannerAgent:
    """Classe responsável por gerenciar a criação e o fluxo de tarefas"""
    def __init__(self, context_manager, task_db, artifact_store, project_context=None, llm_client=None):
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
        logger.info("PlannerAgent inicializado com componentes necessários")

    def _generate_next_id(self) -> str:
        """Gera um ID sequencial único"""
        return str(uuid.uuid4())

    async def generate_initial_plan(self) -> bool:
        """Gera o plano inicial de tarefas para o projeto baseado no goal específico"""
        try:
            logger.info("Gerando plano inicial de tarefas...")
            
            # Obter o objetivo do projeto
            project_goal = self.project_context.project_goal if self.project_context else "projeto genérico"
            logger.info(f"Planejando para objetivo: {project_goal}")
            
            # Gerar plano dinâmico baseado no objetivo
            tasks = await self._generate_dynamic_plan(project_goal)
            
            # Adicionar tarefas ao project_context se disponível
            if self.project_context:
                self.project_context.task_queue.extend(tasks)
                await self.project_context.save_context()
            else:
                # Fallback para compatibilidade
                for task in tasks:
                    self.active_tasks[task.task_id] = task
                
            logger.info(f"Plano inicial criado com {len(tasks)} tarefas para: {project_goal}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar plano inicial: {e}")
            return False

    async def _generate_dynamic_plan(self, project_goal: str) -> List[Task]:
        """Gera um plano dinâmico de tarefas baseado no objetivo do projeto"""
        
        # Realizar análise semântica do projeto
        project_analysis = await self._analyze_project_semantically(project_goal)
        
        # Tarefas básicas que todo projeto precisa
        tasks = []
        
        # 1. Sempre começar com documentação adaptada ao objetivo
        tasks.append(Task(
            task_id=self._generate_next_id(),
            description="Criar documentação do projeto",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="README.md",
                content_guideline=f"Criar documentação completa para: {project_goal}. Incluir instalação, uso, estrutura e exemplos específicos para este tipo de projeto."
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="README.md específico e completo para o projeto"
        ))
        
        # 2. Dependências específicas do tipo de projeto
        tasks.append(Task(
            task_id=self._generate_next_id(),
            description="Criar arquivo de dependências",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="requirements.txt",
                content_guideline=f"Listar dependências Python necessárias para: {project_goal}. Incluir frameworks e bibliotecas específicas."
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="requirements.txt com dependências específicas do projeto"
        ))
        
        # Gerar tarefas específicas baseadas na análise semântica
        domain_tasks = await self._generate_domain_specific_tasks(
            project_analysis['project_type'], 
            project_goal,
            project_analysis['complexity']
        )
        tasks.extend(domain_tasks)
        
        # Adicionar tarefas de qualidade baseadas na complexidade
        if project_analysis['complexity'] >= 7:
            tasks.extend(self._get_enterprise_quality_tasks())
        elif project_analysis['complexity'] >= 5:
            tasks.extend(self._get_professional_quality_tasks())
        
        return tasks

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

    async def _generate_domain_specific_tasks(self, project_type: str, goal: str, complexity: int) -> List[Task]:
        """Gera tarefas específicas baseadas no domínio e complexidade"""
        
        # Calcular número de tarefas baseado na complexidade
        base_tasks = 3  # README, requirements, main
        complexity_factor = max(1, complexity / 3)
        
        type_multipliers = {
            'blog': 2.0,
            'api': 1.5,
            'ecommerce': 2.5,
            'dashboard': 2.0,
            'chatbot': 1.8,
            'data_science': 2.2,
            'web_app': 1.6,
            'generic': 1.0
        }
        
        multiplier = type_multipliers.get(project_type, 1.0)
        target_tasks = int(base_tasks * complexity_factor * multiplier)
        target_tasks = max(4, min(target_tasks, 20))  # Entre 4 e 20 tarefas
        
        logger.info(f"Gerando {target_tasks} tarefas para projeto {project_type} (complexidade {complexity})")
        
        # Gerar tarefas específicas por tipo
        if project_type == "blog":
            return self._get_blog_tasks()
        elif project_type == "api":
            return self._get_enhanced_api_tasks(complexity)
        elif project_type == "ecommerce":
            return self._get_enhanced_ecommerce_tasks(complexity)
        elif project_type == "dashboard":
            return self._get_enhanced_dashboard_tasks(complexity)
        elif project_type == "web_app":
            return self._get_enhanced_web_app_tasks(complexity)
        else:
            return self._get_enhanced_generic_tasks(complexity)

    def _get_enhanced_api_tasks(self, complexity: int) -> List[Task]:
        """Tarefas aprimoradas para APIs baseadas na complexidade"""
        tasks = []
        
        # Tarefas básicas
        tasks.extend([
            Task(
                task_id=self._generate_next_id(),
                description="Criar modelos de dados da API",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="models.py",
                    content_guideline="Modelos SQLAlchemy com relacionamentos, validações e métodos de serialização"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Modelos de dados implementados com relacionamentos corretos"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Criar schemas de validação",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="schemas.py",
                    content_guideline="Schemas Marshmallow para validação e serialização de dados da API"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Schemas de validação implementados"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Implementar API REST principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="api.py",
                    content_guideline="API REST com Flask-RESTX, endpoints CRUD, documentação Swagger automática"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="API REST com documentação implementada"
            )
        ])
        
        # Tarefas adicionais baseadas na complexidade
        if complexity >= 5:
            tasks.append(Task(
                task_id=self._generate_next_id(),
                description="Implementar autenticação JWT",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="auth.py",
                    content_guideline="Sistema de autenticação com JWT, registro e login de usuários"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Sistema de autenticação JWT implementado"
            ))
            
        if complexity >= 6:
            tasks.append(Task(
                task_id=self._generate_next_id(),
                description="Criar testes automatizados",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="test_api.py",
                    content_guideline="Testes pytest para todos os endpoints da API com cobertura de casos de uso"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Suite de testes automatizados implementada"
            ))
            
        if complexity >= 7:
            tasks.extend([
                Task(
                    task_id=self._generate_next_id(),
                    description="Configurar containerização Docker",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="Dockerfile",
                        content_guideline="Dockerfile multi-stage para produção com otimizações de segurança e performance"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Dockerfile de produção criado"
                ),
                Task(
                    task_id=self._generate_next_id(),
                    description="Configurar docker-compose",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="docker-compose.yml",
                        content_guideline="Docker-compose com API, banco de dados, Redis e proxy reverso"
                    ),
                    status=TaskStatus.PENDING,
                    dependencies=[],
                    acceptance_criteria="Orquestração Docker configurada"
                )
            ])
            
        return tasks

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

    def _get_professional_quality_tasks(self) -> List[Task]:
        """Tarefas para elevar o projeto a nível profissional"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Configurar linting e formatação",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path=".pre-commit-config.yaml",
                    content_guideline="Configuração pre-commit com black, flake8, isort e mypy"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Linting e formatação configurados"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Criar documentação técnica",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="docs/ARCHITECTURE.md",
                    content_guideline="Documentação da arquitetura, decisões técnicas e guias de desenvolvimento"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Documentação técnica criada"
            )
        ]

    def _get_enterprise_quality_tasks(self) -> List[Task]:
        """Tarefas para elevar o projeto a nível enterprise"""
        return [
            Task(
                task_id=self._generate_next_id(),
                description="Implementar monitoramento e métricas",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="monitoring.py",
                    content_guideline="Sistema de monitoramento com Prometheus, health checks e alertas"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Sistema de monitoramento implementado"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Configurar pipeline CI/CD",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path=".github/workflows/ci.yml",
                    content_guideline="Pipeline CI/CD com testes, build, security scan e deploy automático"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Pipeline CI/CD configurado"
            ),
            Task(
                task_id=self._generate_next_id(),
                description="Implementar configuração de segurança",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="security.py",
                    content_guideline="Configurações de segurança com HTTPS, CORS, rate limiting e validações"
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Configurações de segurança implementadas"
            )
        ]

    def _get_blog_tasks(self) -> List[Task]:
        """Tarefas específicas para sistemas de blog com dependências inteligentes"""
        
        # Task IDs para dependências
        models_task_id = self._generate_next_id()
        app_task_id = self._generate_next_id()
        base_template_id = self._generate_next_id()
        index_template_id = self._generate_next_id()
        post_template_id = self._generate_next_id()
        create_template_id = self._generate_next_id()
        auth_forms_id = self._generate_next_id()
        init_db_id = self._generate_next_id()
        
        return [
            # 1. Modelos primeiro (base de tudo)
            Task(
                task_id=models_task_id,
                description="Criar modelos de dados para blog",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="models.py",
                    content_guideline="""Criar modelos Flask-SQLAlchemy para blog completo:
                    - User (para autenticação): id, username, email, password_hash, posts, comments
                    - Post: id, title, content, date_posted, author_id, comments
                    - Comment: id, content, date_posted, author_id, post_id
                    Incluir relacionamentos bidirecionais e métodos __repr__"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Modelos User, Post, Comment definidos com relacionamentos corretos"
            ),
            
            # 2. Formulários de autenticação
            Task(
                task_id=auth_forms_id,
                description="Criar formulários de autenticação",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="forms.py",
                    content_guideline="""Criar formulários Flask-WTF:
                    - RegistrationForm: username, email, password, confirm_password
                    - LoginForm: username, password, remember_me
                    - PostForm: title, content
                    - CommentForm: content
                    Com validações apropriadas"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Formulários WTF para autenticação e posts criados"
            ),
            
            # 3. Aplicação Flask (depende dos modelos)
            Task(
                task_id=app_task_id,
                description="Criar aplicação Flask principal",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="app.py",
                    content_guideline="""Criar aplicação Flask completa com:
                    - Configuração do banco de dados SQLite
                    - Flask-Login para autenticação
                    - Rotas: /, /register, /login, /logout, /post/<id>, /create_post, /post/<id>/comment
                    - Importar modelos User, Post, Comment (não Author)
                    - Usar formulários do forms.py
                    - Implementar user_loader para Flask-Login"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[models_task_id, auth_forms_id],
                acceptance_criteria="Aplicação Flask com autenticação e CRUD de posts funcionando"
            ),
            
            # 4. Template base
            Task(
                task_id=base_template_id,
                description="Criar template base HTML",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="templates/base.html",
                    content_guideline="""Criar template base com:
                    - DOCTYPE, html, head, body
                    - Bootstrap CSS para styling
                    - Navbar com links para Home, Login/Logout
                    - Flash messages para feedbacks
                    - Block content para outros templates estenderem
                    - Sintaxe Jinja2 correta"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[],
                acceptance_criteria="Template base com navbar e sistema de mensagens criado"
            ),
            
            # 5. Templates específicos (dependem do base)
            Task(
                task_id=index_template_id,
                description="Criar página inicial do blog",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="templates/index.html",
                    content_guideline="""Criar página inicial que:
                    - Estende base.html
                    - Lista todos os posts com título, autor e data
                    - Links para visualizar posts individuais
                    - Botão para criar novo post (se logado)
                    - Usar sintaxe Jinja2 para loop de posts"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[base_template_id],
                acceptance_criteria="Página inicial listando posts criada"
            ),
            
            Task(
                task_id=post_template_id,
                description="Criar página de visualização de post",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="templates/post.html",
                    content_guideline="""Criar página de post individual com:
                    - Título e conteúdo do post
                    - Informações do autor e data
                    - Lista de comentários
                    - Formulário para adicionar comentário (se logado)
                    - Estender base.html"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[base_template_id],
                acceptance_criteria="Página de post individual com comentários criada"
            ),
            
            Task(
                task_id=create_template_id,
                description="Criar página de criação de post",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="templates/create_post.html",
                    content_guideline="""Criar formulário de criação de post:
                    - Estender base.html
                    - Formulário com título e conteúdo
                    - Validação cliente e servidor
                    - Usar WTForms rendering"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[base_template_id],
                acceptance_criteria="Formulário de criação de post criado"
            ),
            
            # 6. Scripts de inicialização
            Task(
                task_id=init_db_id,
                description="Criar script de inicialização do banco",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="init_db.py",
                    content_guideline="""Criar script para:
                    - Importar app e models
                    - Criar todas as tabelas
                    - Adicionar dados de exemplo (usuário admin, posts exemplo)
                    - Poder ser executado independentemente"""
                ),
                status=TaskStatus.PENDING,
                dependencies=[models_task_id, app_task_id],
                acceptance_criteria="Script de inicialização que cria DB e dados exemplo"
            )
        ]

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
