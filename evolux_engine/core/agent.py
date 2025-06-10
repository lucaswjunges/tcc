import os
from typing import Optional

from evolux_engine.utils.logging_utils import log
from evolux_engine.utils.env_vars import settings
from evolux_engine.llms.llm_factory import LLMFactory
from evolux_engine.core.context_manager import ContextManager
from evolux_engine.utils.string_utils import extract_first_code_block

class Agent:
    def __init__(self, goal: str, context_manager: ContextManager, llm_provider_override: Optional[str] = None):
        self.log = log.bind(agent_id=context_manager.project_id, goal=goal) # Bind para logs específicos do agente
        self.goal = goal
        self.context_manager = context_manager
        # self.project_id e self.project_dir já estão no context_manager
        self.log.info("Inicializando Agente...")

        # Determinar provedor LLM e chave de API
        self.llm_provider = llm_provider_override or settings.LLM_PROVIDER
        
        self.api_key = None
        if self.llm_provider == "openai":
            self.api_key = settings.OPENAI_API_KEY
        elif self.llm_provider == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
        
        if not self.api_key:
            self.log.error(f"API key para {self.llm_provider} não configurada. LLM não será funcional.")
            self.llm_client = None
        else:
            try:
                llm_factory = LLMFactory(api_key=self.api_key)
                # Para planejamento, usamos MODEL_PLANNER, para execução/geração de código, MODEL_EXECUTOR
                # Vamos instanciar um cliente padrão aqui com MODEL_EXECUTOR
                # e podemos obter outro para MODEL_PLANNER se necessário
                self.llm_client = llm_factory.get_llm_client(
                    provider=self.llm_provider, 
                    model=settings.MODEL_EXECUTOR # Modelo para tarefas de execução
                )
                self.log.info(f"LLM client (executor) criado para {self.llm_provider} com modelo {settings.MODEL_EXECUTOR}.")
            except Exception as e:
                self.log.error(f"Falha ao criar LLM client: {e}", exc_info=True)
                self.llm_client = None

        self.log.info(f"Agente inicializado. Provedor LLM: {self.llm_provider if self.llm_client else 'Nenhum (Indisponível)'}")

    def run(self):
        self.log.info("Iniciando execução do agente.")
        self.context_manager.add_log_entry("agent_status", "Iniciando execução do Agente.", {"goal": self.goal})

        if not self.llm_client:
            self.log.error("LLM client não está disponível. Não é possível prosseguir com tarefas que dependem de LLM.")
            self.context_manager.add_log_entry("agent_error", "LLM client indisponível. Encerrando.")
            return

        # 1. Gerar estrutura do projeto
        self._generate_and_create_project_structure()

        # 2. Gerar conteúdo do arquivo principal (ex: app.py)
        self._generate_and_save_main_app_file()

        self.log.info("Execução do agente concluída.")
        self.context_manager.add_log_entry("agent_status", "Execução do Agente concluída.")

    def _get_planner_llm_client(self):
        """Retorna um cliente LLM configurado com o MODEL_PLANNER."""
        if not self.api_key: return None
        try:
            llm_factory = LLMFactory(api_key=self.api_key)
            return llm_factory.get_llm_client(provider=self.llm_provider, model=settings.MODEL_PLANNER)
        except Exception as e:
            self.log.error(f"Falha ao criar LLM client (planner): {e}", exc_info=True)
            return None
            
    def _generate_and_create_project_structure(self):
        self.log.info("Iniciando geração da estrutura do projeto.")
        planner_llm = self._get_planner_llm_client()
        if not planner_llm:
            self.log.error("LLM Planner indisponível, não é possível gerar estrutura do projeto.")
            self.context_manager.add_log_entry("agent_error", "LLM Planner indisponível para gerar estrutura.")
            return

        structure_prompt = f"""
        Baseado no objetivo: "{self.goal}", crie uma estrutura básica e simples de arquivos e diretórios para este projeto.
        Liste os arquivos e diretórios, um por linha.
        Para diretórios, termine o nome com uma barra '/'.
        Exemplo de resposta para um app Flask simples:
        app.py
        templates/
        templates/index.html
        static/
        static/style.css
        requirements.txt

        Se o projeto for muito simples e precisar apenas de um arquivo, liste apenas esse arquivo.
        Responda APENAS com a lista de arquivos/diretórios. Não adicione explicações.
        """
        self.log.info("Enviando prompt para estrutura do projeto...")
        self.context_manager.add_log_entry("llm_prompt", "Prompt para estrutura do projeto.", {"prompt": structure_prompt})
        
        try:
            structure_response = planner_llm.generate_response(prompt=structure_prompt, temperature=0.2, max_tokens=500)
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM para estrutura do projeto: {e}", exc_info=True)
            self.context_manager.add_log_entry("llm_error", f"Erro ao gerar estrutura: {e}")
            structure_response = None

        if structure_response:
            self.log.info(f"Resposta da estrutura recebida:\n{structure_response}")
            self.context_manager.add_log_entry("llm_response", "Resposta da estrutura do projeto.", {"response": structure_response})
            self._create_project_structure_from_text(structure_response)
        else:
            self.log.error("Nenhuma resposta recebida do LLM para a estrutura do projeto.")
            self.context_manager.add_log_entry("llm_error", "Nenhuma resposta para estrutura do projeto.")

    def _create_project_structure_from_text(self, structure_text: str):
        self.log.info(f"Criando estrutura do projeto em: {self.context_manager.project_dir}")
        lines = structure_text.strip().split('\n')
        for line in lines:
            path_item = line.strip()
            if not path_item or path_item.startswith("#") or "```" in path_item:
                continue
            
            try:
                if path_item.endswith('/'):
                    self.context_manager.create_directory(path_item)
                else:
                    # Cria arquivo vazio, conteúdo será gerado depois se necessário
                    self.context_manager.save_file(path_item, "") # Salva arquivo vazio
            except Exception as e:
                # ContextManager já loga o erro, mas podemos logar aqui também se quisermos adicionar contexto do Agent
                self.log.error(f"Falha ao processar item da estrutura '{path_item}': {e}", exc_info=False) # exc_info=False para não duplicar tracebacks

    def _generate_and_save_main_app_file(self, filename: str = "app.py"):
        self.log.info(f"Iniciando geração do conteúdo para {filename}.")
        if not self.llm_client: # Usar o executor LLM aqui
            self.log.error(f"LLM Executor indisponível, não é possível gerar {filename}.")
            self.context_manager.add_log_entry("agent_error", f"LLM Executor indisponível para gerar {filename}.")
            return

        app_py_prompt = f"""
        Crie o conteúdo para o arquivo `{filename}` de uma aplicação web (provavelmente Flask ou similar, dependendo do objetivo)
        que atinge o seguinte objetivo: "{self.goal}".
        O código deve ser um bloco de código Python completo e funcional, pronto para ser executado.
        Se o objetivo envolve o horário atual, use o módulo datetime do Python e formate o horário de forma amigável.
        A aplicação Flask deve rodar em host='0.0.0.0' e port=5000 por padrão, se aplicável.
        Inclua todas as importações necessárias (ex: Flask, datetime).
        Responda APENAS com o bloco de código Python. Não inclua explicações antes ou depois do bloco de código.
        Exemplo de formato de resposta:
        ```python
        from flask import Flask
        # ... resto do código ...
        if __name__ == '__main__':
            app.run(host='0.0.0.0', port=5000, debug=True)
        ```
        Adapte o exemplo acima para o objetivo fornecido.
        """
        self.log.info(f"Enviando prompt para conteúdo de {filename}...")
        self.context_manager.add_log_entry("llm_prompt", f"Prompt para {filename}.", {"prompt": app_py_prompt})

        try:
            app_py_response = self.llm_client.generate_response(prompt=app_py_prompt, temperature=0.5, max_tokens=1500)
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM para conteúdo de {filename}: {e}", exc_info=True)
            self.context_manager.add_log_entry("llm_error", f"Erro ao gerar {filename}: {e}")
            app_py_response = None

        if app_py_response:
            self.log.debug(f"Resposta bruta para {filename}:\n{app_py_response}")
            code_block = extract_first_code_block(app_py_response)
            if code_block:
                self.log.info(f"Bloco de código extraído para {filename}.")
                try:
                    self.context_manager.save_file(filename, code_block)
                    self.context_manager.add_log_entry("llm_generated_code", f"Conteúdo gerado e salvo em {filename}.")
                except Exception as e:
                     self.log.error(f"Falha ao salvar {filename} via ContextManager: {e}", exc_info=True)
            else:
                self.log.warning(f"Nenhum bloco de código Python encontrado na resposta para {filename}. Resposta bruta:\n{app_py_response}")
                self.context_manager.add_log_entry("llm_response_warning", f"Conteúdo bruto (sem bloco Python) para {filename}.", {"raw_response": app_py_response})
        else:
            self.log.error(f"Nenhuma resposta recebida do LLM para o conteúdo de {filename}.")
            self.context_manager.add_log_entry("llm_error", f"Nenhuma resposta para {filename}.")
