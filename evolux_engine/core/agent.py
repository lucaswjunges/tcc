# evolux_engine/agent.py
import re
import uuid
import asyncio # Adicionado
from typing import Optional, List

from evolux_engine.llms.llm_client import LLMClient
from evolux_engine.context_manager import ContextManager
from evolux_engine.utils.logging_utils import log, setup_logging_level
from evolux_engine.settings import settings # Importar configurações

class Agent:
    def __init__(self, project_id: str, goal: str):
        self.project_id = project_id
        self.goal = goal
        self.context_manager = ContextManager(project_id, base_path=settings.project_base_dir)
        self.project_structure_str: str = "" # Estrutura de arquivos/diretórios como string

        # Configurar nível de logging baseado nas settings
        setup_logging_level(settings.logging_level)

        log.info(f"Inicializando LLMClients para Agente {project_id}")
        # Usar valores das 'settings'
        self.planner_llm = LLMClient(
            api_key=settings.openrouter_api_key, 
            model_name=settings.model_planner,
            provider=settings.llm_provider,
            http_referer=settings.http_referer,
            x_title=settings.app_title
        )
        log.info(f"LLM client (planner) criado para {settings.llm_provider} com modelo {settings.model_planner}.", agent_id=self.project_id, goal=self.goal)
        
        self.executor_llm = LLMClient(
            api_key=settings.openrouter_api_key, 
            model_name=settings.model_executor,
            provider=settings.llm_provider,
            http_referer=settings.http_referer,
            x_title=settings.app_title
        )
        log.info(f"LLM client (executor) criado para {settings.llm_provider} com modelo {settings.model_executor}.", agent_id=self.project_id, goal=self.goal)
        log.info(f"Agente inicializado. Provedor LLM: {settings.llm_provider}. Status: Executor LLM: OK, Planner LLM: OK", agent_id=self.project_id, goal=self.goal)


    async def _generate_project_structure(self):
        log.info("Iniciando geração da estrutura do projeto.", agent_id=self.project_id, goal=self.goal)
        prompt = (
            f"Baseado no seguinte objetivo do projeto: '{self.goal}', "
            f"gere uma estrutura de arquivos e diretórios adequada. "
            f"Se for um projeto de código, sugira os arquivos principais. Se for um documento, talvez apenas um arquivo. "
            f"Liste APENAS os nomes dos arquivos e diretórios, um por linha. Marque diretórios com '/' no final. "
            f"Não inclua explicações adicionais, apenas a lista de caminhos.\n"
            f"Exemplo para um app Python simples:\n"
            f"app/\n"
            f"app/__init__.py\n"
            f"app/main.py\n"
            f"app/utils.py\n"
            f"tests/\n"
            f"tests/test_main.py\n"
            f"requirements.txt\n"
            f"README.md"
        )
        log.info("Enviando prompt para estrutura do projeto...", agent_id=self.project_id, goal=self.goal)
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.planner_llm.generate_response(messages=messages, max_tokens=500)
        
        if response:
            self.project_structure_str = response.strip()
            log.info(f"Estrutura do projeto recebida:\n{self.project_structure_str}", agent_id=self.project_id, goal=self.goal)
        else:
            log.error("Nenhuma resposta recebida do LLM (planner) para a estrutura do projeto.", agent_id=self.project_id, goal=self.goal)
            self.project_structure_str = "" 

    def _extract_code_from_response(self, response_text: str, language: Optional[str] = None) -> Optional[str]:
        if not response_text:
            return None

        # Tentativa de extrair de blocos de código específicos
        if language:
            pattern = re.compile(rf"```{language}\s*([\s\S]*?)\s*```", re.MULTILINE)
            match = pattern.search(response_text)
            if match:
                return match.group(1).strip()

        # Tentativa de extrair de blocos de código genéricos
        pattern_generic = re.compile(r"```(?:\w+)?\s*([\s\S]*?)\s*```", re.MULTILINE)
        match_generic = pattern_generic.search(response_text)
        if match_generic:
            return match_generic.group(1).strip()
        
        # Se nenhum bloco de código for encontrado, e o prompt pediu para não ter explicações,
        # pode ser que a LLM tenha retornado o conteúdo diretamente.
        # Mas só se o prompt foi muito claro sobre "APENAS o conteúdo".
        # Para ser mais seguro, vamos retornar None se nenhum bloco foi encontrado,
        # a menos que uma lógica mais sofisticada seja adicionada.
        # Pode-se assumir que se não há ``` e não há muitas frases explicativas, é o conteúdo.
        # Por agora, mantemos a extração por ```
        
        # Se a resposta não contiver "```" e for relativamente curta e sem frases tipo "aqui está o código",
        # poderia ser o conteúdo direto. Isso é mais arriscado.
        # if "```" not in response_text and len(response_text.splitlines()) > 1 and not any(
        #    phrase in response_text.lower() for phrase in ["of course", "here is", "i have generated"]
        # ):
        #    return response_text.strip()

        return None # Não encontrou bloco de código claro

    async def _generate_file_content(self, filepath_str: str, file_description: Optional[str] = None):
        log.info(f"Iniciando geração do conteúdo para {filepath_str}.", agent_id=self.project_id, goal=self.goal)
        
        file_extension = filepath_str.split('.')[-1] if '.' in filepath_str else "txt"
        language_map = {
            "py": "python", "js": "javascript", "html": "html", "css": "css",
            "md": "markdown", "json": "json", "yaml": "yaml", "yml": "yaml",
            "txt": "text", "sh": "bash", "java": "java", "c": "c", "cpp": "cpp",
            "go": "go", "rs": "rust", "ts": "typescript"
        }
        language_hint = language_map.get(file_extension, file_extension) # Para o bloco de código ```<language>


        if not file_description:
            file_description = f"Conteúdo completo e funcional para o arquivo '{filepath_str}' como parte do projeto com objetivo: '{self.goal}'."
            if self.project_structure_str: # Adicionar contexto da estrutura se disponível
                file_description += f"\nO projeto possui a seguinte estrutura de arquivos (o arquivo atual é '{filepath_str}'):\n{self.project_structure_str}"

        prompt = (
            f"Você é um assistente especialista em desenvolvimento de software e criação de conteúdo. "
            f"Gere o conteúdo completo e funcional para o arquivo chamado '{filepath_str}'.\n"
            f"Descrição/Requisitos para este arquivo: {file_description}\n"
            f"Objetivo geral do projeto: {self.goal}\n"
            f"IMPORTANTE: Forneça APENAS o conteúdo do arquivo, sem explicações adicionais. "
            f"O conteúdo deve estar dentro de um único bloco de código formatado como ```{language_hint} ... ```. "
            f"Por exemplo, para um arquivo Python, use ```python ... ```. Para HTML, ```html ... ```. Para texto simples, ```text ... ```. "
            f"Não adicione nenhuma frase introdutória ou conclusiva fora do bloco de código."
        )
        log.info(f"Enviando prompt para conteúdo de {filepath_str}...", agent_id=self.project_id, goal=self.goal)

        messages = [{"role": "user", "content": prompt}]
        # Aumente max_tokens se espera arquivos muito grandes, mas cuidado com custos/limites
        content_response = await self.executor_llm.generate_response(messages=messages, max_tokens_override=settings.MAX_TOKENS_EXECUTOR) 
        
        final_content = None
        if content_response:
            final_content = self._extract_code_from_response(content_response, language_hint)
            if not final_content and language_hint != "text": # Tentar com 'text' se hint específico falhou
                 final_content = self._extract_code_from_response(content_response, "text")
            if not final_content: # Última tentativa: genérico
                 final_content = self._extract_code_from_response(content_response)


        if not final_content:
            raw_response_path_str = f"{filepath_str}.raw_response.txt"
            self.context_manager.save_file(raw_response_path_str, content_response or "Nenhuma resposta recebida da LLM.")
            preview = (content_response[:500] + "...") if content_response and len(content_response) > 500 else (content_response or 'VAZIO')
            log.warning(f"Nenhum bloco de código '{language_hint}' (ou alternativo) encontrado na resposta para '{filepath_str}'. "
                        f"Resposta bruta salva em: {raw_response_path_str}. Início da resposta bruta:\n{preview}",
                        agent_id=self.project_id, goal=self.goal)
            # DECISÃO: Usar a resposta bruta como fallback?
            # Se o prompt for muito bem obedecido, a LLM pode retornar SÓ o conteúdo sem ```
            # Por ora, vamos considerar falha se não extrair do bloco, mas isso pode ser ajustado.
            # final_content = content_response # DESCOMENTE PARA USAR RESPOSTA BRUTA COMO FALLBACK

        if final_content:
            full_path = self.context_manager.save_file(filepath_str, final_content)
            log.info(f"Conteúdo para {filepath_str} gerado e salvo em {full_path}.", agent_id=self.project_id, goal=self.goal)
            return True
        else:
            log.error(f"Falha ao gerar ou extrair conteúdo para {filepath_str}.", agent_id=self.project_id, goal=self.goal)
            return False

    async def run(self):
        log.info("Iniciando execução do agente.", agent_id=self.project_id, goal=self.goal)
        try:
            await self._generate_project_structure()

            if not self.project_structure_str:
                log.error("Não foi possível gerar a estrutura do projeto. Abortando a geração de arquivos.", agent_id=self.project_id)
                return # Não prosseguir se a estrutura falhou

            files_to_generate: List[str] = []
            # Parse self.project_structure_str. Simples split por linha.
            # Isso assume que a LLM retornou uma lista de caminhos, um por linha.
            parsed_files = [line.strip() for line in self.project_structure_str.split('\n') if line.strip()]
            
            for item_path_str in parsed_files:
                if item_path_str.endswith('/'):
                    # É um diretório, garantir que exista
                    log.info(f"Garantindo que o diretório '{item_path_str}' exista.")
                    self.context_manager.ensure_dir_exists(item_path_str)
                else:
                    # É um arquivo para gerar
                    files_to_generate.append(item_path_str)
            
            if not files_to_generate and not any(p.endswith('/') for p in parsed_files):
                log.warning("Nenhum arquivo específico identificado na estrutura do projeto retornada pela LLM. "
                            "Verifique o formato da resposta da LLM para a estrutura.", agent_id=self.project_id)
                # Se o objetivo era um único arquivo HTML, e a LLM retornou só "index.html"
                # Ou se a LLM retornou uma descrição em vez de uma lista de arquivos.
                # Para o seu objetivo específico, talvez um fallback seja criar 'index.html'
                if "página html" in self.goal.lower() and not any(f.lower().endswith(".html") for f in files_to_generate):
                    log.info("Objetivo parece ser uma página HTML, adicionando 'index.html' à lista de geração como fallback.")
                    files_to_generate.append("index.html")


            if not files_to_generate:
                log.error("Nenhum arquivo para gerar após processar a estrutura do projeto. Verifique a resposta da LLM de planejamento.", agent_id=self.project_id)
                return

            log.info(f"Arquivos a serem gerados: {files_to_generate}", agent_id=self.project_id)

            for filepath_str in files_to_generate:
                # A descrição do arquivo pode vir da LLM de planejamento ou ser genérica
                description_for_file = f"Conteúdo para o arquivo '{filepath_str}' no projeto '{self.goal}'."
                if filepath_str.lower() == "readme.md":
                    description_for_file = (f"Um arquivo README.md detalhado para o projeto com o objetivo: '{self.goal}'. "
                                           f"Deve incluir uma visão geral do projeto, como usá-lo ou executá-lo (se aplicável), "
                                           f"e um resumo da estrutura de arquivos planejada:\n{self.project_structure_str}")
                elif filepath_str.lower().endswith(".html"):
                     description_for_file = (f"O conteúdo HTML completo para o arquivo '{filepath_str}'. "
                                             f"Este arquivo faz parte de um projeto com o objetivo: '{self.goal}'. "
                                             f"O HTML deve ser bem estruturado, semanticamente correto e visualmente agradável. "
                                             f"Se o objetivo mencionou 'pelo menos 1000 linhas de texto e com imagens', "
                                             f"certifique-se de incluir conteúdo substancial e placeholders para imagens (ex: <img src='placeholder.jpg' alt='Descrição'>) "
                                             f"ou sugestões de onde buscar imagens ou como elas deveriam ser. "
                                             f"Inclua uma introdução, corpo principal com várias seções e, se apropriado, uma conclusão. "
                                             f"Se for sobre 'evolução da espécie humana', cubra os principais marcos.")


                await self._generate_file_content(filepath_str, description_for_file)

            log.info("Execução do agente concluída.", agent_id=self.project_id, goal=self.goal)
        
        except Exception as e:
            log.opt(exception=True).error(f"Erro durante a execução do agente {self.project_id}.", error=str(e))
        
        finally:
            log.info(f"Fechando clientes LLM para Agente {self.project_id}...")
            if self.planner_llm:
                await self.planner_llm.close()
            if self.executor_llm:
                await self.executor_llm.close()
            log.info(f"Clientes LLM para Agente {self.project_id} fechados.")
