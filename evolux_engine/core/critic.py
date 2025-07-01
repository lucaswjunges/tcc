import asyncio
import json
from typing import Optional, List, Dict, Any
from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task, ArtifactState

class CriticReport(Dict):
    """
    Relatório gerado pelo CriticAgent, contendo uma análise crítica
    de um plano ou artefato.
    """
    score: float  # 0.0 (crítico) a 1.0 (excelente)
    potential_issues: List[str]
    suggestions_for_improvement: List[str]
    is_approved: bool

class CriticAgent:
    """
    O CriticAgent atua como um "advogado do diabo", analisando proativamente
    planos e artefatos em busca de falhas, ineficiências e riscos antes
    que eles causem problemas.
    """

    def __init__(
        self,
        critic_llm_client: LLMClient,
        project_context: ProjectContext,
        agent_id: str = "critic_agent"
    ):
        self.critic_llm = critic_llm_client
        self.project_context = project_context
        self.agent_id = agent_id
        logger.info(f"CriticAgent (ID: {self.agent_id}) inicializado.")

    async def review_plan(self, tasks: List[Task]) -> CriticReport:
        """
        Analisa um plano de tarefas em busca de falhas lógicas,
        dependências ausentes ou ineficiências.
        """
        logger.info(f"CriticAgent: Revisando plano com {len(tasks)} tarefas.")
        
        plan_representation = self._format_plan_for_review(tasks)
        
        prompt = f"""
        Você é um Engenheiro de Software Sênior e Arquiteto de Sistemas. Sua tarefa é analisar construtivamente o seguinte plano de projeto, BALANCEANDO rigor técnico com praticidade.

        PLANO DO PROJETO:
        {plan_representation}

        OBJETIVO GERAL DO PROJETO:
        {self.project_context.project_goal}

        CRITÉRIOS DE AVALIAÇÃO BALANCEADOS:
        1. **Viabilidade Técnica:** O plano é tecnicamente viável e realista?
        2. **Alinhamento com Objetivo:** As tarefas atingem o objetivo principal?
        3. **Estrutura Básica:** Existem dependências críticas ausentes?
        4. **Praticidade:** O plano é executável sem complexidade desnecessária?

        DIRETRIZES DE PONTUAÇÃO BALANCEADAS:
        - 0.8-1.0: Plano sólido com pequenos ajustes opcionais
        - 0.6-0.8: Plano viável com melhorias recomendadas
        - 0.4-0.6: Plano aceitável mas com questões que podem impactar execução
        - 0.2-0.4: Plano com problemas significativos que precisam ser corrigidos
        - 0.0-0.2: Plano fundamentalmente falho

        CONSIDERE QUE:
        - Planos MVP podem ter escopo reduzido intencionalmente
        - Tarefas de qualidade (testes, CI/CD) podem ser iterativas
        - Configuração de produção pode ser incremental
        - Dependências podem ser menos rígidas em projetos pequenos

        Retorne sua análise em um formato JSON com a seguinte estrutura:
        {{
            "score": <float de 0.0 a 1.0>,
            "potential_issues": ["lista de problemas reais encontrados"],
            "suggestions_for_improvement": ["lista de sugestões construtivas"],
            "is_approved": <boolean, true se score >= 0.6, false caso contrário>
        }}
        """
        
        messages = [{"role": "system", "content": "Você é um revisor de planos de engenharia de software altamente crítico e experiente."}, {"role": "user", "content": prompt}]
        
        response_text = await self.critic_llm.generate_response(messages, max_tokens=1024, temperature=0.3)
        
        return self._parse_llm_response(response_text)

    async def review_code_artifact(self, artifact: ArtifactState, file_content: str) -> CriticReport:
        """
        Analisa um artefato de código em busca de bugs, más práticas ou ineficiências.
        """
        logger.info(f"CriticAgent: Revisando o artefato de código: {artifact.path}")

        prompt = f"""
        Você é um Programador Principal (Principal Engineer) e especialista em qualidade de código. Sua tarefa é fazer uma revisão crítica do seguinte arquivo de código.

        ARQUIVO: {artifact.path}
        
        OBJETIVO DO PROJETO:
        {self.project_context.project_goal}

        CONTEÚDO DO ARQUIVO:
        ```python
        {file_content}
        ```

        Analise os seguintes aspectos:
        1.  **Bugs e Erros Lógicos:** Existe algum bug óbvio ou sutil no código?
        2.  **Qualidade e Boas Práticas:** O código segue os princípios SOLID, DRY, etc.? Está bem estruturado?
        3.  **Performance:** Existe alguma ineficiência óbvia que poderia causar lentidão?
        4.  **Legibilidade e Manutenibilidade:** O código é fácil de entender e manter?

        Retorne sua análise em um formato JSON com a seguinte estrutura:
        {{
            "score": <float de 0.0 a 1.0, onde 1.0 é um código perfeito>,
            "potential_issues": ["lista de problemas potenciais encontrados"],
            "suggestions_for_improvement": ["lista de sugestões para melhorar o código"],
            "is_approved": <boolean, true se o código for aceitável, false se precisar de refatoração>
        }}
        """
        
        messages = [{"role": "system", "content": "Você é um revisor de código sênior, focado em encontrar problemas e sugerir melhorias."}, {"role": "user", "content": prompt}]
        
        response_text = await self.critic_llm.generate_response(messages, max_tokens=1500, temperature=0.2)
        
        return self._parse_llm_response(response_text)

    def _format_plan_for_review(self, tasks: List[Task]) -> str:
        """Formata a lista de tarefas em uma representação textual para a LLM."""
        lines = []
        for i, task in enumerate(tasks):
            lines.append(f"Tarefa {i+1}: {task.description} (ID: {task.task_id[:8]})")
            if task.dependencies:
                dep_ids = [dep[:8] for dep in task.dependencies]
                lines.append(f"  - Depende de: {', '.join(dep_ids)}")
        return "\n".join(lines)

    def _parse_llm_response(self, response_text: Optional[str]) -> CriticReport:
        """Faz o parse da resposta JSON da LLM para um CriticReport."""
        if not response_text:
            logger.warning("CriticAgent: LLM não retornou resposta.")
            return {"score": 0.5, "potential_issues": ["Falha na análise crítica"], "suggestions_for_improvement": [], "is_approved": True}

        try:
            from evolux_engine.utils.string_utils import extract_json_from_llm_response
            json_str = extract_json_from_llm_response(response_text)
            if not json_str:
                raise ValueError("Nenhum JSON encontrado na resposta.")
            
            data = json.loads(json_str)
            
            # Validação do schema do relatório
            report = CriticReport(
                score=float(data.get("score", 0.5)),
                potential_issues=data.get("potential_issues", []),
                suggestions_for_improvement=data.get("suggestions_for_improvement", []),
                is_approved=bool(data.get("is_approved", True))
            )
            return report
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"CriticAgent: Falha ao fazer o parse da resposta da LLM: {e}\nResposta: {response_text}")
            return {"score": 0.5, "potential_issues": [f"Erro de parsing na crítica: {e}"], "suggestions_for_improvement": [], "is_approved": True}
