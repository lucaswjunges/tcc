import json
from typing import Optional, Dict, Any, List, Union

import httpx
from loguru import logger # Já estava usando Loguru

try:
    from evolux_engine.schemas.contracts import LLMProvider
except ImportError:
    from enum import Enum
    class LLMProvider(Enum):
        OPENAI = "openai"
        OPENROUTER = "openrouter"
        # Adicione outros conforme necessário

class LLMClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        provider: Union[str, LLMProvider] = LLMProvider.OPENROUTER,
        api_base_url: Optional[str] = None,
        timeout: int = 90,
        http_referer: Optional[str] = None,
        x_title: Optional[str] = None,
    ):
        if not api_key:
            # logger.error(...) # Loguru não precisa de string formatada antes
            logger.error("LLMClient: API key não fornecida na inicialização.")
            raise ValueError("API key é obrigatória para LLMClient.")
        if not model_name:
            logger.error("LLMClient: Nome do modelo não fornecido na inicialização.")
            raise ValueError("Nome do modelo é obrigatório para LLMClient.")

        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout

        if isinstance(provider, str):
            try:
                self.provider = LLMProvider[provider.upper()]
            except KeyError:
                logger.warning(f"Provedor LLM desconhecido: '{provider}'. Usando OpenRouter por padrão.")
                self.provider = LLMProvider.OPENROUTER
        else:
            self.provider = provider
        
        self.base_url = api_base_url or self._get_default_base_url()
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == LLMProvider.OPENROUTER:
            if http_referer: self.headers["HTTP-Referer"] = http_referer
            if x_title: self.headers["X-Title"] = x_title
        
        self._async_client: Optional[httpx.AsyncClient] = None
        # Loguru formata automaticamente os kwargs
        logger.info(
            "LLMClient inicializado.", 
            provider=self.provider.value, 
            default_model=self.model_name,
            base_url=self.base_url
        )

    def _get_default_base_url(self) -> str:
        if self.provider == LLMProvider.OPENAI: return "https://api.openai.com/v1"
        elif self.provider == LLMProvider.OPENROUTER: return "https://openrouter.ai/api/v1"
        logger.warning(f"URL base não especificada para provedor '{self.provider.value}'. Usando URL do OpenRouter.")
        return "https://openrouter.ai/api/v1"

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout)
        return self._async_client

    async def close(self):
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None
            # Adicionar contexto se o logger for capturado por outros handlers
            logger.info(f"LLMClient HTTPX client para modelo '{self.model_name}' fechado.")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_override: Optional[str] = None,
        max_tokens: int = 3800,
        temperature: float = 0.7,
    ) -> Optional[str]:
        model_to_use = model_override or self.model_name
        endpoint_url = f"{self.base_url}/chat/completions"

        payload = {"model": model_to_use, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        
        last_message_content = messages[-1]['content']
        log_message_preview = (last_message_content[:150] + '...') if len(last_message_content) > 150 else last_message_content

        logger.debug(
            "Enviando requisição para LLM.", 
            model=model_to_use, 
            url=endpoint_url, 
            # payload_preview=str(payload)[:200] + "...", # Cuidado com dados sensíveis no payload
            last_message_preview=log_message_preview
        )

        try:
            client = await self._get_async_client()
            response = await client.post(endpoint_url, json=payload)
            response.raise_for_status()
            result_json = response.json()
            
            if result_json.get('choices') and \
               isinstance(result_json['choices'], list) and \
               len(result_json['choices']) > 0 and \
               result_json['choices'][0].get('message') and \
               result_json['choices'][0]['message'].get('content'):
                content = result_json['choices'][0]['message']['content']
                usage = result_json.get('usage', {})
                content_preview = (content[:150] + '...') if len(content) > 150 else content
                logger.debug(
                    "Resposta recebida do LLM.", 
                    model=model_to_use,
                    prompt_tokens=usage.get('prompt_tokens', 'N/A'), 
                    completion_tokens=usage.get('completion_tokens', 'N/A'),
                    content_preview=content_preview
                )
                return str(content)
            else:
                logger.error(
                    "Resposta do LLM em formato inesperado.", 
                    model=model_to_use,
                    endpoint=endpoint_url, 
                    response_data=json.dumps(result_json, indent=2) # Logar a resposta completa
                )
                return None
        except httpx.TimeoutException:
            logger.error(
                "Timeout ao chamar API LLM.",
                model=model_to_use,
                url=endpoint_url,
                timeout_seconds=self.timeout
            )
            return None
        except httpx.HTTPStatusError as http_err:
            error_body_str = http_err.response.text # Texto bruto é mais seguro primeiro
            try: # Tenta formatar como JSON se possível
                error_body_json = http_err.response.json()
                error_body_str = json.dumps(error_body_json, indent=2)
            except json.JSONDecodeError: pass # Mantém texto bruto se não for JSON
            logger.error(
                f"Erro HTTP {http_err.response.status_code} ao chamar API LLM.",
                model=model_to_use,
                url=endpoint_url,
                # request_payload=json.dumps(payload, indent=2), # Cuidado com dados sensíveis
                response_body=error_body_str
            )
            return None
        except httpx.RequestError as req_err: # Outros erros de rede, DNS, etc.
            logger.opt(exception=True).error( # opt(exception=True) captura o traceback
                "Erro na requisição ao chamar API LLM.",
                model=model_to_use,
                url=endpoint_url,
                error_details=str(req_err)
            )
            return None
        except Exception as e: # Captura genérica final
            logger.opt(exception=True).error(
                "Erro inesperado ao gerar resposta do LLM.",
                model=model_to_use,
                url=endpoint_url
            )
            return None

    async def list_models(self) -> Optional[List[Dict[str, Any]]]:
        # ... (corpo do método list_models pode permanecer similar, apenas usando logger.)
        if self.provider not in [LLMProvider.OPENROUTER, LLMProvider.OPENAI]:
            logger.warning(f"Listagem de modelos não é implementada de forma padronizada para '{self.provider.value}'.")
        
        endpoint_url = f"{self.base_url}/models"
        logger.info(f"Listando modelos disponíveis de: {endpoint_url}")

        try:
            client = await self._get_async_client()
            response = await client.get(endpoint_url)
            response.raise_for_status()
            models_data = response.json()
            
            if isinstance(models_data.get('data'), list):
                logger.info(f"Modelos listados com sucesso. Total: {len(models_data['data'])}")
                return models_data['data']
            else:
                logger.warning(f"Formato de resposta inesperado ao listar modelos: {json.dumps(models_data, indent=2)}")
                return models_data
        except Exception:
            logger.opt(exception=True).error(f"Falha ao listar modelos de {endpoint_url}")
            return None

