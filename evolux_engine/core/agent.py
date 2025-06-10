# Conteúdo CORRIGIDO para: evolux_engine/core/agent.py
import logging
import os
from typing import Optional

# Imports de dentro do pacote evolux_engine
from evolux_engine.models.project_context import ProjectContext # Presumo que este arquivo exista e esteja correto
from evolux_engine.core.context_manager import ContextManager # Presumo que este arquivo exista e esteja correto
from evolux_engine.llms.llm_factory import LLMFactory
from evolux_engine.utils.env_vars import settings # <--- CORREÇÃO PRINCIPAL: Importa a instância 'settings'
from evolux_engine.utils.string_utils import extract_first_code_block # Presumo que este arquivo exista e esteja correto
# Remover o import de logging_utils.log se estiver usando logging.getLogger() localmente
# from evolux_engine.utils.logging_utils import log as global_evolux_log # Se quiser usar o logger global configurado

class Agent:
    def __init__(self, goal: str, context_manager: ContextManager, llm_provider_override: Optional[str] = None):
        # Usar o logger padrão do Python configurado para este módulo
        self.log = logging.getLogger(__name__)
        # Ou, se preferir usar o logger configurado pelo structlog em logging_utils:
        # from evolux_engine.utils.logging_utils import log as global_evolux_log
        # self.log = global_evolux_log.bind(agent_id=context_manager.project_id) # Exemplo de bind

        self.goal = goal
        self.context_manager = context_manager
        self.project_id = context_manager.project_id
        self.project_dir = context_manager.project_dir

        # Determinar provedor LLM e chave de API usando a instância 'settings'
        # O 'llm_provider_override' tem prioridade, depois o das settings, depois um default.
        selected_provider = llm_provider_override or settings.LLM_PROVIDER or "openai"
        
        api_key = None
        if selected_provider == "openai":
            api_key = settings.OPENAI_API_KEY
        elif selected_provider == "openrouter":
            api_key = settings.OPENROUTER_API_KEY
        else:
            self.log.error(f"Provedor LLM não suportado: {selected_provider}. Verifique as configurações.")
            # Não continue se o provedor não for reconhecido.
            raise ValueError(f"Provedor LLM não suportado: {selected_provider}")

        if not api_key:
            self.log.warning(f"API key para {selected_provider} não encontrada. LLM functionality will be limited/unavailable.")
            self.llm_client = None # LLM não pode ser usado
        else:
            # Supondo que LLMFactory foi ajustada para ter um método create_llm estático ou
            # que você instância a factory e depois obtém o cliente.
            # A versão anterior da factory necessitava ser instanciada primeiro:
            try:
                llm_factory_instance = LLMFactory(api_key=api_key)
                # O modelo específico deve ser passado para get_llm_client
                # Usaremos MODEL_EXECUTOR das settings como padrão aqui, mas pode variar por tarefa.
                self.llm_client = llm_factory_instance.get_llm_client(model=settings.MODEL_EXECUTOR)
                self.log.info(f"LLM client criado com sucesso para {selected_provider} e modelo {settings.MODEL_EXECUTOR}.")
            except Exception as e:
                self.log.error(f"Falha ao criar LLM client para {selected_provider}: {e}", exc_info=True)
                self.llm_client = None


        self.log.info(f"Agent initialized for project: {self.project_id} with goal: '{self.goal}' using LLM provider: {selected_provider if self.llm_client else 'None (LLM indisponível)'}")

    def run(self):
        self.log.info(f"Starting agent for goal: {self.goal}")

        if not self.llm_client:
            self.log.error("LLM client não inicializado ou falhou na inicialização. Não é possível continuar com a execução do agente que depende de LLM.")
            self.context_manager.add_log_entry("system", "CRÍTICO: LLM client não pôde ser inicializado. Verifique as configurações de API e provedor.")
            return

        # Criar uma estrutura de aplicativo Flask simples
        # Nota: Se o seu objetivo é "Criar um website em Flask que mostra o horário atual",
        # a estrutura pode ser bem simples, talvez apenas um app.py e um diretório templates/.
        app_structure_prompt = f"""
        Baseado no objetivo: "{self.goal}", crie a estrutura básica de arquivos e diretórios para um projeto Flask.
        Considere que o projeto é simples. Se for apenas um arquivo, liste apenas o arquivo.
        Exemplos de resposta:
        app.py
        templates/
        templates/index.html

        OU se mais complexo:
        meu_app/
        meu_app/__init__.py
        meu_app/routes.py
        meu_app/models.py
        meu_app/templates/
        meu_app/templates/index.html
        run.py
        requirements.txt

        Responda com a lista de arquivos e diretórios, um por linha.
        """
        self.log.info("Gerando estrutura do projeto...")
        try:
            # Usar o MODEL_PLANNER para este tipo de tarefa pode ser mais apropriado
            structure_response = self.llm_client.generate_response(prompt=app_structure_prompt, temperature=0.3) # Usar temperature mais baixa para tarefas estruturais
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM para estrutura do projeto: {e}", exc_info=True)
            structure_response = None # Garantir que structure_response seja None em caso de falha

        if structure_response:
            self.log.info(f"Resposta bruta da estrutura: \n{structure_response}")
            self.context_manager.add_log_entry("llm_response", f"Estrutura do projeto sugerida: \n{structure_response}")
            self._create_project_structure(structure_response)
        else:
            self.log.error("Falha ao obter estrutura do projeto do LLM ou resposta vazia.")
            self.context_manager.add_log_entry("system_error", "Falha ao obter estrutura do projeto do LLM.")
            # Decidir se deve parar ou continuar com uma estrutura padrão
            # return # Descomentar para parar se a estrutura for crucial

        # Criar conteúdo de app.py
        app_py_prompt = f"""
        Crie o conteúdo para o arquivo principal `app.py` de uma aplicação Flask que atinge o seguinte objetivo:
        "{self.goal}".
        O código deve ser um bloco de código Python completo e funcional, pronto para ser executado.
        Se o objetivo envolve o horário atual, use o módulo datetime do Python e formate o horário de forma amigável.
        A aplicação deve rodar em host='0.0.0.0' e port=5000.
        Inclua importações necessárias como Flask, datetime.
        Responda APENAS com o bloco de código Python. Não inclua explicações antes ou depois do bloco de código.
        Exemplo de um aplicativo Flask simples:
        ```python
        from flask import Flask
        app = Flask(__name__)

        @app.route('/')
        def hello_world():
            return 'Hello, World!'

        if __name__ == '__main__':
            app.run(host='0.0.0.0', port=5000, debug=True)
        ```
        Adapte o exemplo acima para o objetivo fornecido.
        """
        self.log.info("Gerando conteúdo de app.py...")
        try:
            app_py_response = self.llm_client.generate_response(prompt=app_py_prompt, temperature=0.5)
        except Exception as e:
            self.log.error(f"Erro ao chamar LLM para conteúdo de app.py: {e}", exc_info=True)
            app_py_response = None

        if app_py_response:
            self.log.debug(f"Resposta bruta para app.py: \n{app_py_response}") # Logar como debug pode ser melhor para respostas longas
            code_block = extract_first_code_block(app_py_response)
            if code_block:
                self.log.info("Bloco de código extraído para app.py.")
                self._save_file("app.py", code_block) 
                self.context_manager.add_log_entry("llm_generated_code", f"Conteúdo gerado e salvo em app.py:\n{code_block}")
            else:
                self.log.warning("Nenhum bloco de código Python encontrado na resposta para app.py. Salvando resposta bruta.")
                # Decidir se quer salvar a resposta bruta ou não
                # self._save_file("app.py.raw_response", app_py_response) 
                self.context_manager.add_log_entry("llm_response_warning", f"Conteúdo bruto (sem bloco de código Python encontrado) para app.py:\n{app_py_response}")
        else:
            self.log.error("Falha ao obter conteúdo para app.py do LLM ou resposta vazia.")
            self.context_manager.add_log_entry("system_error", "Falha ao obter conteúdo para app.py do LLM.")

        self.log.info(f"Agent finished processing for goal: {self.goal}")

    def _create_project_structure(self, structure_text: str):
        self.log.info(f"Criando estrutura do projeto em: {self.project_dir}")
        if not os.path.exists(self.project_dir):
            try:
                os.makedirs(self.project_dir, exist_ok=True)
                self.log.info(f"Diretório base do projeto criado: {self.project_dir}")
            except OSError as e:
                self.log.error(f"Falha ao criar diretório base do projeto {self.project_dir}: {e}")
                return # Não pode continuar se o diretório base falhar
                
        for line in structure_text.strip().split('\n'):
            path_item = line.strip()
            if not path_item or path_item.startswith("#") or "```" in path_item: # Ignorar comentários ou delimitadores de bloco
                continue

            # Sanitizar o path_item para remover quaisquer prefixos ou sufixos indesejados que a LLM possa adicionar
            # Ex: remover "diretorio/" se a LLM já estiver pensando em termos relativos ao project_dir
            # Isso pode precisar de mais lógica dependendo da saída da LLM
            
            full_path = os.path.join(self.project_dir, path_item)

            try:
                if path_item.endswith('/'): 
                    os.makedirs(full_path, exist_ok=True)
                    self.log.info(f"Diretório criado: {full_path}")
                else: 
                    parent_dir = os.path.dirname(full_path)
                    if parent_dir and not os.path.exists(parent_dir): # Certificar que o diretório pai exista
                        os.makedirs(parent_dir, exist_ok=True)
                        self.log.info(f"Diretório pai criado: {parent_dir}")
                    
                    with open(full_path, 'w', encoding='utf-8') as f: # Especificar encoding
                        pass # Criar arquivo vazio
                    self.log.info(f"Arquivo vazio criado: {full_path}")
            except OSError as e:
                self.log.error(f"Falha ao criar item da estrutura {full_path}: {e}")
            except Exception as e: # Captura geral para outros erros inesperados
                self.log.error(f"Erro inesperado ao criar item da estrutura {full_path}: {e}", exc_info=True)


    def _save_file(self, file_path_relative: str, content: str):
        full_path = os.path.join(self.project_dir, file_path_relative)
        self.log.info(f"Tentando salvar arquivo em: {full_path}")
        try:
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                self.log.info(f"Diretório pai criado para salvar arquivo: {parent_dir}")

            with open(full_path, 'w', encoding='utf-8') as f: # Especificar encoding
                f.write(content)
            self.log.info(f"Arquivo salvo com sucesso: {full_path}")
        except IOError as e:
            self.log.error(f"Falha ao salvar arquivo {full_path}: {e}", exc_info=True)
        except Exception as e: # Captura geral
            self.log.error(f"Erro inesperado ao salvar arquivo {full_path}: {e}", exc_info=True)

