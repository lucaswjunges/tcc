#!/usr/bin/env python3
"""
Exemplo de Execução Melhorada do Evolux Engine

Este exemplo demonstra como usar as novas funcionalidades de refinamento iterativo,
validação rigorosa e métricas de qualidade para obter resultados muito superiores.

Funcionalidades demonstradas:
- Refinamento iterativo com múltiplas estratégias
- Validação semântica profunda
- Métricas de qualidade em tempo real
- Sistema de feedback e melhoria contínua
- Prompts avançados com auto-crítica
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolux_engine.core.orchestrator import Orchestrator
from evolux_engine.core.executor import TaskExecutorAgent
from evolux_engine.core.validator import SemanticValidatorAgent
from evolux_engine.core.iterative_refiner import IterativeRefiner, RefinementStrategy
from evolux_engine.services.quality_metrics import QualityMetricsCollector
from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.services.file_service import FileService
from evolux_engine.services.shell_service import ShellService
from evolux_engine.prompts.prompt_engine import PromptEngine
from evolux_engine.schemas.contracts import (
    Task, TaskType, TaskDetailsCreateFile, ProjectStatus, TaskStatus
)

from loguru import logger


class ImprovedEvolutionDemo:
    """
    Demonstração das melhorias do Evolux Engine com foco em qualidade.
    """
    
    def __init__(self):
        self.project_context = None
        self.quality_collector = QualityMetricsCollector()
        
        # Configurar logging detalhado
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        
        logger.info("🚀 Iniciando demonstração do Evolux Engine melhorado")
    
    async def setup_project(self, project_goal: str, project_type: str = "web_application"):
        """Configura um novo projeto com as melhorias"""
        
        logger.info(f"📋 Configurando projeto: {project_goal}")
        
        # Criar contexto do projeto
        self.project_context = ProjectContext(
            project_id=f"demo_{int(asyncio.get_event_loop().time())}",
            project_goal=project_goal,
            project_type=project_type,
            status=ProjectStatus.INITIALIZING
        )
        
        # Configurar workspace
        workspace_path = Path.cwd() / "demo_workspace" / self.project_context.project_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        self.project_context.workspace_path = str(workspace_path)
        
        logger.info(f"📁 Workspace criado em: {workspace_path}")
        return self.project_context
    
    async def demonstrate_iterative_refinement(self):
        """Demonstra o refinamento iterativo em ação"""
        
        logger.info("🔄 Demonstrando refinamento iterativo")
        
        # Configurar clientes LLM (simulados para demo)
        primary_llm = await self._create_mock_llm("primary")
        reviewer_llm = await self._create_mock_llm("reviewer") 
        validator_llm = await self._create_mock_llm("validator")
        
        # Configurar serviços
        file_service = FileService()
        shell_service = ShellService()
        prompt_engine = PromptEngine()
        
        # Criar TaskExecutor com refinamento habilitado
        executor = TaskExecutorAgent(
            executor_llm_client=primary_llm,
            project_context=self.project_context,
            file_service=file_service,
            shell_service=shell_service,
            agent_id="demo_executor",
            enable_iterative_refinement=True,
            reviewer_llm_client=reviewer_llm,
            validator_llm_client=validator_llm
        )
        
        # Criar uma tarefa complexa para teste
        complex_task = Task(
            task_id="demo_task_001",
            description="Create a secure authentication system with JWT tokens, password hashing, and session management",
            type=TaskType.CREATE_FILE,
            details=TaskDetailsCreateFile(
                file_path="auth_system.py",
                content_guideline="Implement a production-ready authentication system with comprehensive security measures"
            ),
            acceptance_criteria="Must include password hashing, JWT tokens, session management, input validation, and error handling",
            status=TaskStatus.PENDING
        )
        
        logger.info("🎯 Executando tarefa complexa com refinamento iterativo")
        
        # Executar tarefa com refinamento
        start_time = asyncio.get_event_loop().time()
        execution_result = await executor.execute_task(complex_task, use_refinement=True)
        completion_time = asyncio.get_event_loop().time() - start_time
        
        # Simular validação para demo
        validation_result = await self._simulate_validation(complex_task, execution_result)
        
        # Registrar métricas
        self.quality_collector.record_task_completion(
            task=complex_task,
            execution_result=execution_result,
            validation_result=validation_result,
            completion_time=completion_time,
            llm_calls=5  # Múltiplas iterações
        )\n        \n        logger.info(f\"✅ Tarefa concluída em {completion_time:.2f}s\")\n        logger.info(f\"📊 Pontuação de qualidade: {validation_result.quality_rating or 'N/A'}\")\n        \n        return execution_result, validation_result\n    \n    async def demonstrate_quality_metrics(self):\n        \"\"\"Demonstra o sistema de métricas de qualidade\"\"\"\n        \n        logger.info(\"📈 Analisando métricas de qualidade\")\n        \n        # Simular algumas tarefas adicionais para ter dados\n        await self._simulate_multiple_tasks()\n        \n        # Obter métricas atuais\n        current_metrics = self.quality_collector.get_current_quality_metrics()\n        \n        logger.info(\"📊 Métricas de Qualidade Atuais:\")\n        for metric_name, metric_data in current_metrics.items():\n            if isinstance(metric_data, dict):\n                logger.info(f\"  {metric_name}: {metric_data['current']:.2f} (tendência: {metric_data['trend']})\")\n        \n        # Gerar relatório do projeto\n        project_report = self.quality_collector.generate_project_quality_report(\n            self.project_context.project_id\n        )\n        \n        logger.info(f\"📋 Relatório do Projeto:\")\n        logger.info(f\"  Total de tarefas: {project_report.total_tasks}\")\n        logger.info(f\"  Taxa de sucesso: {project_report.successful_tasks / max(project_report.total_tasks, 1) * 100:.1f}%\")\n        logger.info(f\"  Qualidade média: {project_report.average_quality_score:.2f}\")\n        logger.info(f\"  Taxa de convergência: {project_report.convergence_rate:.2f}\")\n        \n        if project_report.recommendations:\n            logger.info(\"💡 Recomendações:\")\n            for i, rec in enumerate(project_report.recommendations[:3], 1):\n                logger.info(f\"  {i}. {rec[:100]}...\")\n        \n        # Exportar métricas para arquivo\n        metrics_file = Path(self.project_context.workspace_path) / \"quality_metrics.json\"\n        self.quality_collector.export_metrics_to_json(str(metrics_file))\n        logger.info(f\"📁 Métricas exportadas para: {metrics_file}\")\n        \n        return project_report\n    \n    async def demonstrate_advanced_prompts(self):\n        \"\"\"Demonstra o sistema de prompts avançados\"\"\"\n        \n        logger.info(\"🧠 Demonstrando prompts avançados\")\n        \n        prompt_engine = PromptEngine()\n        \n        # Criar contexto rico para prompts\n        from evolux_engine.prompts.prompt_engine import PromptContext\n        \n        context = PromptContext(\n            project_goal=self.project_context.project_goal,\n            project_type=self.project_context.project_type,\n            task_description=\"Create a comprehensive API documentation system\",\n            current_artifacts=\"auth_system.py, database_models.py, config.py\",\n            error_history=[\"Missing type hints in previous attempt\", \"Insufficient error handling\"],\n            iteration_count=3\n        )\n        \n        # Gerar prompt iterativo\n        prompt = prompt_engine.build_iterative_prompt(\n            template_name=\"code_generation\",\n            context=context,\n            previous_attempts=[\n                '{\"quality_score\": 6.5, \"issues\": [\"Missing documentation\", \"No tests\"]}',\n                '{\"quality_score\": 7.8, \"issues\": [\"Could improve error handling\"]}'\n            ]\n        )\n        \n        logger.info(\"📝 Exemplo de prompt avançado gerado:\")\n        logger.info(f\"Tamanho do prompt: {len(prompt) if prompt else 0} caracteres\")\n        \n        if prompt:\n            # Mostrar primeiras linhas do prompt\n            lines = prompt.split('\\n')[:10]\n            for line in lines:\n                logger.info(f\"  {line[:80]}{'...' if len(line) > 80 else ''}\")\n        \n        return prompt\n    \n    async def _create_mock_llm(self, role: str) -> LLMClient:\n        \"\"\"Cria um cliente LLM simulado para demonstração\"\"\"\n        \n        class MockLLMClient(LLMClient):\n            def __init__(self, role):\n                self.role = role\n                self.model_name = f\"mock-{role}-model\"\n            \n            async def generate_response(self, messages, max_tokens=1000, temperature=0.7):\n                # Simular resposta baseada no papel\n                if self.role == \"primary\":\n                    return '''\n{\n    \"file_content\": \"import hashlib\\nimport jwt\\nfrom datetime import datetime, timedelta\\nfrom typing import Optional\\n\\nclass AuthSystem:\\n    def __init__(self):\\n        self.secret_key = 'your-secret-key'\\n    \\n    def hash_password(self, password: str) -> str:\\n        return hashlib.sha256(password.encode()).hexdigest()\\n    \\n    def create_jwt_token(self, user_id: str) -> str:\\n        payload = {\\n            'user_id': user_id,\\n            'exp': datetime.utcnow() + timedelta(hours=24)\\n        }\\n        return jwt.encode(payload, self.secret_key, algorithm='HS256')\\n    \\n    def verify_token(self, token: str) -> Optional[str]:\\n        try:\\n            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])\\n            return payload['user_id']\\n        except jwt.ExpiredSignatureError:\\n            return None\",\n    \"quality_review\": {\n        \"code_quality_score\": 8,\n        \"potential_issues\": [\"Secret key should be environment variable\"],\n        \"improvement_suggestions\": [\"Add input validation\", \"Add rate limiting\"],\n        \"security_considerations\": [\"Password hashing implemented\", \"JWT tokens with expiration\"]\n    }\n}\n'''\n                elif self.role == \"reviewer\":\n                    return \"Code quality is good. Consider adding input validation and using environment variables for secrets. The authentication logic is sound but could benefit from more comprehensive error handling.\"\n                \n                elif self.role == \"validator\":\n                    return '''\n{\n    \"validation_passed\": true,\n    \"confidence_score\": 0.85,\n    \"quality_rating\": 8.2,\n    \"checklist\": {\n        \"correctness\": true,\n        \"completeness\": true,\n        \"efficiency\": true,\n        \"maintainability\": true,\n        \"security\": true\n    },\n    \"identified_issues\": [\"Secret key hardcoded\", \"Missing input validation\"],\n    \"suggested_improvements\": [\"Use environment variables\", \"Add comprehensive input validation\", \"Implement rate limiting\"],\n    \"critical_problems\": []\n}\n'''\n                \n                return \"Mock response from \" + self.role\n        \n        return MockLLMClient(role)\n    \n    async def _simulate_validation(self, task: Task, execution_result) -> 'ValidationResult':\n        \"\"\"Simula validação para demonstração\"\"\"\n        from evolux_engine.schemas.contracts import ValidationResult, SemanticValidationChecklistItem\n        \n        return ValidationResult(\n            validation_passed=True,\n            confidence_score=0.85,\n            checklist=[\n                SemanticValidationChecklistItem(\n                    item=\"Funcionalidade implementada\",\n                    passed=True,\n                    reasoning=\"Sistema de autenticação completo\"\n                ),\n                SemanticValidationChecklistItem(\n                    item=\"Segurança adequada\",\n                    passed=True,\n                    reasoning=\"Hash de senha e JWT implementados\"\n                )\n            ],\n            identified_issues=[\"Chave secreta hardcoded\", \"Falta validação de entrada\"],\n            suggested_improvements=[\"Usar variáveis de ambiente\", \"Adicionar validação robusta\"],\n            quality_rating=8.2,\n            requires_iteration=False\n        )\n    \n    async def _simulate_multiple_tasks(self):\n        \"\"\"Simula múltiplas tarefas para gerar dados de métricas\"\"\"\n        \n        # Simular tarefas com diferentes níveis de qualidade\n        task_scenarios = [\n            (\"Create database models\", 9.1, True, 2),\n            (\"Implement API endpoints\", 7.8, True, 3),\n            (\"Add error handling\", 6.5, False, 4),\n            (\"Write unit tests\", 8.9, True, 1),\n            (\"Setup CI/CD pipeline\", 7.2, True, 3)\n        ]\n        \n        for i, (desc, quality, success, iterations) in enumerate(task_scenarios):\n            from evolux_engine.schemas.contracts import ExecutionResult, ValidationResult\n            \n            # Simular tarefa\n            task = Task(\n                task_id=f\"sim_task_{i:03d}\",\n                description=desc,\n                type=TaskType.CREATE_FILE,\n                status=TaskStatus.COMPLETED\n            )\n            \n            # Simular resultado de execução\n            exec_result = ExecutionResult(\n                exit_code=0 if success else 1,\n                stdout=f\"Task {desc} completed\",\n                stderr=\"\" if success else \"Some error occurred\"\n            )\n            \n            # Simular validação\n            validation = ValidationResult(\n                validation_passed=success,\n                confidence_score=quality / 10.0,\n                quality_rating=quality,\n                identified_issues=[] if success else [\"Implementation incomplete\"],\n                suggested_improvements=[\"Add documentation\"] if quality < 8.0 else []\n            )\n            \n            # Simular refinamento\n            refinement = None\n            if iterations > 1:\n                from evolux_engine.core.iterative_refiner import RefinementResult, RefinementIteration\n                \n                # Simular trajetória de melhoria\n                trajectory = [max(1.0, quality - (iterations - i) * 0.5) for i in range(iterations)]\n                trajectory[-1] = quality  # Resultado final\n                \n                refinement = RefinementResult(\n                    final_result=exec_result,\n                    iterations=[],\n                    total_iterations=iterations,\n                    final_quality_score=quality,\n                    convergence_achieved=quality > 8.0,\n                    improvement_trajectory=trajectory\n                )\n            \n            # Registrar métricas\n            self.quality_collector.record_task_completion(\n                task=task,\n                execution_result=exec_result,\n                validation_result=validation,\n                refinement_result=refinement,\n                completion_time=float(iterations * 30),  # Simular tempo\n                llm_calls=iterations * 2\n            )\n    \n    async def run_complete_demo(self):\n        \"\"\"Executa demonstração completa das melhorias\"\"\"\n        \n        logger.info(\"🎬 Iniciando demonstração completa do Evolux Engine melhorado\")\n        \n        try:\n            # 1. Configurar projeto\n            await self.setup_project(\n                \"Create a comprehensive web application with authentication, API, and dashboard\",\n                \"full_stack_web_app\"\n            )\n            \n            # 2. Demonstrar refinamento iterativo\n            execution_result, validation_result = await self.demonstrate_iterative_refinement()\n            \n            # 3. Demonstrar prompts avançados\n            advanced_prompt = await self.demonstrate_advanced_prompts()\n            \n            # 4. Analisar métricas de qualidade\n            quality_report = await self.demonstrate_quality_metrics()\n            \n            # 5. Resumo final\n            logger.info(\"\\n🎉 Demonstração concluída com sucesso!\")\n            logger.info(\"\\n📊 Resumo das Melhorias:\")\n            logger.info(\"  ✅ Refinamento iterativo implementado\")\n            logger.info(\"  ✅ Validação semântica rigorosa\")\n            logger.info(\"  ✅ Prompts avançados com auto-crítica\")\n            logger.info(\"  ✅ Sistema de métricas de qualidade\")\n            logger.info(\"  ✅ Feedback contínuo e melhoria\")\n            \n            logger.info(f\"\\n📈 Resultados de Qualidade:\")\n            logger.info(f\"  Pontuação média: {quality_report.average_quality_score:.2f}/10\")\n            logger.info(f\"  Taxa de sucesso: {quality_report.successful_tasks/max(quality_report.total_tasks,1)*100:.1f}%\")\n            logger.info(f\"  Convergência: {quality_report.convergence_rate:.1f}%\")\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"❌ Erro na demonstração: {e}\")\n            import traceback\n            traceback.print_exc()\n            return False\n\n\nasync def main():\n    \"\"\"Função principal da demonstração\"\"\"\n    \n    demo = ImprovedEvolutionDemo()\n    success = await demo.run_complete_demo()\n    \n    if success:\n        print(\"\\n\" + \"=\"*80)\n        print(\"🎯 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!\")\n        print(\"\\nO Evolux Engine agora possui:\")\n        print(\"  🔄 Refinamento iterativo inteligente\")\n        print(\"  🔍 Validação semântica rigorosa\")\n        print(\"  🧠 Prompts avançados com auto-crítica\")\n        print(\"  📊 Métricas de qualidade em tempo real\")\n        print(\"  💡 Sistema de feedback e melhoria contínua\")\n        print(\"\\nEstas melhorias resultam em:\")\n        print(\"  📈 Qualidade de código muito superior\")\n        print(\"  🎯 Maior precisão na execução de tarefas\")\n        print(\"  🔄 Capacidade de auto-correção\")\n        print(\"  📊 Visibilidade completa do progresso\")\n        print(\"  🚀 Resultados mais robustos e confiáveis\")\n        print(\"=\"*80)\n    else:\n        print(\"\\n❌ Demonstração falhou - veja os logs para detalhes\")\n\n\nif __name__ == \"__main__\":\n    asyncio.run(main())