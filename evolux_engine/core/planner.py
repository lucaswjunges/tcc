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
logger = get_structured_logger(name="planner")

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

    def _generate_filename_from_description(self, description: str) -> str:
        """Gera um nome de arquivo a partir da descrição da tarefa."""
        import re
        import unicodedata
        
        s = ''.join(c for c in unicodedata.normalize('NFD', description) if unicodedata.category(c) != 'Mn')
        s = s.lower()
        
        match = re.search(r'([a-z0-9_.-]+\.(py|md|txt|json|yml|yaml|html|css|js|sh|dockerfile))', s)
        if match:
            return match.group(1)

        s = re.sub(r'[^\w\s-]', '', s)
        words = s.split()
        common_words = {'e', 'o', 'a', 'de', 'do', 'da', 'com', 'para', 'em', 'um', 'uma', 'os', 'as'}
        action_words = {'criar', 'implementar', 'desenvolver', 'configurar', 'gerar', 'adicionar', 'modificar', 'refatorar', 'testar'}
        
        filtered_words = [word for word in words if word not in common_words and word not in action_words]
        
        if not filtered_words:
            # Fallback com base em palavras de ação se nada mais restar
            filtered_words = [word for word in words if word not in common_words]
            if not filtered_words:
                return "task_file.py"

        filename_base = "_".join(filtered_words[:5])
        
        # Adiciona extensão baseada em palavras-chave
        if any(keyword in s for keyword in ['backend', 'serviço', 'api', 'lógica', 'modelo', 'autenticação', 'script', 'python']):
            filename = f"{filename_base}.py"
        elif any(keyword in s for keyword in ['frontend', 'ui', 'interface', 'página', 'template', 'html']):
            filename = f"{filename_base}.html"
        elif any(keyword in s for keyword in ['estilo', 'css']):
            filename = f"{filename_base}.css"
        elif any(keyword in s for keyword in ['documentação', 'readme', 'docs']):
            filename = f"{filename_base}.md"
        elif any(keyword in s for keyword in ['dependências', 'requirements']):
            filename = "requirements.txt"
        elif any(keyword in s for keyword in ['configuração', 'settings']):
            filename = f"{filename_base}.py"
        elif any(keyword in s for keyword in ['docker-compose', 'compose']):
            filename = "docker-compose.yml"
        elif 'dockerfile' in s:
            filename = "Dockerfile"
        elif any(keyword in s for keyword in ['json']):
            filename = f"{filename_base}.json"
        elif any(keyword in s for keyword in ['yaml', 'yml']):
            filename = f"{filename_base}.yml"
        else:
            filename = f"{filename_base}.py"
            
        return filename.replace("-", "_")

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
        
        logger.info("PlannerAgent initialized with necessary components and A2A capabilities")

    def _generate_next_id(self) -> str:
        """Gera um ID sequencial único"""
        return str(uuid.uuid4())

    async def generate_initial_plan(self) -> bool:
        """Gera o plano inicial de tarefas para o projeto e o estrutura como um DependencyGraph."""
        try:
            logger.info("Generating initial task plan...")
            prompt_mestre = self.project_context.project_goal if self.project_context else "generic project"
            logger.info(f"Prompt Mestre: {prompt_mestre}")

            # Aplicar refinamento de prompt se necessário
            prompt_efetivo = await self._refine_prompt_if_needed(prompt_mestre)
            if prompt_efetivo != prompt_mestre:
                logger.info(f"🎯 Prompt refinado de vago para específico")
                logger.info(f"Prompt Efetivo: {prompt_efetivo}")
                # Log dos prompts para análise (evitando modificar ProjectContext que usa Pydantic)
                logger.info(f"📝 Transformação: {len(prompt_mestre)} chars → {len(prompt_efetivo)} chars")
            else:
                logger.info("✅ Prompt mestre já é suficientemente específico")
                prompt_efetivo = prompt_mestre

            # O DependencyGraph será a fonte da verdade para a estrutura do plano
            dependency_graph = await self._generate_dynamic_plan(prompt_efetivo)
            
            # Popular a task_queue do contexto do projeto a partir do grafo
            if self.project_context:
                all_tasks = dependency_graph.get_all_tasks()
                self.project_context.task_queue = all_tasks
                await self.project_context.save_context()
                logger.info(f"Initial plan created with {len(all_tasks)} tasks and saved to context.")
                # Opcional: Logar a estrutura do grafo para depuração
                # logger.debug(f"Dependency graph generated:\n{dependency_graph.to_mermaid()}")
            else:
                # Fallback para ambientes sem project_context
                self.active_tasks = {task.task_id: task for task in dependency_graph.get_all_tasks()}

            return True
            
        except Exception as e:
            logger.error(f"Error generating initial plan: {e}", exc_info=True)
            return False

    async def _refine_prompt_if_needed(self, prompt_mestre: str) -> str:
        """
        Analisa se o prompt mestre é suficientemente específico.
        Se não, utiliza LLM para criar um prompt efetivo mais detalhado.
        """
        # Primeiro, verificar se o prompt é suficientemente específico
        specificity_score = self._analyze_prompt_specificity(prompt_mestre)
        
        logger.info(f"📊 Prompt specificity score: {specificity_score:.2f}")
        
        # Se o score for baixo (< 0.6), refinar o prompt
        if specificity_score < 0.6:
            logger.info("🔄 Prompt considerado vago - iniciando refinamento...")
            return await self._create_effective_prompt(prompt_mestre, specificity_score)
        else:
            logger.info("✅ Prompt suficientemente específico - usando original")
            return prompt_mestre

    async def improve_plan_with_feedback(self, current_tasks: List[Task], feedback: dict) -> DependencyGraph:
        """
        Melhora o plano atual baseado no feedback do CriticAgent, instruindo o LLM a reestruturar
        a lista de tarefas e suas dependências diretamente.
        """
        if not hasattr(self, 'llm_client') or not self.llm_client:
            logger.warning("LLM client not available for plan improvement. Returning original plan.")
            graph = DependencyGraph()
            for task in current_tasks:
                graph.add_task(task)
            return graph

        try:
            issues = feedback.get('potential_issues', [])
            score = feedback.get('score', 0.0)
            
            logger.info(f"🔄 Improving plan with score {score:.2f} based on {len(issues)} identified issues.")

            # Manter o prompt original detalhado como a fonte da verdade para o objetivo.
            original_goal = self.project_context.project_goal

            # Criar um prompt que instrui o LLM a agir como um gerente de projetos e reestruturar o plano.
            # Função para serializar objetos datetime
            def default_serializer(o):
                if isinstance(o, datetime):
                    return o.isoformat()
                raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

            improvement_prompt = f"""
            Você é um Gerente de Projetos de Software Sênior. Sua tarefa é refatorar um plano de projeto que foi rejeitado por um analista de qualidade.

            **Objetivo Principal do Projeto:**
            {original_goal}

            **Plano Atual (Rejeitado com Score: {score:.2f}):**
            {json.dumps([task.dict() for task in current_tasks], indent=2, default=default_serializer)}

            **Críticas e Problemas Identificados pelo Analista de Qualidade:**
            - {chr(10).join(f"- {issue}" for issue in issues)}

            **Sua Missão:**
            Reestruture o plano de tarefas para resolver TODAS as críticas. O novo plano deve ser mais ágil, permitir paralelismo, integrar segurança e testes desde o início, e ter uma granularidade de tarefas mais adequada.

            **Diretrizes para o Novo Plano:**
            1.  **Agilidade e Paralelismo:** Evite longas cadeias de dependência. Permita que tarefas de backend e frontend ocorram em paralelo sempre que possível.
            2.  **Qualidade Contínua:** Posicione tarefas de configuração de CI/CD e testes no início do projeto.
            3.  **Segurança "By Design":** Integre tarefas de segurança (como configuração de autenticação) no início, não no final.
            4.  **Granularidade:** Quebre tarefas monolíticas (como "Implementar Frontend") em tarefas menores e mais específicas.
            5.  **Dependências Lógicas:** Garanta que as dependências entre as tarefas sejam lógicas e eficientes.

            **Formato de Saída:**
            Responda com um JSON contendo uma única chave "tasks", que é uma lista de tarefas. Cada tarefa deve ter:
            - "id": um número sequencial único para esta lista (ex: 1, 2, 3...).
            - "description": uma descrição clara e concisa da tarefa.
            - "dependencies": uma lista de IDs numéricos das tarefas das quais ela depende. Deixe a lista vazia ([]) se não houver dependências.

            **Exemplo de Saída JSON:**
            {{
              "tasks": [
                {{
                  "id": 1,
                  "description": "Configurar pipeline CI/CD inicial com linting e build",
                  "dependencies": []
                }},
                {{
                  "id": 2,
                  "description": "Definir modelos de dados (ORM) para Usuário e Produto",
                  "dependencies": []
                }},
                {{
                  "id": 3,
                  "description": "Implementar endpoints da API para CRUD de Produtos",
                  "dependencies": [2]
                }}
              ]
            }}

            Agora, gere o novo plano de tarefas em formato JSON.
            """

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": improvement_prompt}],
                temperature=0.3,
                max_tokens=2048  # Aumentar para permitir planos mais detalhados
            )

            if response and response.strip():
                logger.info("📄 Received improved plan from LLM. Parsing and building new graph.")
                try:
                    # Extrair o JSON da resposta do LLM de forma mais robusta
                    response_text = response.strip()
                    json_start_index = response_text.find('{')
                    if json_start_index == -1:
                        raise ValueError("Nenhum JSON encontrado na resposta da LLM.")
                    
                    # Tentar encontrar o final do JSON correspondente
                    json_response_str = response_text[json_start_index:]
                    if "```" in json_response_str:
                        json_response_str = json_response_str.split("```")[0]

                    new_plan_data = json.loads(json_response_str)
                    tasks_data = new_plan_data.get("tasks", [])

                    if not tasks_data:
                        raise ValueError("LLM response did not contain a 'tasks' list.")

                    # Construir o novo grafo de dependências
                    new_graph = DependencyGraph()
                    id_to_uuid_map = {}

                    # Primeira passagem: criar todas as tarefas e mapear IDs numéricos para UUIDs
                    for task_data in tasks_data:
                        new_task_id = self._generate_next_id()
                        id_to_uuid_map[task_data['id']] = new_task_id
                        
                        generated_filename = self._generate_filename_from_description(task_data['description'])
                        new_task = Task(
                            task_id=new_task_id,
                            description=task_data['description'],
                            type=TaskType.CREATE_FILE,  # Default, pode ser refinado depois
                            details=TaskDetailsCreateFile(file_path=generated_filename, content_guideline=task_data['description']),
                            status=TaskStatus.PENDING,
                            dependencies=[], # Será preenchido na segunda passagem
                            acceptance_criteria=f"Funcionalidade '{task_data['description']}' implementada e testada."
                        )
                        new_graph.add_task(new_task)

                    # Segunda passagem: adicionar as dependências usando os UUIDs mapeados
                    for task_data in tasks_data:
                        task_uuid = id_to_uuid_map[task_data['id']]
                        task_obj = new_graph.get_task(task_uuid)
                        
                        dep_uuids = [id_to_uuid_map[dep_id] for dep_id in task_data.get('dependencies', [])]
                        task_obj.dependencies = dep_uuids
                        
                        # Atualizar o grafo com as dependências corretas
                        new_graph.dependencies[task_uuid] = set(dep_uuids)
                        for dep_uuid in dep_uuids:
                            new_graph.dependents.setdefault(dep_uuid, set()).add(task_uuid)

                    logger.info(f"✅ Successfully built new dependency graph with {len(new_graph.get_all_tasks())} improved tasks.")
                    return new_graph

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(f"Error parsing improved plan from LLM: {e}. Response: {response.strip()}")
                    # Fallback: se a análise falhar, retorna o plano original para evitar quebrar o ciclo.
                    graph = DependencyGraph()
                    for task in current_tasks:
                        graph.add_task(task)
                    return graph
            else:
                logger.warning("LLM returned an empty response for plan improvement.")
                raise ValueError("LLM failed to provide an improved plan.")

        except Exception as e:
            logger.error(f"Error improving plan with feedback: {e}", exc_info=True)
            # Fallback em caso de erro inesperado
            graph = DependencyGraph()
            for task in current_tasks:
                graph.add_task(task)
            return graph

    def _analyze_prompt_specificity(self, prompt: str) -> float:
        """
        Analisa a especificidade de um prompt usando métricas heurísticas.
        Retorna score de 0.0 (muito vago) a 1.0 (muito específico).
        """
        if not prompt or len(prompt.strip()) < 10:
            return 0.0
        
        prompt_lower = prompt.lower()
        words = prompt_lower.split()
        word_count = len(words)
        
        # Penalizar prompts muito curtos
        if word_count < 5:
            length_score = 0.2
        elif word_count < 10:
            length_score = 0.4
        elif word_count < 20:
            length_score = 0.7
        else:
            length_score = 1.0
        
        # Verificar palavras vagas (penalizam o score)
        vague_words = [
            'coisa', 'algo', 'sistema', 'aplicação', 'projeto', 'ferramenta',
            'programa', 'software', 'solução', 'plataforma', 'site', 'app'
        ]
        
        specific_words = [
            # Web/Frontend
            'flask', 'django', 'react', 'vue', 'angular', 'bootstrap', 'css', 'html', 'javascript',
            # Backend/API
            'fastapi', 'rest', 'api', 'endpoint', 'microservice', 'graphql', 'oauth', 'jwt',
            # Database
            'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'orm', 'sqlalchemy',
            # Cloud/Infrastructure
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'nginx',
            # Data Science/ML
            'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'jupyter', 'ml', 'ai',
            # Business domains
            'e-commerce', 'fintech', 'crm', 'erp', 'blog', 'forum', 'dashboard',
            # Specific features
            'autenticação', 'pagamento', 'carrinho', 'estoque', 'relatório', 'analytics'
        ]
        
        # Contabilizar palavras vagas vs específicas
        vague_count = sum(1 for word in vague_words if word in prompt_lower)
        specific_count = sum(1 for word in specific_words if word in prompt_lower)
        
        # Score baseado na proporção de palavras específicas
        if word_count == 0:
            word_specificity = 0.0
        else:
            # Penalizar palavras vagas, premiar específicas
            word_specificity = max(0.0, (specific_count - vague_count * 0.5) / word_count)
        
        # Verificar se menciona tecnologias específicas
        tech_bonus = 0.3 if specific_count >= 2 else 0.1 if specific_count >= 1 else 0.0
        
        # Verificar se menciona funcionalidades específicas
        feature_keywords = [
            'crud', 'login', 'registro', 'dashboard', 'relatório', 'api', 'banco de dados',
            'autenticação', 'autorização', 'pagamento', 'carrinho', 'estoque', 'usuário'
        ]
        feature_count = sum(1 for keyword in feature_keywords if keyword in prompt_lower)
        feature_bonus = min(0.2, feature_count * 0.05)
        
        # Score final (média ponderada)
        final_score = (length_score * 0.3 + word_specificity * 0.4 + tech_bonus + feature_bonus)
        
        return min(1.0, final_score)

    async def _create_effective_prompt(self, prompt_mestre: str, specificity_score: float) -> str:
        """
        Usa LLM estrategicamente escolhido para criar um prompt efetivo 
        a partir de um prompt mestre vago.
        """
        if not hasattr(self, 'llm_client') or not self.llm_client:
            logger.warning("LLM client not available for prompt refinement. Using original prompt.")
            return prompt_mestre

        try:
            logger.info("🤖 Usando LLM para refinar prompt vago...")
            
            # Determinar nível de refinamento baseado no score
            if specificity_score < 0.3:
                refinement_level = "extensive"
                example_complexity = "alta complexidade com múltiplas funcionalidades integradas"
            elif specificity_score < 0.5:
                refinement_level = "moderate"
                example_complexity = "complexidade média com funcionalidades essenciais"
            else:
                refinement_level = "light"
                example_complexity = "escopo bem definido"
            
            refinement_prompt = f"""
            Você é um especialista em engenharia de software e análise de requisitos. Sua tarefa é transformar um objetivo vago em um prompt específico e actionable para desenvolvimento de software.

            PROMPT ORIGINAL (VAGO): "{prompt_mestre}"
            NÍVEL DE REFINAMENTO: {refinement_level}
            
            Sua tarefa é criar um prompt efetivo que:
            
            1. **Especifique o tipo de aplicação** (web app, API, CLI tool, data science, etc.)
            2. **Defina tecnologias principais** (Flask, React, FastAPI, Python, etc.)
            3. **Liste funcionalidades específicas** (CRUD, autenticação, dashboard, etc.)
            4. **Inclua requisitos técnicos** (banco de dados, segurança, performance, etc.)
            5. **Mencione entregáveis concretos** (MVP, funcionalidades específicas)
            
            EXEMPLO DE TRANSFORMAÇÃO:
            Vago: "Preciso de um sistema para gerenciar informações"
            Específico: "Desenvolver uma aplicação web usando Flask para gerenciamento de inventário. Preciso de CRUD completo para produtos, sistema de autenticação de usuários, dashboard com relatórios, integração com banco PostgreSQL, e funcionalidades de busca e filtros. A aplicação deve ter interface responsiva e ser deployável em produção."
            
            DIRETRIZES:
            - Assuma {example_complexity} baseado no contexto
            - Seja específico mas realista
            - Inclua tecnologias modernas e práticas
            - Mencione aspectos de produção (deployment, segurança, etc.)
            - Mantenha a essência do objetivo original
            
            RETORNE APENAS O PROMPT REFINADO, SEM EXPLICAÇÕES ADICIONAIS:
            """
            
            # Fazer chamada para o LLM
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": refinement_prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            if response and response.strip():
                refined_prompt = response.strip()
                logger.info(f"✅ Prompt refinado com sucesso ({len(refined_prompt)} chars)")
                return refined_prompt
            else:
                logger.warning("LLM returned empty response for prompt refinement")
                return prompt_mestre
                
        except Exception as e:
            logger.error(f"Error in prompt refinement: {e}")
            return prompt_mestre

    async def _get_project_type(self, goal: str) -> str:
        """
        Usa um prompt focado para determinar o tipo de projeto.
        Corrigido para classificar corretamente aplicações web como 'web_app'.
        """
        # Se não houver cliente LLM, recorra à análise básica melhorada.
        if not hasattr(self, 'llm_client') or not self.llm_client:
            logger.warning("LLM client not available for project type analysis. Using improved basic analysis.")
            return self._analyze_project_type_basic(goal)

        try:
            # Prompt melhorado e mais específico para classificação
            classification_prompt = f"""
            Você é um especialista em classificação de projetos de software. Analise o objetivo e classifique em UMA categoria:
            
            CATEGORIAS DISPONÍVEIS:
            - 'web_app': Aplicações web interativas (Flask, Django, React, lista de tarefas, blog, e-commerce)
            - 'api_service': APIs REST, microserviços, endpoints de dados
            - 'cli_tool': Ferramentas de linha de comando, scripts utilitários
            - 'static_website': Sites estáticos, landing pages, documentação
            - 'data_science': Análise de dados, machine learning, relatórios, Jupyter
            - 'mobile_app': Aplicativos móveis (Android, iOS)
            - 'desktop_app': Aplicações desktop (GUI, Tkinter, PyQt)
            - 'documentation': Documentação técnica, manuais, wikis
            
            REGRAS DE CLASSIFICAÇÃO:
            - Se menciona 'aplicação web', 'lista de tarefas', 'to-do', 'Flask', 'Django' → 'web_app'
            - Se menciona 'banco de dados' E interface web → 'web_app'
            - Se menciona apenas 'API' ou 'REST' sem interface → 'api_service'
            - Se menciona 'análise', 'dados', 'gráficos', 'relatórios' → 'data_science'
            
            OBJETIVO: "{goal}"
            
            Retorne APENAS a categoria (exemplo: web_app)
            """
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            # Limpar a resposta e normalizar
            project_type = response.strip().lower().replace('"', '').replace("'", "")
            
            # Validação rigorosa dos tipos
            valid_types = ['web_app', 'api_service', 'cli_tool', 'static_website', 'data_science', 'mobile_app', 'desktop_app', 'documentation']
            
            if project_type in valid_types:
                logger.info(f"✅ Project classified as '{project_type}' by LLM")
                return project_type
            else:
                logger.warning(f"LLM returned invalid type: '{project_type}'. Using basic analysis.")
                return self._analyze_project_type_basic(goal)

        except Exception as e:
            logger.error(f"Error in LLM classification: {e}. Using basic analysis.")
            return self._analyze_project_type_basic(goal)

    async def _extract_project_info(self, project_goal: str) -> dict:
        """
        Extrai informações específicas do prompt refinado usando LLM.
        Retorna tecnologias, funcionalidades e arquitetura identificadas.
        """
        if not hasattr(self, 'llm_client') or not self.llm_client:
            return self._extract_project_info_basic(project_goal)
        
        try:
            extraction_prompt = f"""
            Analise o seguinte objetivo de projeto e extraia informações específicas em formato JSON:

            OBJETIVO: "{project_goal}"

            Extraia as seguintes informações:
            1. Tecnologias mencionadas (frameworks, linguagens, bancos de dados)
            2. Funcionalidades principais identificadas
            3. Tipo de arquitetura (monolito, microserviços, API, etc.)
            4. Componentes de infraestrutura (Docker, Kubernetes, Redis, etc.)

            FORMATO DE RESPOSTA (JSON):
            {{
                "technologies": ["FastAPI", "React", "PostgreSQL"],
                "features": ["autenticação JWT", "CRUD de produtos", "dashboard"],
                "architecture": "microserviços",
                "infrastructure": ["Docker", "Redis"]
            }}

            Retorne APENAS o JSON, sem explicações:
            """
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            if response and response.strip():
                import json
                try:
                    info = json.loads(response.strip())
                    logger.info(f"📋 Project info extracted: {len(info.get('technologies', []))} techs, {len(info.get('features', []))} features")
                    return info
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM JSON response for project info")
                    return self._extract_project_info_basic(project_goal)
            else:
                return self._extract_project_info_basic(project_goal)
                
        except Exception as e:
            logger.error(f"Error extracting project info: {e}")
            return self._extract_project_info_basic(project_goal)
    
    def _extract_project_info_basic(self, project_goal: str) -> dict:
        """Extração básica de informações do projeto usando análise de texto."""
        goal_lower = project_goal.lower()
        
        # Tecnologias detectadas
        tech_keywords = {
            'fastapi': 'FastAPI', 'flask': 'Flask', 'django': 'Django',
            'react': 'React', 'vue': 'Vue.js', 'angular': 'Angular',
            'postgresql': 'PostgreSQL', 'mysql': 'MySQL', 'mongodb': 'MongoDB',
            'redis': 'Redis', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
            'kafka': 'Apache Kafka', 'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch'
        }
        
        technologies = [tech_name for keyword, tech_name in tech_keywords.items() if keyword in goal_lower]
        
        # Funcionalidades detectadas
        feature_keywords = {
            'autenticação': 'Sistema de autenticação', 'login': 'Login/logout',
            'jwt': 'Autenticação JWT', 'oauth': 'OAuth', 'crud': 'Operações CRUD',
            'dashboard': 'Dashboard', 'relatório': 'Relatórios', 'api': 'API REST',
            'microserviç': 'Microserviços', 'cache': 'Sistema de cache',
            'notification': 'Sistema de notificações', 'email': 'Envio de emails'
        }
        
        features = [feature_name for keyword, feature_name in feature_keywords.items() if keyword in goal_lower]
        
        # Arquitetura
        architecture = "monolito"  # default
        if 'microserviç' in goal_lower or 'microservice' in goal_lower:
            architecture = "microserviços"
        elif any(keyword in goal_lower for keyword in ['api', 'rest', 'endpoint']):
            architecture = "API service"
        
        # Infraestrutura
        infra_keywords = ['docker', 'kubernetes', 'redis', 'kafka', 'nginx']
        infrastructure = [keyword.title() for keyword in infra_keywords if keyword in goal_lower]
        
        return {
            "technologies": technologies,
            "features": features,
            "architecture": architecture,
            "infrastructure": infrastructure
        }

    async def _generate_dynamic_plan(self, project_goal: str) -> DependencyGraph:
        """Gera um plano dinâmico de tarefas e o retorna como um DependencyGraph."""
        graph = DependencyGraph()
        
        # Passo 1: Extrair informações específicas do prompt refinado
        project_info = await self._extract_project_info(project_goal)
        
        # Passo 2: Classificar o tipo de projeto de forma robusta.
        project_type = await self._get_project_type(project_goal)
        logger.info(f"Determined project type: {project_type}")

        # Passo 3: Usar a análise básica para determinar a complexidade.
        project_analysis = self._analyze_project_basic(project_goal)
        complexity = project_analysis['complexity']
        logger.info(f"Determined project complexity: {complexity}")

        # Tarefas básicas que todo projeto precisa (sem dependências)
        readme_task = Task(
            task_id=self._generate_next_id(),
            description="Criar documentação do projeto (README.md)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="README.md", content_guideline=f"Criar um README.md claro e conciso para o projeto: {project_goal}."),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="README.md criado com as informações essenciais do projeto."
        )
        graph.add_task(readme_task)

        reqs_task = Task(
            task_id=self._generate_next_id(),
            description="Criar arquivo de dependências (requirements.txt)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="requirements.txt", content_guideline=f"Listar as dependências Python mínimas para o projeto: {project_goal}."),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="requirements.txt criado com as dependências essenciais."
        )
        graph.add_task(reqs_task)
        
        # Gerar tarefas específicas do domínio usando informações extraídas
        await self._generate_domain_specific_tasks(
            graph,
            project_type, 
            project_goal,
            complexity,
            project_info
        )
        
        # Adicionar tarefas de qualidade (que podem depender de outras)
        if complexity >= 7:
            self._get_enterprise_quality_tasks(graph)
        elif complexity >= 5:
            self._get_professional_quality_tasks(graph)
        
        return graph

    def _analyze_project_type_basic(self, goal: str) -> str:
        """Análise básica melhorada por palavras-chave para classificação de tipo"""
        goal_lower = goal.lower()
        
        # Prioridade para aplicações web (corrige o problema principal)
        web_keywords = ["aplicação web", "web app", "lista de tarefas", "to-do", "todo", "flask", "django", "site", "web"]
        if any(keyword in goal_lower for keyword in web_keywords):
            return "web_app"
        
        # API sem interface web
        api_keywords = ["api", "rest", "microserviço", "microservice", "endpoint"]
        if any(keyword in goal_lower for keyword in api_keywords) and "web" not in goal_lower:
            return "api_service"
        
        # Data Science
        data_keywords = ["análise", "data science", "dados", "relatório", "gráfico", "jupyter", "pandas", "machine learning"]
        if any(keyword in goal_lower for keyword in data_keywords):
            return "data_science"
        
        # CLI Tools
        cli_keywords = ["script", "comando", "cli", "terminal", "linha de comando"]
        if any(keyword in goal_lower for keyword in cli_keywords):
            return "cli_tool"
        
        # Mobile
        mobile_keywords = ["mobile", "android", "ios", "app móvel"]
        if any(keyword in goal_lower for keyword in mobile_keywords):
            return "mobile_app"
        
        # Desktop
        desktop_keywords = ["desktop", "gui", "tkinter", "pyqt"]
        if any(keyword in goal_lower for keyword in desktop_keywords):
            return "desktop_app"
        
        # Documentation
        doc_keywords = ["documentação", "manual", "wiki", "docs"]
        if any(keyword in goal_lower for keyword in doc_keywords):
            return "documentation"
        
        # Default para web_app se contém termos relacionados a interface
        interface_keywords = ["interface", "página", "formulário", "bootstrap", "css"]
        if any(keyword in goal_lower for keyword in interface_keywords):
            return "web_app"
        
        # Fallback
        return "web_app"  # Mudança: default para web_app em vez de generic
    
    def _analyze_project_basic(self, goal: str) -> Dict[str, Any]:
        """Análise básica para complexidade e outros detalhes"""
        goal_lower = goal.lower()
        project_type = self._analyze_project_type_basic(goal)
        
        # Determinar complexidade base mais precisa
        complexity_map = {
            "web_app": 5,
            "api_service": 6,  # APIs são mais complexas por natureza
            "cli_tool": 4,     # CLI tools podem ser bem complexos
            "static_website": 3,
            "data_science": 7, # ML projects são naturalmente complexos
            "mobile_app": 8,
            "desktop_app": 6,
            "documentation": 2
        }
        
        complexity = complexity_map.get(project_type, 4)
        
        # Ajustar complexidade baseada em palavras-chave específicas
        # Segurança e autenticação
        if any(keyword in goal_lower for keyword in ["autenticação", "login", "usuário", "auth", "jwt", "oauth"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["encryption", "criptografia", "segurança", "security"]):
            complexity += 1
            
        # Banco de dados e persistência
        if any(keyword in goal_lower for keyword in ["banco", "database", "db", "sqlite", "postgresql", "mysql"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["migration", "migração", "backup", "sincronização"]):
            complexity += 1
            
        # Testing e qualidade
        if any(keyword in goal_lower for keyword in ["testes", "test", "ci", "deploy", "pipeline"]):
            complexity += 1
            
        # DevOps e infraestrutura
        if any(keyword in goal_lower for keyword in ["docker", "kubernetes", "cloud", "aws", "azure"]):
            complexity += 1
        if any(keyword in goal_lower for keyword in ["rate limiting", "monitoramento", "metrics", "observability"]):
            complexity += 1
            
        # Features avançadas específicas por tipo
        if project_type == "api_service":
            if any(keyword in goal_lower for keyword in ["swagger", "openapi", "documentação", "fastapi"]):
                complexity += 1
        elif project_type == "data_science":
            if any(keyword in goal_lower for keyword in ["machine learning", "ml", "churn", "predição", "dashboard"]):
                complexity += 1
        elif project_type == "cli_tool":
            if any(keyword in goal_lower for keyword in ["yaml", "configuração", "múltiplos", "compressão"]):
                complexity += 2  # CLI tools com estas features são bem complexos
            
        complexity = min(complexity, 10)  # Máximo 10
        
        return {
            "project_type": project_type,
            "complexity": complexity,
            "technologies": ["python", "flask"],
            "components": ["main", "config", "requirements"],
            "features": ["basic_functionality"]
        }

    async def _generate_domain_specific_tasks(self, graph: DependencyGraph, project_type: str, goal: str, complexity: int, project_info: dict = None):
        """Gera tarefas específicas do domínio e as adiciona diretamente ao grafo."""
        
        if project_info is None:
            project_info = {}
            
        # A lógica de contagem de tarefas pode ser mantida para guiar a geração
        logger.info(f"Generating domain-specific tasks for project type '{project_type}' with complexity {complexity}")
        
        # Gerar tarefas específicas por tipo e adicioná-las ao grafo
        if project_type == "blog":
            self._get_blog_tasks(graph)
        elif project_type == "api_service":
            await self._get_enhanced_api_tasks(graph, complexity, goal, project_info)
        elif project_type == "ecommerce":
            self._get_enhanced_ecommerce_tasks(graph, complexity)
        elif project_type == "dashboard":
            self._get_enhanced_dashboard_tasks(graph, complexity)
        elif project_type == "web_app":
            await self._get_enhanced_web_app_tasks(graph, complexity, goal, project_info)
        elif project_type == "data_science":
            await self._get_enhanced_data_science_tasks(graph, complexity, goal, project_info)
        else:
            await self._get_enhanced_generic_tasks(graph, complexity, goal, project_info)

    async def _get_enhanced_api_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """Tarefas específicas e detalhadas para APIs REST baseadas nas informações extraídas"""
        
        logger.info(f"🚀 Creating API service tasks with complexity {complexity}")
        
        # Extrair informações específicas
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        infrastructure = project_info.get('infrastructure', [])
        
        # Determinar framework baseado nas tecnologias
        framework = "FastAPI"  # default
        if "Flask" in technologies:
            framework = "Flask"
        elif "Django" in technologies:
            framework = "Django"
        
        # Determinar banco de dados
        database = "PostgreSQL"  # default
        if "MongoDB" in technologies:
            database = "MongoDB"
        elif "MySQL" in technologies:
            database = "MySQL"
        
        # 1. Configuração inicial baseada no framework detectado
        config_task = Task(
            task_id=self._generate_next_id(),
            description=f"Configurar projeto {framework}",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="main.py", 
                content_guideline=f"Configurar aplicação {framework} com {database}, incluindo configurações básicas, middleware CORS e documentação automática"
            ),
            dependencies=[],
            acceptance_criteria=f"Aplicação {framework} configurada e funcional"
        )
        graph.add_task(config_task)
        
        # 2. Modelos baseados nas funcionalidades identificadas
        models_content = f"Modelos de dados para {', '.join(features[:3]) if features else 'sistema de autenticação'}"
        if "JWT" in ' '.join(technologies + features):
            models_content += " com suporte a autenticação JWT"
        
        models_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar modelos de dados",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="models.py", 
                content_guideline=models_content
            ),
            dependencies=[config_task.task_id],
            acceptance_criteria="Modelos de dados implementados com relacionamentos corretos"
        )
        graph.add_task(models_task)

        # 3. Schemas de validação baseadas nas funcionalidades
        schemas_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar schemas de validação",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="schemas.py", 
                content_guideline=f"Schemas Pydantic para {', '.join(features[:3]) if features else 'autenticação e dados básicos'}, com validações customizadas"
            ),
            dependencies=[models_task.task_id],
            acceptance_criteria="Schemas de validação implementados para todas as funcionalidades"
        )
        graph.add_task(schemas_task)

        # 4. Endpoints específicos baseados nas funcionalidades
        endpoints_description = "Implementar endpoints da API"
        if "autenticação" in ' '.join(features).lower() or "jwt" in ' '.join(features).lower():
            endpoints_description = "Implementar endpoints de autenticação e autorização"
        elif "crud" in ' '.join(features).lower():
            endpoints_description = "Implementar endpoints CRUD da API"
        
        api_task = Task(
            task_id=self._generate_next_id(),
            description=endpoints_description,
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="routes.py", 
                content_guideline=f"Endpoints {framework} para {', '.join(features) if features else 'operações básicas'}, com documentação automática e tratamento de erros"
            ),
            dependencies=[schemas_task.task_id],
            acceptance_criteria="Endpoints funcionais com documentação e validação"
        )
        graph.add_task(api_task)
        
        # 5. Funcionalidades específicas baseadas nas tecnologias detectadas
        
        # Redis para cache (se detectado)
        if "Redis" in infrastructure:
            redis_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar cache Redis",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="cache.py", 
                    content_guideline="Configuração e integração Redis para cache de sessões e dados frequentes"
                ),
                dependencies=[api_task.task_id],
                acceptance_criteria="Sistema de cache Redis implementado e funcional"
            )
            graph.add_task(redis_task)
        
        # JWT Authentication (se detectado)
        if any("jwt" in tech.lower() for tech in technologies + features):
            auth_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar autenticação JWT",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="auth.py", 
                    content_guideline="Sistema completo de autenticação JWT com geração, validação e middleware de autorização"
                ),
                dependencies=[api_task.task_id],
                acceptance_criteria="Autenticação JWT implementada com middleware e validação"
            )
            graph.add_task(auth_task)
        
        # Rate Limiting (se mencionado)
        if any("rate limit" in feature.lower() for feature in features):
            rate_limit_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar rate limiting",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="rate_limiter.py", 
                    content_guideline="Sistema de rate limiting por IP e usuário com configuração flexível"
                ),
                dependencies=[api_task.task_id],
                acceptance_criteria="Rate limiting implementado e configurado"
            )
            graph.add_task(rate_limit_task)

    async def _get_enhanced_web_app_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """
        Tarefas específicas e detalhadas para aplicações web, geradas dinamicamente
        com base nas informações extraídas do prompt refinado.
        """
        logger.info(f"🌐 Creating dynamic web app tasks with complexity {complexity} based on extracted info")

        # Extrair informações ricas do projeto
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        infrastructure = project_info.get('infrastructure', [])
        architecture = project_info.get('architecture', 'monolito')

        # Detectar se é um projeto de e-commerce para usar o plano mais especializado
        is_ecommerce = any(keyword in goal.lower() for keyword in [
            'e-commerce', 'ecommerce', 'loja', 'shop', 'carrinho', 'cart', 'pagamento',
            'payment', 'produto', 'product', 'estoque', 'inventory', 'vendas', 'sales', 'venda'
        ])

        if is_ecommerce and complexity >= 8:
            logger.info("🛒 E-commerce project detected. Using specialized e-commerce plan.")
            return self._get_ecommerce_specific_tasks(graph, complexity)

        # Determinar o framework principal
        framework = "Flask" # Default
        if "Django" in technologies: framework = "Django"
        elif "FastAPI" in technologies: framework = "FastAPI"
        
        logger.info(f"Detected web framework: {framework}")

        # 1. Tarefa de Dependências (requirements.txt) - Dinâmica
        reqs_content = f"{framework.lower()}\n"
        if "PostgreSQL" in technologies: reqs_content += "psycopg2-binary\n"
        if "SQLAlchemy" in technologies or framework in ["Flask", "FastAPI"]: reqs_content += "Flask-SQLAlchemy\n"
        if "Redis" in infrastructure: reqs_content += "redis\n"
        if "Celery" in infrastructure: reqs_content += "celery\n"
        reqs_content += "python-dotenv\npytest\ngunicorn\n"

        reqs_task = next((task for task in graph.get_all_tasks() if task.description == "Criar arquivo de dependências (requirements.txt)"), None)
        if reqs_task:
            reqs_task.details.content_guideline = reqs_content
            logger.info("Updated requirements.txt task with dynamic dependencies.")
        
        # 2. Tarefa de Configuração (config.py) - Dinâmica
        config_guideline = f"Configurações para ambiente de desenvolvimento, teste e produção. Carregar variáveis de ambiente (.env). Incluir secret key, URI do banco de dados ({'PostgreSQL' if 'PostgreSQL' in technologies else 'SQLite'})."
        if "Redis" in infrastructure: config_guideline += " Configuração para conexão com Redis."
        if "Celery" in infrastructure: config_guideline += " Configuração do broker Celery."

        config_task = Task(
            task_id=self._generate_next_id(),
            description="Criar sistema de configuração centralizado",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="config.py", content_guideline=config_guideline),
            dependencies=[reqs_task.task_id] if reqs_task else [],
            acceptance_criteria="Arquivo de configuração criado e funcional."
        )
        graph.add_task(config_task)
        last_task_id = config_task.task_id

        # 3. Tarefa da Aplicação Principal (app.py/main.py) - Dinâmica
        app_guideline = f"Criar a aplicação principal {framework}. Inicializar extensões (SQLAlchemy, etc.), registrar blueprints/routers e aplicar configurações."
        app_task = Task(
            task_id=self._generate_next_id(),
            description=f"Criar aplicação principal {framework}",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="app.py", content_guideline=app_guideline),
            dependencies=[last_task_id],
            acceptance_criteria=f"Aplicação {framework} principal funcional."
        )
        graph.add_task(app_task)
        last_task_id = app_task.task_id

        # 4. Tarefa de Modelos (models.py) - Dinâmica
        models_guideline = f"Definir modelos de dados com SQLAlchemy/Django ORM para as funcionalidades: {', '.join(features)}. Incluir relacionamentos, validações e timestamps."
        models_task = Task(
            task_id=self._generate_next_id(),
            description="Criar modelos de dados do projeto",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(file_path="models.py", content_guideline=models_guideline),
            dependencies=[last_task_id],
            acceptance_criteria="Modelos de dados implementados corretamente."
        )
        graph.add_task(models_task)
        last_task_id = models_task.task_id

        # 5. Gerar tarefas para cada funcionalidade principal
        logger.info(f"Generating tasks for {len(features)} identified features.")
        feature_task_ids = []
        for feature in features:
            feature_file = f"{feature.lower().replace(' ', '_').replace('/', '_')}.py"
            feature_task = Task(
                task_id=self._generate_next_id(),
                description=f"Implementar funcionalidade: {feature}",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path=f"features/{feature_file}",
                    content_guideline=f"Implementar a lógica de backend (rotas, views, lógica de negócio) para a funcionalidade '{feature}'."
                ),
                dependencies=[last_task_id],
                acceptance_criteria=f"Funcionalidade '{feature}' implementada e funcional."
            )
            graph.add_task(feature_task)
            feature_task_ids.append(feature_task.task_id)
        
        # A próxima tarefa depende de todas as features estarem prontas
        last_task_id = feature_task_ids if feature_task_ids else [last_task_id]

        # 6. Gerar tarefas para cada componente de infraestrutura
        logger.info(f"Generating tasks for {len(infrastructure)} infrastructure components.")
        infra_task_ids = []
        for infra_component in infrastructure:
            if infra_component.lower() == 'docker':
                docker_task = Task(
                    task_id=self._generate_next_id(),
                    description="Criar Dockerfile para containerização",
                    type=TaskType.CREATE_FILE,
                    details=TaskDetailsCreateFile(
                        file_path="Dockerfile",
                        content_guideline="Criar um Dockerfile multi-stage otimizado para produção."
                    ),
                    dependencies=last_task_id,
                    acceptance_criteria="Dockerfile criado e funcional."
                )
                graph.add_task(docker_task)
                infra_task_ids.append(docker_task.task_id)
        
        if infra_task_ids:
            last_task_id = infra_task_ids

        # 7. Adicionar tarefas de qualidade se a complexidade for alta
        if complexity >= 8:
            test_task = Task(
                task_id=self._generate_next_id(),
                description="Criar suíte de testes automatizados",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="tests/test_features.py",
                    content_guideline=f"Criar testes (pytest) para as funcionalidades: {', '.join(features)}. Cobrir casos de sucesso e de erro."
                ),
                dependencies=last_task_id,
                acceptance_criteria="Testes implementados com boa cobertura."
            )
            graph.add_task(test_task)
    
    def _get_ecommerce_specific_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas específicas para projetos de e-commerce complexos"""
        
        logger.info("🛒 Criando plano específico para E-COMMERCE")
        
        # 1. Setup e dependências específicas para e-commerce
        setup_task = Task(
            task_id=self._generate_next_id(),
            description="Configurar dependências específicas para e-commerce",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="requirements.txt",
                content_guideline="Flask, SQLAlchemy, Flask-Login, Flask-Mail, Stripe, PayPal-SDK, Redis, Celery, Pillow, WTForms, pytest, gunicorn"
            ),
            dependencies=[],
            acceptance_criteria="Dependencies para e-commerce configuradas"
        )
        graph.add_task(setup_task)
        
        # 2. Modelos de dados para e-commerce
        models_task = Task(
            task_id=self._generate_next_id(),
            description="Criar modelos específicos para e-commerce",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="models.py",
                content_guideline="User, Product, Category, Cart, Order, OrderItem, Review, Inventory, Payment com relacionamentos e índices"
            ),
            dependencies=[setup_task.task_id],
            acceptance_criteria="Modelos de e-commerce com relacionamentos implementados"
        )
        graph.add_task(models_task)
        
        # 3. Aplicação Flask principal
        app_task = Task(
            task_id=self._generate_next_id(),
            description="Configurar aplicação Flask para e-commerce",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="app.py",
                content_guideline="Flask app com blueprints, configuração de pagamento, upload de imagens, CSRF, CORS, rate limiting"
            ),
            dependencies=[models_task.task_id],
            acceptance_criteria="Aplicação Flask configurada para e-commerce"
        )
        graph.add_task(app_task)
        
        # 4. Sistema de autenticação JWT
        auth_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar autenticação JWT robusta",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="auth.py",
                content_guideline="JWT com refresh tokens, verificação de email, reset senha, proteção brute force, roles admin/customer"
            ),
            dependencies=[app_task.task_id],
            acceptance_criteria="Sistema JWT com segurança avançada implementado"
        )
        graph.add_task(auth_task)
        
        # 5. Catálogo de produtos
        catalog_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar catálogo de produtos dinâmico",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="catalog.py",
                content_guideline="CRUD produtos, categorias hierárquicas, filtros avançados, busca full-text, paginação, ordenação"
            ),
            dependencies=[auth_task.task_id],
            acceptance_criteria="Catálogo com busca e filtros avançados implementado"
        )
        graph.add_task(catalog_task)
        
        # 6. Sistema de carrinho
        cart_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar carrinho de compras com sessões",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="cart.py",
                content_guideline="Carrinho com sessões Redis, persistência, cálculo de preços, descontos, frete, integração estoque"
            ),
            dependencies=[catalog_task.task_id],
            acceptance_criteria="Sistema de carrinho com persistência implementado"
        )
        graph.add_task(cart_task)
        
        # 7. Sistema de pagamento
        payment_task = Task(
            task_id=self._generate_next_id(),
            description="Integrar sistema de pagamento",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="payments.py",
                content_guideline="Integração Stripe/PayPal, webhooks, processamento assíncrono, logs de transação, reembolsos"
            ),
            dependencies=[cart_task.task_id],
            acceptance_criteria="Sistema de pagamento com múltiplos provedores implementado"
        )
        graph.add_task(payment_task)
        
        # 8. Dashboard administrativo
        admin_task = Task(
            task_id=self._generate_next_id(),
            description="Criar dashboard administrativo completo",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="admin.py",
                content_guideline="Dashboard com gestão produtos, pedidos, usuários, relatórios, gráficos, export CSV/PDF"
            ),
            dependencies=[payment_task.task_id],
            acceptance_criteria="Dashboard administrativo completo implementado"
        )
        graph.add_task(admin_task)
        
        # 9. Sistema de reviews e ratings
        reviews_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar sistema de reviews e ratings",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="reviews.py",
                content_guideline="Reviews com ratings, moderação, spam detection, média de avaliações, fotos nos reviews"
            ),
            dependencies=[admin_task.task_id],
            acceptance_criteria="Sistema de reviews com moderação implementado"
        )
        graph.add_task(reviews_task)
        
        # 10. Gestão de estoque em tempo real
        inventory_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar gestão de estoque em tempo real",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="inventory.py",
                content_guideline="Controle estoque, alertas baixo estoque, reservas temporárias, sync com pedidos, histórico movimentação"
            ),
            dependencies=[reviews_task.task_id],
            acceptance_criteria="Sistema de estoque em tempo real implementado"
        )
        graph.add_task(inventory_task)
        
        # 11. Sistema de notificações
        notifications_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar notificações por email automatizadas",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="notifications.py",
                content_guideline="Emails transacionais, confirmação pedido, shipping, Celery tasks, templates HTML responsivos"
            ),
            dependencies=[inventory_task.task_id],
            acceptance_criteria="Sistema de notificações automatizadas implementado"
        )
        graph.add_task(notifications_task)
        
        # 12. Templates e frontend responsivo
        frontend_task = Task(
            task_id=self._generate_next_id(),
            description="Criar frontend responsivo e SEO-otimizado",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="templates/index.html",
                content_guideline="Templates responsivos, SEO meta tags, schema.org, PWA, lazy loading imagens, performance otimizada"
            ),
            dependencies=[notifications_task.task_id],
            acceptance_criteria="Frontend responsivo com SEO implementado"
        )
        graph.add_task(frontend_task)
        
        # 13. Relatórios de vendas
        reports_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar relatórios de vendas com gráficos",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="reports.py",
                content_guideline="Relatórios vendas, Chart.js, export PDF/Excel, métricas KPI, análise por período, produtos top"
            ),
            dependencies=[frontend_task.task_id],
            acceptance_criteria="Sistema de relatórios com gráficos implementado"
        )
        graph.add_task(reports_task)
        
        # 14. Testes automatizados
        tests_task = Task(
            task_id=self._generate_next_id(),
            description="Criar testes automatizados abrangentes",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="tests/test_ecommerce.py",
                content_guideline="Testes unitários e integração, mock pagamentos, fixtures produtos, coverage > 80%, CI/CD pipeline"
            ),
            dependencies=[reports_task.task_id],
            acceptance_criteria="Suite de testes abrangente implementada"
        )
        graph.add_task(tests_task)
        
        # 15. Deployment automatizado
        deploy_task = Task(
            task_id=self._generate_next_id(),
            description="Configurar deployment automatizado",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="deploy.yml",
                content_guideline="Docker multi-stage, Kubernetes/Docker Swarm, CI/CD GitHub Actions, monitoring, logging, backup DB"
            ),
            dependencies=[tests_task.task_id],
            acceptance_criteria="Pipeline de deployment automatizado configurado"
        )
        graph.add_task(deploy_task)

    def _get_enhanced_generic_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas aprimoradas para projetos genéricos"""
        
        # Tarefas básicas
        main_task = Task(
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
        graph.add_task(main_task)
        last_task_id = main_task.task_id
        
        # Tarefas baseadas na complexidade
        if complexity >= 5:
            config_task = Task(
                task_id=self._generate_next_id(),
                description="Criar sistema de configuração",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="config.py",
                    content_guideline="Sistema de configuração com variáveis de ambiente e validações"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Sistema de configuração implementado"
            )
            graph.add_task(config_task)
            last_task_id = config_task.task_id

            logger_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar sistema de logging",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="logger.py",
                    content_guideline="Sistema de logging estruturado com diferentes níveis e outputs"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Sistema de logging implementado"
            )
            graph.add_task(logger_task)
            last_task_id = logger_task.task_id
            
        if complexity >= 7:
            tests_task = Task(
                task_id=self._generate_next_id(),
                description="Criar testes unitários",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="tests.py",
                    content_guideline="Suite de testes unitários com pytest e cobertura adequada"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Testes unitários implementados"
            )
            graph.add_task(tests_task)

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
    
    async def _get_enhanced_data_science_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """Tarefas específicas para projetos de data science baseadas nas informações extraídas"""
        
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        
        # Determinar biblioteca de ML principal
        ml_framework = "scikit-learn"  # default
        if "TensorFlow" in technologies:
            ml_framework = "TensorFlow"
        elif "PyTorch" in technologies:
            ml_framework = "PyTorch"
        
        # 1. Setup do ambiente de data science
        notebook_task = Task(
            task_id=self._generate_next_id(),
            description="Configurar ambiente Jupyter",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="notebooks/analysis.ipynb",
                content_guideline=f"Notebook Jupyter para análise exploratória usando {ml_framework}, pandas e matplotlib"
            ),
            dependencies=[],
            acceptance_criteria="Ambiente Jupyter configurado e funcional"
        )
        graph.add_task(notebook_task)
        
        # 2. Pipeline de dados
        data_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar pipeline de dados",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="src/data_pipeline.py",
                content_guideline=f"Pipeline de processamento de dados com pandas, validação e transformações para {', '.join(features) if features else 'análise padrão'}"
            ),
            dependencies=[notebook_task.task_id],
            acceptance_criteria="Pipeline de dados implementado e testado"
        )
        graph.add_task(data_task)
        
        # 3. Modelo ML baseado nas features detectadas
        model_description = "machine learning"
        if any("sentiment" in feature.lower() for feature in features):
            model_description = "análise de sentimentos"
        elif any("predict" in feature.lower() for feature in features):
            model_description = "predição"
        
        model_task = Task(
            task_id=self._generate_next_id(),
            description=f"Implementar modelo de {model_description}",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="src/model.py",
                content_guideline=f"Modelo {ml_framework} para {model_description}, com treinamento, validação e serialização"
            ),
            dependencies=[data_task.task_id],
            acceptance_criteria=f"Modelo de {model_description} implementado e treinado"
        )
        graph.add_task(model_task)
    
    async def _get_enhanced_generic_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """Tarefas genéricas baseadas nas informações extraídas do projeto"""
        
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        
        # 1. Aplicação principal baseada nas tecnologias detectadas
        main_file = "main.py"
        framework_guidance = "aplicação Python básica"
        
        if "Flask" in technologies:
            framework_guidance = "aplicação Flask com rotas básicas"
        elif "FastAPI" in technologies:
            framework_guidance = "aplicação FastAPI com endpoints básicos"
        elif "Django" in technologies:
            framework_guidance = "projeto Django com configurações básicas"
            main_file = "manage.py"
        
        app_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar aplicação principal",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path=main_file,
                content_guideline=f"{framework_guidance} implementando {', '.join(features[:3]) if features else 'funcionalidades básicas'}"
            ),
            dependencies=[],
            acceptance_criteria="Aplicação principal implementada e funcional"
        )
        graph.add_task(app_task)
        
        # 2. Configurações baseadas na infraestrutura detectada
        if any(tech in technologies for tech in ["Redis", "PostgreSQL", "MongoDB"]):
            config_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar conexões de banco de dados",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="config.py",
                    content_guideline=f"Configurações para {', '.join([t for t in technologies if t in ['Redis', 'PostgreSQL', 'MongoDB']])}"
                ),
                dependencies=[app_task.task_id],
                acceptance_criteria="Conexões de banco configuradas"
            )
            graph.add_task(config_task)
        
        # 3. Utilitários baseados nas funcionalidades
        if features:
            utils_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar utilitários e helpers",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="utils.py",
                    content_guideline=f"Funções utilitárias para {', '.join(features[:3])}"
                ),
                dependencies=[app_task.task_id],
                acceptance_criteria="Utilitários implementados e testados"
            )
            graph.add_task(utils_task)


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
            # Implementar limite máximo de replans para evitar loops infinitos
            MAX_REPLAN_COUNT = 3
            if failed_task.replan_count >= MAX_REPLAN_COUNT:
                logger.error(f"Task {failed_task.task_id} exceeded maximum replan attempts ({MAX_REPLAN_COUNT}). Stopping replanning.")
                return []
            
            # Detectar loop infinito de revisões
            if failed_task.description.count("Revisão:") >= 2:
                logger.warning(f"Multiple revision loop detected for task {failed_task.task_id}. Stopping replanning.")
                return []
            
            # Detectar loop infinito de correção
            if "Corrigir erro na tarefa:" in failed_task.description:
                logger.warning(f"Correction loop detected for task {failed_task.task_id}. Trying alternative approach.")
                
                # Extrair descrição original removendo prefixos de correção
                original_description = failed_task.description
                while "Corrigir erro na tarefa:" in original_description:
                    original_description = original_description.replace("Corrigir erro na tarefa:", "").strip()
                
                # Se ainda está vazio, falhar graciosamente
                if not original_description:
                    logger.error("Could not extract original task description. Cancelling replanning.")
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
                    max_retries=2,  # Limite menor para evitar loops
                    replan_count=failed_task.replan_count + 1
                )
                
                return [alternative_task]
            
            # Analisar tipo de erro para replanejamento inteligente
            logger.info(f"Replanning task {failed_task.task_id} due to error: {error_feedback[:200]}...")
            
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
                    max_retries=2,
                    replan_count=failed_task.replan_count + 1
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
                    max_retries=2,
                    replan_count=failed_task.replan_count + 1
                )
                
                subtask2 = Task(
                    task_id=self._generate_next_id(),
                    description=f"Parte 2 de: {failed_task.description}",
                    type=failed_task.type,
                    details=failed_task.details,
                    status=TaskStatus.PENDING,
                    dependencies=[subtask1.task_id],
                    acceptance_criteria=f"Segunda parte de: {failed_task.acceptance_criteria}",
                    max_retries=2,
                    replan_count=failed_task.replan_count + 1
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
                    max_retries=1,  # Apenas uma tentativa para evitar loops
                    replan_count=failed_task.replan_count + 1
                )
                
                return [adjusted_task]
            
        except Exception as e:
            logger.error(f"Error replanning task: {e}")
            return []

    async def generate_tasks_from_blueprint(self, blueprint_name: str) -> List[Task]:
        """Baseado em um blueprint, gera um conjunto de tarefas"""
        if not self.context_manager:
            logger.warning("Context manager not available for blueprint")
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
            return False, ValueError("Task not found")

        logger.info(f"Executing task {task_id}: {task.description}")
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
            logger.error(f"Error executing task {task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            return False, e

    async def manage_workflow(self) -> Tuple[bool, str]:
        """Gera e gerencia o fluxo de trabalho através das tarefas"""
        active_context = self.context_manager.get_active_context()
        if not active_context:
            logger.error("No active context found for planning")
            return False, "Context not configured"

        tasks_to_run = self.get_pending_tasks()
        if not tasks_to_run:
            logger.info("No pending tasks available")
            return False, "No tasks to execute"

        # Executa todas as tarefas pendentes
        success_count = 0
        for task in tasks_to_run:
            task_id = task.task_id
            success, error = await self.execute_task(task_id)
            if not success:
                logger.error(f"Failed to execute task {task_id}: {str(error)}")
                # Gera tarefa de fallback
                await self.recover_problematic_task(task, str(error))
            else:
                success_count += 1

        return True, f"{success_count}/{len(tasks_to_run)} tasks completed"

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
        logger.info(f"Recovery task created: {recovery_task.task_id}")
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
            
            logger.warning(f"Failure pattern detected for task {task_id}: {patterns}")
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
            logger.info(f"No specific strategy for {task_id}, using default approach")
            return await self.replan_task(failed_task, "Generic failure")
        
        strategy = self.recovery_strategies[task_id]
        recovery_tasks = []
        
        for action in strategy['actions']:
            recovery_task = self._create_recovery_task_from_action(action, failed_task)
            if recovery_task:
                recovery_tasks.append(recovery_task)
        
        logger.info(f"Applying recovery strategy for {task_id}: {len(recovery_tasks)} tasks created")
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
            logger.warning(f"PlannerAgent: Unsupported handoff type: {request.handoff_type}")
    
    async def _handle_context_transfer(self, request):
        """Processa transferência de contexto de outro agente"""
        context_data = request.data_payload.get('project_context', {})
        
        logger.info(f"PlannerAgent: Receiving context for project {context_data.get('project_id')}")
        
        # Armazenar contexto recebido
        self.received_contexts[request.handoff_id] = {
            'context': context_data,
            'sender': request.sender_agent_id,
            'received_at': datetime.utcnow()
        }
        
        # Se incluir task_queue, mesclar com tarefas existentes
        if 'task_queue' in request.data_payload:
            received_tasks = request.data_payload['task_queue']
            logger.info(f"PlannerAgent: Receiving {len(received_tasks)} tasks from agent {request.sender_agent_id}")
            
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
                        logger.info(f"PlannerAgent: Task {task.task_id} added to local queue")
    
    async def _handle_task_delegation(self, request):
        """Processa delegação de tarefa de outro agente"""
        task_data = request.data_payload.get('task', {})
        execution_context = request.data_payload.get('execution_context', {})
        
        logger.info(f"PlannerAgent: Receiving task delegation for task {task_data.get('task_id')}")
        
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
        
        logger.info(f"PlannerAgent: Task {delegated_task.task_id} accepted for execution")
    
    async def _handle_knowledge_share(self, request):
        """Processa compartilhamento de conhecimento de outro agente"""
        knowledge_data = request.data_payload.get('knowledge', {})
        knowledge_type = request.data_payload.get('knowledge_type', 'general')
        source_agent = request.data_payload.get('source_agent')
        
        logger.info(f"PlannerAgent: Receiving knowledge '{knowledge_type}' from agent {source_agent}")
        
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
        
        logger.info(f"PlannerAgent: Knowledge '{knowledge_type}' integrated successfully")
    
    async def _integrate_planning_patterns(self, patterns_data):
        """Integra padrões de planejamento recebidos"""
        # Exemplo: integrar novos templates de tarefas ou estratégias de planejamento
        if 'task_generation_strategies' in patterns_data:
            strategies = patterns_data['task_generation_strategies']
            logger.info(f"PlannerAgent: Integrating {len(strategies)} task generation strategies")
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
                    logger.info(f"PlannerAgent: New recovery strategy added: {pattern_id}")
    
    async def _integrate_task_templates(self, templates_data):
        """Integra templates de tarefas recebidos"""
        if 'templates' in templates_data:
            templates = templates_data['templates']
            logger.info(f"PlannerAgent: Integrating {len(templates)} task templates")
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
            logger.exception("Error generating initial plan")
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
            logger.info(f"PlannerAgent: Knowledge shared with {successful_shares}/{len(target_agents)} agents")
            
        except Exception as e:
            logger.error(f"Error sharing knowledge: {e}")
    
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

    # ============================================================================
    # MÉTODOS PARA NOVOS TIPOS DE PROJETO
    # ============================================================================
    
    def _get_enhanced_cli_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas específicas e detalhadas para ferramentas CLI"""
        
        logger.info(f"💻 Creating CLI tool tasks with complexity {complexity}")
        
        # 1. Estrutura principal do CLI (SEMPRE)
        cli_main_task = Task(
            task_id=self._generate_next_id(),
            description="Criar estrutura principal da ferramenta CLI",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="cli.py",
                content_guideline="Ferramenta CLI com Click, comandos principais, help context, validação de argumentos"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Estrutura CLI com Click funcional implementada"
        )
        graph.add_task(cli_main_task)
        
        # 2. Módulos de funcionalidades core (SEMPRE)
        core_modules_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar módulos de funcionalidades core",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="core.py",
                content_guideline="Módulos para as funcionalidades principais da ferramenta CLI, classes e funções organizadas"
            ),
            status=TaskStatus.PENDING,
            dependencies=[cli_main_task.task_id],
            acceptance_criteria="Módulos de funcionalidades core implementados"
        )
        graph.add_task(core_modules_task)
        
        last_task_id = core_modules_task.task_id
        
        # 3. Sistema de configuração (para complexidade >= 4)
        if complexity >= 4:
            config_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar sistema de configuração",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="config.py",
                    content_guideline="Sistema de configuração com YAML, validação, defaults, profiles de configuração"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Sistema de configuração YAML funcional"
            )
            graph.add_task(config_task)
            last_task_id = config_task.task_id
            
        # 4. Sistema de logging avançado (para complexidade >= 5)
        if complexity >= 5:
            logging_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar sistema de logging detalhado",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="logger.py",
                    content_guideline="Sistema de logging estruturado com níveis, rotação de arquivos, formatação customizada"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Sistema de logging detalhado implementado"
            )
            graph.add_task(logging_task)
            last_task_id = logging_task.task_id
            
        # 5. Testes CLI (para complexidade >= 6)
        if complexity >= 6:
            test_task = Task(
                task_id=self._generate_next_id(),
                description="Criar testes para CLI",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="test_cli.py",
                    content_guideline="Testes pytest com Click testing, mocking, cobertura de comandos e edge cases"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Suite de testes CLI implementada"
            )
            graph.add_task(test_task)
            
        # 6. Packaging e distribuição (para complexidade >= 7)
        if complexity >= 7:
            package_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar packaging e distribuição",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="setup.py",
                    content_guideline="Setup.py para distribuição via PyPI, entry points, dependencies, metadata"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Packaging para distribuição configurado"
            )
            graph.add_task(package_task)
        
    def _get_enhanced_static_website_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas para sites estáticos"""
        index_task = Task(
            task_id=self._generate_next_id(),
            description="Criar página principal do site",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="index.html",
                content_guideline="Página HTML principal com CSS e JavaScript, design responsivo"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Site estático funcional criado"
        )
        graph.add_task(index_task)
        
    def _get_enhanced_data_science_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas específicas e detalhadas para projetos de ciência de dados"""
        
        logger.info(f"📊 Creating data science tasks with complexity {complexity}")
        
        # 1. Preparação e limpeza de dados (SEMPRE)
        data_prep_task = Task(
            task_id=self._generate_next_id(),
            description="Preparação e limpeza de dados",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="data_preparation.py",
                content_guideline="Scripts para carregamento, limpeza, transformação de dados com pandas, validação de qualidade"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Pipeline de preparação de dados funcional"
        )
        graph.add_task(data_prep_task)
        
        # 2. Análise exploratória (SEMPRE)
        eda_task = Task(
            task_id=self._generate_next_id(),
            description="Análise exploratória de dados (EDA)",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="exploratory_analysis.ipynb",
                content_guideline="Jupyter notebook com EDA completa, estatísticas descritivas, visualizações, insights"
            ),
            status=TaskStatus.PENDING,
            dependencies=[data_prep_task.task_id],
            acceptance_criteria="Análise exploratória completa com insights documentados"
        )
        graph.add_task(eda_task)
        
        # 3. Feature Engineering (SEMPRE para ML)
        feature_eng_task = Task(
            task_id=self._generate_next_id(),
            description="Feature engineering e seleção",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="feature_engineering.py",
                content_guideline="Criação, transformação e seleção de features, encoding categórico, normalização"
            ),
            status=TaskStatus.PENDING,
            dependencies=[eda_task.task_id],
            acceptance_criteria="Pipeline de feature engineering implementado"
        )
        graph.add_task(feature_eng_task)
        
        # 4. Modelagem de ML (SEMPRE para projetos com ML)
        ml_model_task = Task(
            task_id=self._generate_next_id(),
            description="Desenvolvimento de modelo de Machine Learning",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="ml_model.py",
                content_guideline="Treinamento de modelos scikit-learn, validação cruzada, otimização de hiperparâmetros, métricas"
            ),
            status=TaskStatus.PENDING,
            dependencies=[feature_eng_task.task_id],
            acceptance_criteria="Modelo de ML treinado e validado implementado"
        )
        graph.add_task(ml_model_task)
        
        # 5. Dashboard interativo (SEMPRE para projetos com dashboard)
        dashboard_task = Task(
            task_id=self._generate_next_id(),
            description="Criar dashboard interativo",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="dashboard.py",
                content_guideline="Dashboard interativo com Plotly/Dash, gráficos dinâmicos, filtros, KPIs principais"
            ),
            status=TaskStatus.PENDING,
            dependencies=[ml_model_task.task_id],
            acceptance_criteria="Dashboard interativo funcional implementado"
        )
        graph.add_task(dashboard_task)
        
        last_task_id = dashboard_task.task_id
        
        # 6. Relatório executivo (para complexidade >= 7)
        if complexity >= 7:
            report_task = Task(
                task_id=self._generate_next_id(),
                description="Gerar relatório executivo",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="report_generator.py",
                    content_guideline="Geração automática de relatório PDF com insights, visualizações, recomendações executivas"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Sistema de geração de relatório PDF funcional"
            )
            graph.add_task(report_task)
            last_task_id = report_task.task_id
            
        # 7. Pipeline MLOps (para complexidade >= 8)
        if complexity >= 8:
            mlops_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar pipeline MLOps",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="mlops_pipeline.py",
                    content_guideline="Pipeline de MLOps com versionamento de modelos, monitoramento, retreinamento automático"
                ),
                status=TaskStatus.PENDING,
                dependencies=[last_task_id],
                acceptance_criteria="Pipeline MLOps funcional implementado"
            )
            graph.add_task(mlops_task)
        
    def _get_enhanced_mobile_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas para aplicativos móveis"""
        app_task = Task(
            task_id=self._generate_next_id(),
            description="Criar aplicativo móvel básico",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="main.py",
                content_guideline="Aplicativo móvel com framework apropriado (Kivy/BeeWare)"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Aplicativo móvel funcional criado"
        )
        graph.add_task(app_task)
        
    def _get_enhanced_desktop_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas para aplicações desktop"""
        gui_task = Task(
            task_id=self._generate_next_id(),
            description="Criar interface desktop",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="gui.py",
                content_guideline="Interface desktop com Tkinter ou PyQt, funcionalidades principais"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Interface desktop funcional criada"
        )
        graph.add_task(gui_task)
        
    def _get_enhanced_documentation_tasks(self, graph: DependencyGraph, complexity: int):
        """Tarefas para documentação"""
        docs_task = Task(
            task_id=self._generate_next_id(),
            description="Criar documentação técnica",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="docs/README.md",
                content_guideline="Documentação completa com guias de instalação, uso e exemplos"
            ),
            status=TaskStatus.PENDING,
            dependencies=[],
            acceptance_criteria="Documentação técnica completa criada"
        )
        graph.add_task(docs_task)
    
    async def _get_enhanced_data_science_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """Tarefas específicas para projetos de data science baseadas nas informações extraídas"""
        
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        
        # Determinar biblioteca de ML principal
        ml_framework = "scikit-learn"  # default
        if "TensorFlow" in technologies:
            ml_framework = "TensorFlow"
        elif "PyTorch" in technologies:
            ml_framework = "PyTorch"
        
        # 1. Setup do ambiente de data science
        notebook_task = Task(
            task_id=self._generate_next_id(),
            description="Configurar ambiente Jupyter",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="notebooks/analysis.ipynb",
                content_guideline=f"Notebook Jupyter para análise exploratória usando {ml_framework}, pandas e matplotlib"
            ),
            dependencies=[],
            acceptance_criteria="Ambiente Jupyter configurado e funcional"
        )
        graph.add_task(notebook_task)
        
        # 2. Pipeline de dados
        data_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar pipeline de dados",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="src/data_pipeline.py",
                content_guideline=f"Pipeline de processamento de dados com pandas, validação e transformações para {', '.join(features) if features else 'análise padrão'}"
            ),
            dependencies=[notebook_task.task_id],
            acceptance_criteria="Pipeline de dados implementado e testado"
        )
        graph.add_task(data_task)
        
        # 3. Modelo ML baseado nas features detectadas
        model_description = "machine learning"
        if any("sentiment" in feature.lower() for feature in features):
            model_description = "análise de sentimentos"
        elif any("predict" in feature.lower() for feature in features):
            model_description = "predição"
        
        model_task = Task(
            task_id=self._generate_next_id(),
            description=f"Implementar modelo de {model_description}",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="src/model.py",
                content_guideline=f"Modelo {ml_framework} para {model_description}, com treinamento, validação e serialização"
            ),
            dependencies=[data_task.task_id],
            acceptance_criteria=f"Modelo de {model_description} implementado e treinado"
        )
        graph.add_task(model_task)
    
    async def _get_enhanced_generic_tasks(self, graph: DependencyGraph, complexity: int, goal: str, project_info: dict):
        """Tarefas genéricas baseadas nas informações extraídas do projeto"""
        
        technologies = project_info.get('technologies', [])
        features = project_info.get('features', [])
        
        # 1. Aplicação principal baseada nas tecnologias detectadas
        main_file = "main.py"
        framework_guidance = "aplicação Python básica"
        
        if "Flask" in technologies:
            framework_guidance = "aplicação Flask com rotas básicas"
        elif "FastAPI" in technologies:
            framework_guidance = "aplicação FastAPI com endpoints básicos"
        elif "Django" in technologies:
            framework_guidance = "projeto Django com configurações básicas"
            main_file = "manage.py"
        
        app_task = Task(
            task_id=self._generate_next_id(),
            description="Implementar aplicação principal",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path=main_file,
                content_guideline=f"{framework_guidance} implementando {', '.join(features[:3]) if features else 'funcionalidades básicas'}"
            ),
            dependencies=[],
            acceptance_criteria="Aplicação principal implementada e funcional"
        )
        graph.add_task(app_task)
        
        # 2. Configurações baseadas na infraestrutura detectada
        if any(tech in technologies for tech in ["Redis", "PostgreSQL", "MongoDB"]):
            config_task = Task(
                task_id=self._generate_next_id(),
                description="Configurar conexões de banco de dados",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="config.py",
                    content_guideline=f"Configurações para {', '.join([t for t in technologies if t in ['Redis', 'PostgreSQL', 'MongoDB']])}"
                ),
                dependencies=[app_task.task_id],
                acceptance_criteria="Conexões de banco configuradas"
            )
            graph.add_task(config_task)
        
        # 3. Utilitários baseados nas funcionalidades
        if features:
            utils_task = Task(
                task_id=self._generate_next_id(),
                description="Implementar utilitários e helpers",
                type=TaskType.CREATE_FILE,
                details=TaskDetailsCreateFile(
                    file_path="utils.py",
                    content_guideline=f"Funções utilitárias para {', '.join(features[:3])}"
                ),
                dependencies=[app_task.task_id],
                acceptance_criteria="Utilitários implementados e testados"
            )
            graph.add_task(utils_task)
