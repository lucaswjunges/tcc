import asyncio
import re
import os
from typing import Optional, List

from loguru import logger as log

from evolux_engine.settings import settings
from evolux_engine.context_manager import ContextManager
from evolux_engine.llms.llm_client import LLMClient

class Agent:
    def __init__(self, project_id: str, goal: str):
        self.project_id = project_id
        self.goal = goal
        self.project_structure_str: str = ""

        # --- INÍCIO DA MODIFICAÇÃO ---
        # Lógica para selecionar a API Key correta baseada no provedor
        provider = settings.LLM_PROVIDER
        if provider == "google":
            api_key_to_use = settings.GOOGLE_API_KEY
            if not api_key_to_use:
                raise ValueError("LLM_PROVIDER é 'google', mas GOOGLE_API_KEY não foi encontrada.")
        else: # Padrão para openrouter ou outros
            api_key_to_use = settings.OPENROUTER_API_KEY
            if not api_key_to_use:
                raise ValueError(f"LLM_PROVIDER é '{provider}', mas OPENROUTER_API_KEY não foi encontrada.")
        # --- FIM DA MODIFICAÇÃO ---

        self.planner_llm = LLMClient(
            api_key=api_key_to_use,
            model_name=settings.MODEL_PLANNER,
            provider=provider
        )
        self.executor_llm = LLMClient(
            api_key=api_key_to_use,
            model_name=settings.MODEL_EXECUTOR,
            provider=provider
        )
        
        project_base_dir = getattr(settings, 'PROJECT_BASE_DIR', './project_workspaces')
        self.context_manager = ContextManager(project_id=project_id, base_project_dir=project_base_dir)

        log.info(
            "Agente inicializado.",
            agent_id=self.project_id,
            goal=self.goal,
            planner_model=self.planner_llm.model_name,
            executor_model=self.executor_llm.model_name,
            project_path=self.context_manager.project_path
        )
    
    # ... (O RESTO DO ARQUIVO agent.py CONTINUA IGUAL)
    # ... (Não precisa colar o resto, ele não muda)
    def _extract_code_block(self, response_text: str, language: Optional[str] = None) -> Optional[str]:
        # ... (código existente)
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
        
        if not language:
            return None
            
        if language not in ["markdown", "md", "txt", "text"]:
             return None

        return response_text.strip()


    async def _generate_project_structure(self):
        # ... (código existente)
        log.info("Iniciando geração da estrutura do projeto.", component="planner", agent_id=self.project_id, goal=self.goal)
        prompt = (
            f"Baseado no seguinte objetivo do projeto: '{self.goal}', "
            f"gere uma estrutura de arquivos e diretórios adequada. "
            f"Se for um projeto de código, sugira os arquivos principais. Se for um documento, talvez apenas um arquivo. "
            f"Liste APENAS os nomes dos arquivos e diretórios, um por linha. Marque diretórios com '/' no final. "
            f"Não adicione nenhuma explicação ou introdução, apenas a lista.\n"
            f"Exemplo para um webapp simples:\n"
            f"static/\n"
            f"static/style.css\n"
            f"templates/\n"
            f"templates/index.html\n"
            f"app.py\n"
            f"README.md"
        )
        log.info("Enviando prompt para estrutura do projeto...", component="planner", agent_id=self.project_id, goal=self.goal)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.planner_llm.generate_response(messages=messages, max_tokens=2000, temperature=0.2)
        
        if response:
            self.project_structure_str = response.strip()
            log.info(f"Estrutura do projeto recebida:\n{self.project_structure_str}", component="planner", agent_id=self.project_id)
        else:
            log.error("Nenhuma resposta recebida do LLM (planner) para a estrutura do projeto.", component="planner", agent_id=self.project_id)
            self.project_structure_str = ""

    async def _generate_file_content(self, filepath_str: str, file_description: Optional[str] = None):
        # ... (código existente)
        log.info(f"Iniciando geração do conteúdo para {filepath_str}.", component="executor", agent_id=self.project_id)
        
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
        log.info(f"Enviando prompt para conteúdo de {filepath_str}...", component="executor", agent_id=self.project_id)

        messages = [{"role": "user", "content": prompt}]
        
        max_tokens_for_file = 8000 
        temperature_for_file = 0.3

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
            raw_response_path = self.context_manager.get_path(f"{os.path.basename(filepath_str)}.raw_response.txt")
            self.context_manager.save_file(raw_response_path.name, content_response)
            log.warning(f"Nenhum bloco de código extraído para {filepath_str}. Resposta bruta salva em: {raw_response_path}.",
                        component="executor", agent_id=self.project_id)
            if file_extension in ["txt", "md"] or not language_for_block:
                 final_content = content_response.strip()
                 log.info("Usando resposta bruta como conteúdo final.", component = "executor", agent_id=self.project_id, file=filepath_str)

        if final_content:
            filename_to_save = filepath_str
            saved_path = self.context_manager.save_file(filename_to_save, final_content)
            log.info(f"Conteúdo para {filepath_str} gerado e salvo em {saved_path}.", component="executor", agent_id=self.project_id)
            return True
        else:
            log.error(f"Falha ao gerar ou extrair conteúdo para {filepath_str}.", component="executor", agent_id=self.project_id)
            return False

    async def run(self):
        # ... (código existente)
        log.info("Iniciando execução do agente.", agent_id=self.project_id, goal=self.goal)
        success = True
        try:
            await self._generate_project_structure()

            if not self.project_structure_str:
                log.error("Não foi possível gerar a estrutura do projeto. Abortando.", agent_id=self.project_id)
                success = False
                return

            files_to_generate: List[str] = []
            if self.project_structure_str:
                raw_lines = [line.strip() for line in self.project_structure_str.split('\n')]
                for line in raw_lines:
                    if not line:
                        continue
                    cleaned_line = re.sub(r"^(```[\w]*|- |\* )", "", line).strip()
                    if cleaned_line and not cleaned_line.endswith('/'):
                        files_to_generate.append(cleaned_line)
                    elif cleaned_line.endswith('/'):
                        self.context_manager.ensure_dir_exists(cleaned_line)
                        log.info(f"Diretório '{cleaned_line}' verificado/criado.", agent_id=self.project_id)
            
            if not files_to_generate:
                log.warning("Nenhum arquivo identificado na estrutura após parsing.", agent_id=self.project_id)
                success = False

            if not files_to_generate and not success:
                 log.error("Planner não retornou arquivos válidos. Encerrando.")
                 return

            for filepath_rel in files_to_generate:
                log.info(f"Processando arquivo da estrutura: {filepath_rel}", agent_id=self.project_id)
                if os.path.dirname(filepath_rel):
                    self.context_manager.ensure_dir_exists(os.path.dirname(filepath_rel))

                description_for_file = f"Conteúdo para o arquivo '{filepath_rel}' no contexto do projeto: '{self.goal}'. "
                if filepath_rel.lower().endswith("readme.md"):
                    description_for_file += "Descreva o projeto, como usá-lo/executá-lo, e a estrutura geral."
                elif filepath_rel.lower().endswith(".html"):
                     description_for_file += "Gere o conteúdo HTML completo, incluindo <html>, <head>, e <body>."
                
                if not await self._generate_file_content(filepath_rel, description_for_file):
                    success = False
                    log.warning(f"Não foi possível gerar o conteúdo para o arquivo: {filepath_rel}", agent_id=self.project_id)

        except Exception as e:
            log.error(f"Erro durante a execução do agente: {str(e)}", agent_id=self.project_id, exc_info=True)
            success = False
        finally:
            if self.planner_llm:
                await self.planner_llm.close()
            if self.executor_llm:
                await self.executor_llm.close()
            log.info(f"Execução do agente {'concluída com sucesso.' if success else 'concluída com falhas.'}", agent_id=self.project_id, goal=self.goal)
        
        return success