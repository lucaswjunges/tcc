import asyncio
import re
import os
from typing import Optional, List

from loguru import logger # Importar logger do Loguru
from evolux_engine.settings import settings
from evolux_engine.core.context_manager import ContextManager
from evolux_engine.llms.llm_client import LLMClient


class Agent:
    def __init__(self, project_id: str, goal: str):
        self.project_id = project_id
        self.goal = goal
        self.project_structure_str: str = ""

        # Bind project_id e agent_goal ao logger para esta instância, se desejar contexto automático
        # self.log = logger.bind(agent_project_id=project_id, agent_goal=goal)
        # Se fizer isso, use self.log.info(...) em vez de logger.info(...) dentro desta classe.
        # Por simplicidade, vamos usar o logger global e passar o contexto como kwargs.

        openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', os.getenv('OPENROUTER_API_KEY'))
        
        if not openrouter_api_key:
            logger.error("OPENROUTER_API_KEY não encontrada nas configurações nem nas variáveis de ambiente.", agent_id=self.project_id)
            raise ValueError("OPENROUTER_API_KEY é necessária.")

        self.planner_llm = LLMClient(
            api_key=openrouter_api_key,
            model_name=getattr(settings, 'MODEL_PLANNER', "deepseek/deepseek-r1-0528-qwen3-8b:free"),
            provider="openrouter",
            http_referer=getattr(settings, 'HTTP_REFERER', "http://localhost:3000"), # Exemplo com porta
            x_title=getattr(settings, 'APP_TITLE', "Evolux Engine TCC")
        )
        self.executor_llm = LLMClient(
            api_key=openrouter_api_key,
            model_name=getattr(settings, 'MODEL_EXECUTOR', "deepseek/deepseek-r1-0528-qwen3-8b:free"),
            provider="openrouter",
            http_referer=getattr(settings, 'HTTP_REFERER', "http://localhost:3000"),
            x_title=getattr(settings, 'APP_TITLE', "Evolux Engine TCC")
        )
        
        project_base_dir = getattr(settings, 'PROJECT_BASE_DIR', './project_workspaces')
        self.context_manager = ContextManager(project_id=project_id, base_project_dir=project_base_dir)

        logger.info(
            "Agente inicializado.",
            agent_id=self.project_id,
            goal=self.goal,
            planner_model=self.planner_llm.model_name,
            executor_model=self.executor_llm.model_name,
            project_path=str(self.context_manager.project_path) # Garante que é string p/ log
        )

    def _extract_code_block(self, response_text: str, language: Optional[str] = None) -> Optional[str]:
        if not response_text:
            return None
        if language:
            pattern = re.compile(rf"```{language}\s*([\s\S]*?)\s*```", re.MULTILINE)
        else:
            pattern = re.compile(r"```(?:\w+\s*)?([\s\S]*?)\s*```", re.MULTILINE)
        match = pattern.search(response_text)
        if match:
            return match.group(1).strip()
        if language == "html" and response_text.lower().lstrip().startswith("<!doctype html"):
            return response_text.strip()
        if not language: return None
        if language not in ["markdown", "md", "txt", "text"]: return None
        return response_text.strip()

    async def _generate_project_structure(self):
        logger.info("Iniciando geração da estrutura do projeto.", component="planner", agent_id=self.project_id, goal=self.goal)
        prompt = (
            f"Baseado no seguinte objetivo do projeto: '{self.goal}', "
            f"gere uma estrutura de arquivos e diretórios adequada. "
            f"Liste APENAS os nomes dos arquivos e diretórios, um por linha. Marque diretórios com '/' no final. "
            f"Não adicione nenhuma explicação ou introdução, apenas a lista.\n"
            f"Exemplo para um webapp simples:\n"
            f"static/\nstatic/style.css\ntemplates/\ntemplates/index.html\napp.py\nREADME.md"
        )
        logger.debug("Enviando prompt para estrutura do projeto...", component="planner", agent_id=self.project_id, prompt_preview=prompt[:200])
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.planner_llm.generate_response(messages=messages, max_tokens=500, temperature=0.2)
        
        if response:
            self.project_structure_str = response.strip()
            logger.info(f"Estrutura do projeto recebida:\n{self.project_structure_str}", component="planner", agent_id=self.project_id)
        else:
            logger.error("Nenhuma resposta recebida do LLM (planner) para a estrutura do projeto.", component="planner", agent_id=self.project_id)
            self.project_structure_str = ""

    async def _generate_file_content(self, filepath_str: str, file_description: Optional[str] = None):
        logger.info(f"Iniciando geração do conteúdo para {filepath_str}.", component="executor", agent_id=self.project_id, file=filepath_str)
        
        file_extension = filepath_str.split('.')[-1].lower() if '.' in filepath_str else "txt"
        lang_map = {"py": "python", "js": "javascript", "html": "html", "css": "css", "md": "markdown", "json": "json", "yaml": "yaml", "yml": "yaml", "txt": "text"}
        language_for_block = lang_map.get(file_extension)

        if not file_description:
            file_description = f"Conteúdo para o arquivo '{filepath_str}' como parte do projeto com objetivo: '{self.goal}'."
            if self.project_structure_str:
                file_description += f"\nPossível contexto da estrutura do projeto (ignore se não relevante para ESTE arquivo):\n{self.project_structure_str}"

        prompt = (
            f"Você é um assistente especialista em desenvolvimento de software e criação de conteúdo. "
            f"Gere o conteúdo completo para o arquivo chamado '{filepath_str}'.\n"
            f"Descrição/Requisitos para este arquivo: {file_description}\n"
            f"Objetivo geral do projeto: {self.goal}\n"
            f"IMPORTANTE: Forneça APENAS o conteúdo solicitado para o arquivo. "
            f"Se for um arquivo de código (Python, HTML, CSS, JS, etc.), coloque o código dentro de um único bloco de código cercado por ```{language_for_block or 'linguagem'} ... ```. "
            f"Se for um arquivo de texto simples (ex: .txt, .md sem formatação rica), apenas o texto. "
            f"Não adicione nenhuma explicação, introdução ou comentários fora do conteúdo do arquivo em si."
        )
        logger.debug(f"Enviando prompt para conteúdo de {filepath_str}...", component="executor", agent_id=self.project_id, prompt_preview=prompt[:200])

        messages = [{"role": "user", "content": prompt}]
        max_tokens_for_file = 3900 if file_extension == "html" else 2000
        temperature_for_file = 0.5 if file_extension == "html" else 0.3

        content_response = await self.executor_llm.generate_response(
            messages=messages, 
            max_tokens=max_tokens_for_file,
            temperature=temperature_for_file
        )
        
        final_content = None
        if content_response:
            final_content = self._extract_code_block(content_response, language_for_block)
            if final_content is None and language_for_block in ["markdown", "text", None]:
                 final_content = content_response.strip()
        
        if not final_content and content_response:
            # raw_response_path = self.context_manager.get_path(f"{os.path.basename(filepath_str)}.raw_response.txt") # get_path retorna Path
            # self.context_manager.save_file(raw_response_path.name, content_response)
            # Simplificado para apenas salvar no diretório raiz do projeto se o nome for simples
            raw_filename = f"{os.path.basename(filepath_str)}.raw_response.txt"
            self.context_manager.save_file(raw_filename, content_response)
            logger.warning(
                f"Nenhum bloco de código {(language_for_block or 'específico')} extraído da resposta para {filepath_str}. "
                f"Resposta bruta salva em: {raw_filename}. Resposta bruta (início):\n{content_response[:200]}...",
                component="executor", agent_id=self.project_id, file=filepath_str
            )
            if file_extension in ["txt", "md"] or not language_for_block:
                 final_content = content_response.strip()
                 logger.info("Usando resposta bruta como conteúdo final.", component = "executor", agent_id=self.project_id, file=filepath_str)

        if final_content:
            filename_to_save = filepath_str # Assume que filepath_str já é o caminho relativo correto
            saved_path = self.context_manager.save_file(filename_to_save, final_content)
            logger.info(f"Conteúdo para {filepath_str} gerado e salvo em {saved_path}.", component="executor", agent_id=self.project_id)
            return True
        else:
            logger.error(f"Falha ao gerar ou extrair conteúdo para {filepath_str}. Nenhuma resposta ou conteúdo válido.", component="executor", agent_id=self.project_id, file=filepath_str)
            return False

    async def run(self):
        logger.info("Iniciando execução do agente.", agent_id=self.project_id, goal=self.goal)
        overall_success = True
        try:
            await self._generate_project_structure()

            if not self.project_structure_str:
                logger.error("Não foi possível gerar a estrutura do projeto. Abortando geração de arquivos.", agent_id=self.project_id)
                overall_success = False
                # Não retorna imediatamente para permitir o fechamento dos clientes no finally

            files_to_generate: List[str] = []
            if self.project_structure_str and overall_success: # Só processa se a estrutura foi gerada
                raw_lines = [line.strip() for line in self.project_structure_str.split('\n')]
                for line in raw_lines:
                    if not line: continue
                    cleaned_line = re.sub(r"^(```[\w]*|- |\* )", "", line).strip()
                    if cleaned_line and not cleaned_line.endswith('/'):
                        files_to_generate.append(cleaned_line)
                    elif cleaned_line.endswith('/'):
                        self.context_manager.ensure_dir_exists(cleaned_line)
                        logger.info(f"Diretório '{cleaned_line}' verificado/criado.", agent_id=self.project_id)
            
            if not files_to_generate and overall_success: # Se overall_success ainda é True mas não há arquivos
                logger.warning("Nenhum arquivo identificado na estrutura do projeto após parsing. Verifique a resposta do planner.", agent_id=self.project_id)
                overall_success = False # Considera falha se o planner não retornou arquivos válidos

            if not overall_success: # Se em algum momento a estrutura falhou ou não gerou arquivos
                 logger.error("Encerrando devido a falha na geração da estrutura ou ausência de arquivos.", agent_id=self.project_id)
            else:
                for filepath_rel in files_to_generate:
                    logger.debug(f"Processando arquivo da estrutura: {filepath_rel}", agent_id=self.project_id)
                    if os.path.dirname(filepath_rel):
                        self.context_manager.ensure_dir_exists(os.path.dirname(filepath_rel))

                    description_for_file = f"Conteúdo para o arquivo '{filepath_rel}' no contexto do projeto: '{self.goal}'. "
                    if filepath_rel.lower().endswith("readme.md"):
                        description_for_file += "Este é o README principal. Descreva o projeto, uso e estrutura."
                    elif filepath_rel.lower().endswith(".html"):
                         description_for_file += "Este é um arquivo HTML. Gere o conteúdo completo."
                    
                    if not await self._generate_file_content(filepath_rel, description_for_file):
                        overall_success = False
                        logger.warning(f"Não foi possível gerar o conteúdo para: {filepath_rel}", agent_id=self.project_id)

        except Exception as e: # Captura exceções mais amplas no run
            logger.opt(exception=True).error(f"Erro crítico durante a execução do agente: {e}", agent_id=self.project_id)
            overall_success = False
        finally:
            if self.planner_llm: await self.planner_llm.close()
            if self.executor_llm: await self.executor_llm.close()
            logger.info(f"Execução do agente finalizada. Sucesso geral: {overall_success}", agent_id=self.project_id, goal=self.goal)
        
        return overall_success
