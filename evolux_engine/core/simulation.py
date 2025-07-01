import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.models.project_context import ProjectContext
from evolux_engine.schemas.contracts import Task

class SimulationReport(Dict):
    """
    Relatório gerado pelo SimulationEngine, prevendo os resultados de uma ação.
    """
    predicted_outcome: str
    confidence_score: float
    potential_side_effects: List[str]
    affected_artifacts: List[str]
    is_safe_to_proceed: bool

class SimulationEngine:
    """
    O SimulationEngine usa LLMs para prever o resultado de ações
    (como comandos de shell ou modificações de arquivos) antes que
    elas sejam executadas, permitindo uma execução mais segura e inteligente.
    """

    def __init__(
        self,
        simulation_llm_client: LLMClient,
        project_context: ProjectContext,
        agent_id: str = "simulation_engine"
    ):
        self.simulation_llm = simulation_llm_client
        self.project_context = project_context
        self.agent_id = agent_id
        logger.info(f"SimulationEngine (ID: {self.agent_id}) inicializado.")

    async def simulate_command_execution(self, command: str, task_context: str) -> SimulationReport:
        """
        Simula a execução de um comando de shell e prevê seu impacto.
        """
        logger.info(f"SimulationEngine: Simulando execução do comando: '{command}'")

        artifacts_summary = self.project_context.get_artifacts_structure_summary()

        prompt = f"""
        Você é um especialista em sistemas e DevOps. Sua tarefa é prever o resultado da execução de um comando de shell no contexto de um projeto de software.

        COMANDO A SER EXECUTADO:
        `{command}`

        CONTEXTO DA TAREFA:
        {task_context}

        ESTRUTURA DE ARQUIVOS ATUAL DO PROJETO:
        {artifacts_summary}

        Com base nessas informações, preveja:
        1.  **Resultado Provável:** O que este comando provavelmente fará? (ex: "Instalará a biblioteca 'requests', "Listará os arquivos no diretório 'src'").
        2.  **Efeitos Colaterais:** Quais são os possíveis efeitos colaterais inesperados? (ex: "Pode sobrescrever a versão de uma dependência", "Pode deletar arquivos se o caminho estiver errado").
        3.  **Artefatos Afetados:** Quais arquivos ou diretórios serão criados, modificados ou deletados?
        4.  **Segurança:** O comando parece seguro para prosseguir?

        Retorne sua análise em um formato JSON com a seguinte estrutura:
        {{
            "predicted_outcome": "Descrição do resultado esperado.",
            "confidence_score": <float de 0.0 a 1.0>,
            "potential_side_effects": ["lista de possíveis efeitos colaterais"],
            "affected_artifacts": ["lista de caminhos de arquivos/diretórios afetados"],
            "is_safe_to_proceed": <boolean>
        }}
        """
        
        messages = [{"role": "system", "content": "Você é um simulador de execução de comandos de terminal."}, {"role": "user", "content": prompt}]
        
        response_text = await self.simulation_llm.generate_response(messages, max_tokens=1024, temperature=0.1)
        
        return self._parse_llm_response(response_text)

    def _parse_llm_response(self, response_text: Optional[str]) -> SimulationReport:
        """Faz o parse da resposta JSON da LLM para um SimulationReport."""
        if not response_text:
            logger.warning("SimulationEngine: LLM não retornou resposta.")
            return {"predicted_outcome": "Falha na simulação", "confidence_score": 0.0, "potential_side_effects": [], "affected_artifacts": [], "is_safe_to_proceed": False}

        try:
            from evolux_engine.utils.string_utils import extract_json_from_llm_response
            import json
            json_str = extract_json_from_llm_response(response_text)
            if not json_str:
                raise ValueError("Nenhum JSON encontrado na resposta.")
            
            data = json.loads(json_str)
            
            report = SimulationReport(
                predicted_outcome=data.get("predicted_outcome", "N/A"),
                confidence_score=float(data.get("confidence_score", 0.5)),
                potential_side_effects=data.get("potential_side_effects", []),
                affected_artifacts=data.get("affected_artifacts", []),
                is_safe_to_proceed=bool(data.get("is_safe_to_proceed", False))
            )
            return report
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"SimulationEngine: Falha ao fazer o parse da resposta da LLM: {e}\nResposta: {response_text}")
            return {"predicted_outcome": f"Erro de parsing na simulação: {e}", "confidence_score": 0.0, "potential_side_effects": [], "affected_artifacts": [], "is_safe_to_proceed": False}
