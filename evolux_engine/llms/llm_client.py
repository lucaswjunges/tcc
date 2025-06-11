import json
from typing import Optional, Dict, Any, List, Union

import httpx # Para chamadas HTTP assíncronas
from loguru import logger # Usar logger diretamente em vez de utils.log

from evolux_engine.schemas.contracts import LLMProvider # Para tipar o provedor


class LLMClient:
    """
    Cliente assíncrono para interagir com APIs de LLM,
    atualmente focado em OpenRouter e compatível com a API OpenAI.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        provider: Union[str, LLMProvider] = LLMProvider.OPENROUTER, # Default para OpenRouter
        api_base_url: Optional[str] = None, # Para provedores self-hosted ou diferentes
        timeout: int = 90, # Timeout padrão em segundos
        http_referer: Optional[str] = None, # Recomendado pelo OpenRouter
        x_title: Optional[str] = None, # Recomendado pelo OpenRouter
    ):
        if not api_key:
            logger.error("LLMClient: API key não fornecida na inicialização.")
            raise ValueError("API key é obrigatória para LLMClient.")
        if not model_name:
            logger.error("LLMClient: Nome do modelo não fornecido na inicialização.")
            raise ValueError("Nome do modelo é obrigatório para LLMClient.")

        self.api_key = api_key
        self.model_name = model_name # Modelo padrão para este cliente
        self.timeout = timeout

        if isinstance(provider, str):
            try:
                self.provider = LLMProvider[provider.upper()]
            except KeyError:
                logger.warning(f"Provedor LLM desconhecido: '{provider}'. Usando genérico/OpenRouter.")
                self.provider = LLMProvider.OPENROUTER # Ou um tipo genérico
        else:
            self.provider = provider
        
        self.base_url = api_base_url or self._get_default_base_url()
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == LLMProvider.OPENROUTER:
            # OpenRouter recomenda estes headers para identificação e prevenção de abuso
            if http_referer: # Ex: "https://meuprojeto.com" ou "http://localhost:3000"
                self.headers["HTTP-Referer"] = http_referer
            if x_title: # Ex: "Evolux Engine (Desenvolvimento)"
                self.headers["X-Title"] = x_title
        
        self._async_client: Optional[httpx.AsyncClient] = None
        logger.info(f"LLMClient inicializado para provedor '{self.provider.value}' com modelo padrão '{self.model_name}'.")

    def _get_default_base_url(self) -> str:
        """Retorna a URL base padrão com base no provedor."""
        if self.provider == LLMProvider.OPENAI:
            return "https://api.openai.com/v1"
        elif self.provider == LLMProvider.OPENROUTER:
            return "https://openrouter.ai/api/v1"
        # Adicionar outros provedores aqui
        # elif self.provider == LLMProvider.ANTHROPIC:
        #     return "https://api.anthropic.com/v1" # Verificar URL exata
        else: # Fallback para OpenRouter se url não fornecida e provedor desconhecido/genérico
            logger.warning(f"URL base não especificada para provedor '{self.provider.value}'. Usando URL do OpenRouter como padrão.")
            return "https://openrouter.ai/api/v1"

    async def _get_async_client(self) -> httpx.AsyncClient:
        """Retorna uma instância do AsyncClient, criando-a se necessário."""
        if self._async_client is None or self._async_client.is_closed:
            # Você pode configurar proxies, limites, etc. aqui se necessário
            self._async_client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self._async_client

    async def close(self):
        """Fecha o cliente HTTP assíncrono se estiver aberto."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None
            logger.info("LLMClient HTTPX client fechado.")


    async def generate_response(
        self,
        messages: List[Dict[str, str]], # Lista de mensagens no formato OpenAI
        model_override: Optional[str] = None,
        max_tokens: int = 2048, # Aumentado o padrão para tarefas comuns
        temperature: float = 0.7,
        # top_p: Optional[float] = None, # Outros parâmetros comuns
        # stream: bool = False, # Streaming pode ser implementado no futuro
    ) -> Optional[str]:
        """
        Gera uma resposta de um modelo LLM usando o endpoint de chat/completions.

        Args:
            messages: Uma lista de mensagens, onde cada mensagem é um dict com "role" e "content".
                      Ex: [{"role": "user", "content": "Olá mundo!"}]
            model_override: Permite usar um modelo diferente do padrão deste cliente.
            max_tokens: Número máximo de tokens a serem gerados.
            temperature: Aleatoriedade da saída.
            
        Returns:
            O conteúdo da mensagem gerada pelo LLM, ou None em caso de falha.
        """
        model_to_use = model_override or self.model_name
        endpoint_url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model_to_use,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            # if top_p is not None: payload["top_p"] = top_p
            # "stream": stream, # Se implementar streaming
        }

        logger.debug(f"Enviando requisição para LLM: Modelo='{model_to_use}', URL='{endpoint_url}', Última Msg='{messages[-1]['content'][:100]}...'")

        try:
            client = await self._get_async_client()
            response = await client.post(endpoint_url, json=payload)
            response.raise_for_status()  # Levanta HTTPStatusError para respostas 4xx/5xx
            
            result_json = response.json()
            
            if result_json.get('choices') and \
               isinstance(result_json['choices'], list) and \
               len(result_json['choices']) > 0 and \
               result_json['choices'][0].get('message') and \
               result_json['choices'][0]['message'].get('content'):
                
                content = result_json['choices'][0]['message']['content']
                # Registrar métricas (exemplos, podem ser mais detalhados)
                usage = result_json.get('usage', {})
                logger.debug(
                    f"Resposta recebida do LLM ('{model_to_use}'). "
                    f"Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}, "
                    f"Completion Tokens: {usage.get('completion_tokens', 'N/A')}, "
                    f"Conteúdo (início): {content[:100]}..."
                )
                return str(content) # Garantir que é string
            else:
                logger.error(
                    f"Resposta do LLM ('{model_to_use}') em formato inesperado. "
                    f"Endpoint: {endpoint_url}, Resposta: {result_json}"
                )
                return None # Ou levantar um erro específico
                
        except httpx.TimeoutException:
            logger.error(f"Timeout ao chamar API LLM. Modelo: {model_to_use}, URL: {endpoint_url}")
            return None
        except httpx.HTTPStatusError as http_err:
            error_body_str = "N/A"
            try:
                # Tentar decodificar como JSON se possível, senão texto bruto
                error_body_json = http_err.response.json()
                error_body_str = json.dumps(error_body_json, indent=2)
            except json.JSONDecodeError:
                error_body_str = http_err.response.text

            logger.error(
                f"Erro HTTP {http_err.response.status_code} ao chamar API LLM. "
                f"Modelo: {model_to_use}, URL: {endpoint_url}, "
                f"Corpo da Resposta:\n{error_body_str}"
            )
            return None
        except httpx.RequestError as req_err: # Outros erros de requisição (ex: rede)
            logger.error(
                f"Erro na requisição ao chamar API LLM (não timeout/HTTPStatus). "
                f"Modelo: {model_to_use}, URL: {endpoint_url}, Erro: {req_err}"
            )
            return None
        except Exception as e:
            logger.opt(exception=True).error(
                f"Erro inesperado ao gerar resposta do LLM. "
                f"Modelo: {model_to_use}, URL: {endpoint_url}"
            )
            return None

    async def list_models(self) -> Optional[List[Dict[str, Any]]]:
        """Lista os modelos disponíveis do provedor (se suportado pela API)."""
        if self.provider not in [LLMProvider.OPENROUTER, LLMProvider.OPENAI]:
            logger.warning(f"Listagem de modelos não é implementada de forma genérica para o provedor '{self.provider.value}'. Tentando endpoint padrão.")
        
        endpoint_url = f"{self.base_url}/models"
        logger.info(f"Listando modelos disponíveis de: {endpoint_url}")

        try:
            client = await self._get_async_client()
            response = await client.get(endpoint_url)
            response.raise_for_status()
            models_data = response.json()
            
            # A estrutura da resposta pode variar entre provedores
            # Para OpenAI e OpenRouter, 'data' é uma lista de objetos de modelo
            if isinstance(models_data.get('data'), list):
                logger.info(f"Modelos listados com sucesso. Total: {len(models_data['data'])}")
                return models_data['data']
            else:
                logger.warning(f"Formato de resposta inesperado ao listar modelos. Resposta: {models_data}")
                return None # Ou retornar models_data diretamente se a estrutura for diferente

        except httpx.TimeoutException:
            logger.error("Timeout ao listar modelos da LLM API.")
            return None
        except httpx.HTTPStatusError as http_err:
            logger.error(f"Erro HTTP {http_err.response.status_code} ao listar modelos. Corpo: {http_err.response.text}")
            return None
        except Exception as e:
            logger.opt(exception=True).error("Erro inesperado ao listar modelos.")
            return None

# --- Exemplo de como usar e fechar o cliente ---
# async def example_usage():
#     api_key = os.getenv("OPENROUTER_API_KEY")
#     if not api_key:
#         print("Chave OPENROUTER_API_KEY não encontrada nas variáveis de ambiente.")
#         return

#     client = LLMClient(
#         api_key=api_key,
#         model_name="mistralai/mistral-7b-instruct", # Um modelo conhecido no OpenRouter
#         provider=LLMProvider.OPENROUTER,
#         http_referer="http://localhost", # Exemplo
#         x_title="Evolux Test" # Exemplo
#     )
    
#     try:
#         # Listar modelos
#         models = await client.list_models()
#         if models:
#             print(f"Primeiros 5 modelos encontrados: {models[:5]}")

#         # Gerar resposta
#         messages = [{"role": "user", "content": "Qual a capital da França?"}]
#         response_content = await client.generate_response(messages, max_tokens=50)
        
#         if response_content:
#             print(f"\nResposta do LLM: {response_content}")
#         else:
#             print("\nNão foi possível obter resposta do LLM.")
            
#     finally:
#         await client.close() # Importante fechar o cliente ao final

# if __name__ == "__main__":
#     import asyncio
#     import os
#     from dotenv import load_dotenv
#     load_dotenv()
#     asyncio.run(example_usage())
