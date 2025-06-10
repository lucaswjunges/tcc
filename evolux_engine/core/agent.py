import os
from typing import Optional

from evolux_engine.utils.logging_utils import log # Usar o logger global
from evolux_engine.utils.env_vars import settings
from evolux_engine.llms.llm_factory import LLMFactory
from evolux_engine.core.context_manager import ContextManager
from evolux_engine.utils.string_utils import extract_first_code_block

class Agent:
    def __init__(self, goal: str, context_manager: ContextManager, llm_provider_override: Optional[str] = None):
        # Bind do logger para este agente específico
        self.log = log.bind(agent_id=context_manager.project_id, goal=goal)
        self.goal = goal
        self.context_manager = context_manager
        self.log.info("Inicializando Agente...")

        self.llm_provider = llm_provider_override or settings.LLM_PROVIDER
        self.api_key = None
        if self.llm_provider == "openai":
            self.api_key = settings.OPENAI_API_KEY
        elif self.llm_provider == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
        
        self.executor_llm = None # LLM para execução
        self.planner_llm = None  # LLM para planejamento

        if not self.api_key:
            self.log.error(f"API key para {self.llm_provider} não configurada. LLM não será funcional.")
        else:
            try:
                llm_factory = LLMFactory(api_key=self.api_key)
                
                # Criar cliente LLM para execução
                self.executor_llm = llm_factory.get_llm_client(
                    provider=self.llm_provider, 
                    model=settings.MODEL_EXECUTOR
                )
                self.log.info(f"LLM client (executor) criado para {self.llm_provider} com modelo {settings.MODEL_EXECUTOR}.")

                # Criar cliente LLM para planejamento
                self.planner_llm = llm_factory.get_llm_client(
                    provider=self.llm_provider,
                    model=settings.MODEL_PLANNER
                )
                self.log.info(f"LLM client (planner) criado para {self.llm_provider} com modelo {settings.MODEL_PLANNER}.")

            except Exception as e:
                self.log.error(f"Falha ao criar um ou mais LLM clients: {e}", exc_info=True)
                # Se um falhar, pode ser que o outro também, ou podemos querer tratar separadamente.
                # Por simplicidade, se houver erro, ambos podem ficar None.
                if self.executor_llm is None: self.log.warning("Executor LLM não pôde ser inicializado.")
                if self.planner_llm is None: self.log.warning("Planner LLM não pôde ser inicializado.")


        llm_status_msg = f"Executor LLM: {'OK' if self.executor_llm else 'Indisponível'}, Planner LLM: {'OK' if self.planner_llm else 'Indisponível'}"
        self.log.info(f"Agente inicializado. Provedor LLM: {self.llm_provider}. Status: {llm_status_msg}")


    def run(self):
        self.log.info("Iniciando execução do agente.")
        self.context_manager.add_log_entry("agent_status", "Iniciando execução do Agente.", {"goal": self.goal})

        if not self.executor_llm or not self.planner_llm:
            self.log.error("Um ou ambos os LLM clients (executor/planner) não estão disponíveis. Não é possível prosseguir.")
            self.context_manager.add_log_entry("agent_error", "LLM client(s) indisponível(is). Encerrando.")
            return

        # 1. Gerar estrutura do projeto
        self._generate_and_create_project_structure()

        # 2. Gerar conteúdo do arquivo principal (ex: app.py)
        self._generate_and_save_main_app_file()

        self.log.info("Execução do agente concluída.")
        self.context_manager.add_log_entry("agent_status", "Execução do Agente concluída.")
          
    def _generate_and_create_project_structure(self):
        self.log.info("Iniciando geração da estrutura do projeto.")
        if not self.planner_llm: # Usa o planner_llm
            self.log.error("LLM Planner indisponível, não é possível gerar estrutura do projeto.")
            self.context_manager.add_log_entry("agent_error", "LLM Planner indisponível para gerar estrutura.")
            return

        structure_prompt = f"""
        Baseado no objetivo: "{self.goal}", crie uma estrutura básica e simples de arquivos e diretórios para este projeto.
        Liste os arquivos e diretórios, um por linha.
        Para diretórios, termine o nome com uma barra '/'. Use apenas nomes válidos para arquivos/diretórios.
        Exemplo de resposta para um app Flask simples:
        app.py
        templates/
        templates/index.html
        static/
        static/style.css
        requirements.txt
        README.md

        Se o projeto for muito simples e precisar apenas de um arquivo, liste apenas esse arquivo.
        Responda APENAS com a lista de arquivos/diretórios. Não adicione explicações nem ```.
        """
        self.log.info("Enviando prompt para estrutura do projeto...")
        self.context_manager.add_log_entry("llm_prompt", "Prompt para estrutura do projeto.", 
                                           {"prompt": structure_prompt, "model": settings.MODEL_PLANNER})
        
        try:
            structure_response = self.planner_llm.generate_response(prompt=structure_prompt, temperature=0.1, max_tokens=500)
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM (planner) para estrutura do projeto: {e}", exc_info=True)
            self.context_manager.add_log_entry("llm_error", f"Erro ao gerar estrutura: {e}")
            structure_response = None

        if structure_response:
            self.log.info(f"Resposta da estrutura recebida:\n{structure_response}")
            self.context_manager.add_log_entry("llm_response", "Resposta da estrutura do projeto.", {"response": structure_response})
            self._create_project_structure_from_text(structure_response)
        else:
            self.log.error("Nenhuma resposta recebida do LLM (planner) para a estrutura do projeto.")
            self.context_manager.add_log_entry("llm_error", "Nenhuma resposta para estrutura do projeto.")

    def _create_project_structure_from_text(self, structure_text: str):
        self.log.info(f"Criando estrutura do projeto em: {self.context_manager.project_dir}")
        lines = structure_text.strip().split('\n')
        created_paths = []
        for line in lines:
            path_item = line.strip()
            if not path_item or path_item.startswith("#") or "```" in path_item or "<" in path_item or ">" in path_item: # Filtra mais
                self.log.debug(f"Item ignorado da estrutura: '{path_item}'")
                continue
            
            try:
                if path_item.endswith('/'):
                    self.context_manager.create_directory(path_item)
                else:
                    self.context_manager.save_file(path_item, "# Conteúdo a ser gerado\n") # Salva com placeholder
                created_paths.append(path_item)
            except Exception as e:
                self.log.error(f"Falha ao processar item da estrutura '{path_item}': {e}", exc_info=False)
        if not created_paths:
            self.log.warning("Nenhuma estrutura de arquivo/diretório foi criada a partir da resposta do LLM.")

    def _generate_and_save_main_app_file(self, filename: str = "app.py"): # Tornar filename um argumento se necessário
        self.log.info(f"Iniciando geração do conteúdo para {filename}.")
        if not self.executor_llm: # Usa o executor_llm
            self.log.error(f"LLM Executor indisponível, não é possível gerar {filename}.")
            self.context_manager.add_log_entry("agent_error", f"LLM Executor indisponível para gerar {filename}.")
            return
        
        # Checa se o arquivo existe na estrutura planejada
        potential_path = os.path.join(self.context_manager.project_dir, filename)
        if not os.path.exists(potential_path):
            # Se o planner não o criou, talvez o LLM o crie ao gerar o conteúdo.
            # Ou podemos forçar a criação do arquivo vazio aqui se quisermos.
            # Por ora, vamos apenas avisar se ele não foi planejado.
            self.log.warning(f"O arquivo '{filename}' não foi explicitamente listado na estrutura inicial. Será gerado mesmo assim.")
            # self.context_manager.save_file(filename, "# Arquivo principal\n") # Cria se não existir

        app_py_prompt = f"""
        Crie o conteúdo Python completo para o arquivo `{filename}`.
        O objetivo do projeto é: "{self.goal}".
        O código deve estar pronto para ser executado, incluindo todas as importações necessárias.
        Se for uma aplicação Flask, configure para rodar em `host='0.0.0.0'` e `port=5000`.
        Responda APENAS com o bloco de código Python, formatado assim:
        ```python
        # Seu código Python aqui
        ```
        Não adicione NENHUMA explicação antes ou depois do bloco de código.
        """
        self.log.info(f"Enviando prompt para conteúdo de {filename}...")
        self.context_manager.add_log_entry("llm_prompt", f"Prompt para {filename}.", 
                                           {"prompt": app_py_prompt, "model": settings.MODEL_EXECUTOR})

        try:
            app_py_response = self.executor_llm.generate_response(prompt=app_py_prompt, temperature=0.3, max_tokens=2000)
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM (executor) para conteúdo de {filename}: {e}", exc_info=True)
            self.context_manager.add_log_entry("llm_error", f"Erro ao gerar {filename}: {e}")
            app_py_response = None

        if app_py_response:
            self.log.debug(f"Resposta bruta para {filename}:\n{app_py_response[:300]}...") # Log truncado
            code_block = extract_first_code_block(app_py_response)
            if code_block:
                self.log.info(f"Bloco de código Python extraído para {filename}.")
                try:
                    self.context_manager.save_file(filename, code_block)
                    self.context_manager.add_log_entry("llm_generated_code", f"Conteúdo gerado e salvo em {filename}.")
                except Exception as e:
                     self.log.error(f"Falha ao salvar {filename} via ContextManager: {e}", exc_info=True)
            else:
                self.log.warning(f"Nenhum bloco de código Python encontrado na resposta para {filename}. Resposta bruta (início):\n{app_py_response[:500]}")
                self.context_manager.add_log_entry("llm_response_warning", f"Conteúdo bruto (sem bloco Py) para {filename}.", {"raw_response_start": app_py_response[:500]})
                # Tenta salvar a resposta bruta se não encontrou bloco de código, pode ser útil para debug
                try:
                    self.context_manager.save_file(f"{filename}.raw_response.txt", app_py_response)
                except Exception as e:
                    self.log.error(f"Falha ao salvar resposta bruta de {filename}: {e}", exc_info=True)

        else:
            self.log.error(f"Nenhuma resposta recebida do LLM (executor) para o conteúdo de {filename}.")
            self.context_manager.add_log_entry("llm_error", f"Nenhuma resposta para {filename}.")

