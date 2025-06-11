import asyncio
import re
import os # Adicionado para os fallbacks de API key
from typing import Optional, List

from evolux_engine.utils.logging_utils import log_entry as log # Usando seu logger
from evolux_engine.settings import settings # Seu arquivo de settings
from evolux_engine.context_manager import ContextManager # Seu ContextManager
from evolux_engine.llms.llm_client import LLMClient # O LLMClient assíncrono


class Agent:
    def __init__(self, project_id: str, goal: str):
        self.project_id = project_id
        self.goal = goal
        self.project_structure_str: str = "" # Para armazenar a estrutura como string

        # Certifique-se de que as API keys estão disponíveis
        # Fallback para variáveis de ambiente se não estiverem em settings
        openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', os.getenv('OPENROUTER_API_KEY'))
        
        if not openrouter_api_key:
            log.error("OPENROUTER_API_KEY não encontrada nas configurações nem nas variáveis de ambiente.", agent_id=self.project_id)
            raise ValueError("OPENROUTER_API_KEY é necessária.")

        # Inicializar LLMClients assíncronos
        # Usar model_name em vez de model
        self.planner_llm = LLMClient(
            api_key=openrouter_api_key,
            model_name=getattr(settings, 'MODEL_PLANNER', "deepseek/deepseek-r1-0528-qwen3-8b:free"), # Fallback
            provider="openrouter",
            http_referer=getattr(settings, 'HTTP_REFERER', "http://localhost"),
            x_title=getattr(settings, 'APP_TITLE', "Evolux Engine TCC")
        )
        self.executor_llm = LLMClient(
            api_key=openrouter_api_key,
            model_name=getattr(settings, 'MODEL_EXECUTOR', "deepseek/deepseek-r1-0528-qwen3-8b:free"), # Fallback
            provider="openrouter",
            http_referer=getattr(settings, 'HTTP_REFERER', "http://localhost"),
            x_title=getattr(settings, 'APP_TITLE', "Evolux Engine TCC")
        )
        
        # Inicializar ContextManager
        # O path para o ContextManager deve levar em conta o settings.PROJECT_BASE_DIR
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

    def _extract_code_block(self, response_text: str, language: Optional[str] = None) -> Optional[str]:
        """
        Extrai o conteúdo de um bloco de código Markdown da resposta do LLM.
        Se 'language' for fornecido, procura por um bloco com esse idioma.
        Caso contrário, tenta encontrar o primeiro bloco de código genérico.
        """
        if not response_text:
            return None

        if language:
            # Tenta encontrar um bloco de código com o idioma especificado
            pattern = re.compile(rf"```{language}\s*([\s\S]*?)\s*```", re.MULTILINE)
        else:
            # Tenta encontrar qualquer bloco de código
            pattern = re.compile(r"```(?:\w+\s*)?([\s\S]*?)\s*```", re.MULTILINE)
        
        match = pattern.search(response_text)
        if match:
            return match.group(1).strip()
        
        # Se nenhum bloco de código Markdown for encontrado, e não for Markdown/texto puro,
        # pode ser que a LLM tenha retornado o código diretamente.
        # Esta é uma heurística e pode precisar de ajuste.
        # Se o objetivo é HTML e a resposta começa com <!DOCTYPE html>, assume que é o conteúdo.
        if language == "html" and response_text.lower().lstrip().startswith("<!doctype html"):
            return response_text.strip()
        
        # Se language não foi especificado E nenhum bloco foi encontrado,
        # retorne None para indicar que o parsing explícito falhou.
        # A lógica de chamada decidirá se usa a resposta bruta.
        if not language:
            return None
            
        # Se um idioma foi especificado mas não encontrado, e não é um .md ou .txt, retorne None.
        # Para .md e .txt, a ausência de ```bloco``` pode significar que o conteúdo é o texto inteiro.
        if language not in ["markdown", "md", "txt", "text"]:
             return None

        # Fallback final: se for esperado markdown/txt e nenhum bloco encontrado, retorna o texto inteiro.
        # Isso assume que, para esses tipos, a LLM pode omitir os delimitadores ```.
        return response_text.strip()


    async def _generate_project_structure(self):
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
        response = await self.planner_llm.generate_response(messages=messages, max_tokens=500, temperature=0.2)
        
        if response:
            self.project_structure_str = response.strip()
            log.info(f"Estrutura do projeto recebida:\n{self.project_structure_str}", component="planner", agent_id=self.project_id)
        else:
            log.error("Nenhuma resposta recebida do LLM (planner) para a estrutura do projeto.", component="planner", agent_id=self.project_id)
            self.project_structure_str = "" # Define um padrão ou trata o erro mais robustamente

    async def _generate_file_content(self, filepath_str: str, file_description: Optional[str] = None):
        log.info(f"Iniciando geração do conteúdo para {filepath_str}.", component="executor", agent_id=self.project_id)
        
        file_extension = filepath_str.split('.')[-1].lower() if '.' in filepath_str else "txt"
        # Mapeamento simples de extensões para linguagens de Markdown
        lang_map = {"py": "python", "js": "javascript", "html": "html", "css": "css", "md": "markdown", "json": "json", "yaml": "yaml", "yml": "yaml", "txt": "text"}
        language_for_block = lang_map.get(file_extension)

        if not file_description:
            file_description = f"Conteúdo para o arquivo '{filepath_str}' como parte do projeto com objetivo: '{self.goal}'."
            if self.project_structure_str: # Adicionar contexto da estrutura se disponível
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
        # Para HTML com muito texto, pode precisar de mais tokens
        max_tokens_for_file = 3900 if file_extension == "html" else 2000
        temperature_for_file = 0.5 if file_extension == "html" else 0.3 # Mais criativo para HTML, mais direto para código

        content_response = await self.executor_llm.generate_response(
            messages=messages, 
            max_tokens=max_tokens_for_file,
            temperature=temperature_for_file
        )
        
        final_content = None
        if content_response:
            final_content = self._extract_code_block(content_response, language_for_block)
            if final_content is None and language_for_block in ["markdown", "text", None]: # Se for texto puro e não encontrou bloco
                 final_content = content_response.strip() # Usa a resposta inteira
        
        if not final_content and content_response: # Se parsing explícito falhou mas houve resposta
            # Salvar a resposta bruta se o parsing falhar ou não encontrar conteúdo
            raw_response_path = self.context_manager.get_path(f"{os.path.basename(filepath_str)}.raw_response.txt")
            self.context_manager.save_file(raw_response_path.name, content_response) # Passar apenas o nome do arquivo
            log.warning(f"Nenhum bloco de código {(language_for_block or 'específico')} extraído da resposta para {filepath_str}. "
                        f"Resposta bruta salva em: {raw_response_path}. Resposta bruta (início):\n{content_response[:500]}",
                        component="executor", agent_id=self.project_id)
            # Decidir usar a resposta bruta como fallback
            if file_extension in ["txt", "md"] or not language_for_block: # Se for texto ou linguagem desconhecida
                 final_content = content_response.strip()
                 log.info("Usando resposta bruta como conteúdo final para arquivo de texto/desconhecido.", component = "executor", agent_id=self.project_id, file=filepath_str)

        if final_content:
            # O ContextManager.save_file espera apenas o nome relativo do arquivo, não um Path completo de fora.
            # A função get_path dentro do ContextManager já constrói o caminho completo.
            filename_to_save = os.path.basename(filepath_str) # Garante que estamos salvando no diretório do projeto
            if os.path.dirname(filepath_str): # Se filepath_str inclui subdiretórios
                filename_to_save = filepath_str # Usa o caminho relativo completo

            saved_path = self.context_manager.save_file(filename_to_save, final_content)
            log.info(f"Conteúdo para {filepath_str} gerado e salvo em {saved_path}.", component="executor", agent_id=self.project_id)
            return True
        else:
            log.error(f"Falha ao gerar ou extrair conteúdo para {filepath_str}. Nenhuma resposta ou conteúdo válido da LLM.", component="executor", agent_id=self.project_id)
            return False

    async def run(self):
        log.info("Iniciando execução do agente.", agent_id=self.project_id, goal=self.goal)
        success = True
        try:
            await self._generate_project_structure()

            if not self.project_structure_str:
                log.error("Não foi possível gerar a estrutura do projeto. Abortando a geração de arquivos.", agent_id=self.project_id)
                success = False
                return # Retorna aqui para evitar o bloco finally fechar os clientes prematuramente se houver mais lógica

            files_to_generate: List[str] = []
            if self.project_structure_str:
                # Normaliza para remover espaços em branco de cada linha antes de processar
                raw_lines = [line.strip() for line in self.project_structure_str.split('\n')]
                for line in raw_lines:
                    if not line: # Ignora linhas vazias
                        continue
                    # Remove prefixos comuns como "```", "- ", "* "
                    cleaned_line = re.sub(r"^(```[\w]*|- |\* )", "", line).strip()
                    if cleaned_line and not cleaned_line.endswith('/'): # Adiciona apenas arquivos
                        files_to_generate.append(cleaned_line)
                    elif cleaned_line.endswith('/'): # É um diretório
                        self.context_manager.ensure_dir_exists(cleaned_line) # Cria o diretório
                        log.info(f"Diretório '{cleaned_line}' verificado/criado.", agent_id=self.project_id)
            
            if not files_to_generate:
                log.warning("Nenhum arquivo identificado na estrutura do projeto após parsing. Verifique a resposta do planner.", agent_id=self.project_id)
                # Fallback para arquivos padrão se NENHUM arquivo for identificado.
                # Você pode querer remover este fallback para forçar o planner a funcionar.
                # files_to_generate = ["index.html", "README.md"] 
                # log.info(f"Usando arquivos de fallback: {files_to_generate}", agent_id=self.project_id)
                success = False # Considera falha se o planner não retornou arquivos


            if not files_to_generate and not success: # Se o planner falhou e δεν há fallback
                 log.error("Planner não retornou arquivos válidos e não há fallback. Encerrando.")
                 return

            for filepath_rel in files_to_generate:
                log.info(f"Processando arquivo da estrutura: {filepath_rel}", agent_id=self.project_id)
                # Garante que subdiretórios sejam criados se o path do arquivo os contiver
                if os.path.dirname(filepath_rel):
                    self.context_manager.ensure_dir_exists(os.path.dirname(filepath_rel))

                description_for_file = f"Conteúdo para o arquivo '{filepath_rel}' no contexto do projeto: '{self.goal}'. "
                if filepath_rel.lower().endswith("readme.md"):
                    description_for_file += "Este é o arquivo README principal do projeto. Descreva o projeto, como usá-lo/executá-lo, e a estrutura geral."
                elif filepath_rel.lower().endswith(".html"):
                     description_for_file += "Este é um arquivo HTML. Gere o conteúdo completo, incluindo tags <html>, <head>, <body>."
                
                if not await self._generate_file_content(filepath_rel, description_for_file):
                    success = False # Marca falha se algum arquivo não for gerado
                    log.warning(f"Não foi possível gerar o conteúdo para o arquivo: {filepath_rel}", agent_id=self.project_id)


        except Exception as e:
            log.error(f"Erro durante a execução do agente: {str(e)}", agent_id=self.project_id, exc_info=True)
            success = False
        finally:
            # Fechar os clientes LLM no final da execução do agente
            if self.planner_llm:
                await self.planner_llm.close()
            if self.executor_llm:
                await self.executor_llm.close()
            log.info(f"Execução do agente {'concluída com sucesso.' if success else 'concluída com falhas.'}", agent_id=self.project_id, goal=self.goal)
        
        return success # Retorna o status de sucesso

