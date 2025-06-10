# evolux-engine/core/agent.py
import logging # Adicionar import logging
import os
from typing import Optional
from evolux_engine.models.project_context import ProjectContext


from evolux_engine.core.context_manager import ContextManager
from evolux_engine.llms.llm_factory import LLMFactory
from evolux_engine.utils.env_vars import EVOLUX_LLM_PROVIDER, EVOLUX_OPENROUTER_API_KEY, OPENAI_API_KEY
from evolux_engine.utils.string_utils import extract_first_code_block

class Agent:
    def __init__(self, goal: str, context_manager: ContextManager, llm_provider: Optional[str] = None):
        self.log = logging.getLogger(__name__) # <<---- ADICIONADO: Inicializar logger para a instância
        self.goal = goal
        self.context_manager = context_manager
        self.project_id = context_manager.project_id
        self.project_dir = context_manager.project_dir

        # Determine LLM provider and API key
        selected_provider = llm_provider or EVOLUX_LLM_PROVIDER or "openai" # Default to openai if nothing else is set
        api_key = None
        if selected_provider == "openai":
            api_key = OPENAI_API_KEY
        elif selected_provider == "openrouter":
            api_key = EVOLUX_OPENROUTER_API_KEY

        if not api_key:
            self.log.warning(f"API key for {selected_provider} not found. LLM functionality will be limited.")
            self.llm_client = None
        else:
            self.llm_client = LLMFactory.create_llm(provider=selected_provider, api_key=api_key)

        self.log.info(f"Agent initialized for project: {self.project_id} with goal: '{self.goal}' using LLM provider: {selected_provider}") # <<---- ADICIONADO: Log de inicialização

    def run(self):
        self.log.info(f"Starting agent for goal: {self.goal}") # <<---- CORRIGIDO: Usar self.log

        if not self.llm_client:
            self.log.error("LLM client not initialized. Cannot proceed with agent run.")
            return

        # Create a simple Flask app structure
        app_structure_prompt = f"""
        Baseado no objetivo: "{self.goal}", crie a estrutura básica de arquivos e diretórios para um projeto Flask.
        Liste os arquivos e diretórios no seguinte formato:
        diretorio/
        diretorio/arquivo.py
        outro_diretorio/
        """
        self.log.info("Generating project structure...")
        structure_response = self.llm_client.get_completion(app_structure_prompt)

        if structure_response:
            self.log.info(f"Raw structure response: {structure_response}")
            # TODO: Parsear a resposta para criar os diretórios e arquivos
            # Por enquanto apenas logamos
            self.context_manager.add_log_entry("system", f"Estrutura do projeto sugerida: \n{structure_response}")
            self._create_project_structure(structure_response)
        else:
            self.log.error("Failed to get project structure from LLM.")
            self.context_manager.add_log_entry("system", "Falha ao obter estrutura do projeto do LLM.")
            return

        # Create app.py content
        app_py_prompt = f"""
        Crie o conteúdo para o arquivo principal `app.py` de uma aplicação Flask que atinge o seguinte objetivo:
        "{self.goal}".
        O código deve ser um bloco de código Python completo e funcional.
        Certifique-se de que ele é um aplicativo Flask simples, mas executável.
        Se o objetivo envolve o horário atual, use o módulo datetime do Python.
        Responda APENAS com o bloco de código Python.
        """
        self.log.info("Generating app.py content...")
        app_py_response = self.llm_client.get_completion(app_py_prompt)

        if app_py_response:
            self.log.info("app.py content generated.")
            code_block = extract_first_code_block(app_py_response)
            if code_block:
                self._save_file("app.py", code_block) # Assumindo que app.py está na raiz do projeto_dir
                self.context_manager.add_log_entry("system", f"Conteúdo gerado para app.py:\n{code_block}")
            else:
                self.log.warning("No code block found in app.py response. Saving raw response.")
                self._save_file("app.py", app_py_response)
                self.context_manager.add_log_entry("system", f"Conteúdo bruto (sem bloco de código encontrado) para app.py:\n{app_py_response}")

        else:
            self.log.error("Failed to get app.py content from LLM.")
            self.context_manager.add_log_entry("system", "Falha ao obter conteúdo para app.py do LLM.")

        self.log.info(f"Agent finished processing for goal: {self.goal}")

    def _create_project_structure(self, structure_text: str):
        """
        Cria os diretórios e arquivos vazios baseados no texto da estrutura.
        Espera linhas como:
        diretorio/
        diretorio/arquivo.py
        """
        self.log.info(f"Creating project structure in {self.project_dir}")
        for line in structure_text.strip().split('\n'):
            path_item = line.strip()
            if not path_item:
                continue

            full_path = os.path.join(self.project_dir, path_item)

            if path_item.endswith('/'): # É um diretório
                try:
                    os.makedirs(full_path, exist_ok=True)
                    self.log.info(f"Created directory: {full_path}")
                except OSError as e:
                    self.log.error(f"Failed to create directory {full_path}: {e}")
            else: # É um arquivo
                try:
                    # Garante que o diretório pai exista
                    parent_dir = os.path.dirname(full_path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)
                        self.log.info(f"Created parent directory: {parent_dir}")

                    with open(full_path, 'w') as f:
                        # Criando arquivo vazio por enquanto, conteúdo será gerado depois se necessário
                        pass
                    self.log.info(f"Created empty file: {full_path}")
                except OSError as e:
                    self.log.error(f"Failed to create file {full_path}: {e}")

    def _save_file(self, file_path: str, content: str):
        full_path = os.path.join(self.project_dir, file_path)
        try:
            # Garante que o diretório pai exista
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                self.log.info(f"Created parent directory for saving file: {parent_dir}")

            with open(full_path, 'w') as f:
                f.write(content)
            self.log.info(f"Saved file: {full_path}")
        except IOError as e:
            self.log.error(f"Failed to save file {full_path}: {e}")
