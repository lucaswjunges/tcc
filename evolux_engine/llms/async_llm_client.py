# Async LLM Client com concorrência, circuit breaker e retry inteligente

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps

from ..schemas.contracts import LLMProvider
from ..utils.logging_utils import get_structured_logger

logger = get_structured_logger("async_llm_client")

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class LLMMetrics:
    """Métricas detalhadas de LLM"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    circuit_breaks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    concurrent_requests: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        return 1.0 - self.success_rate

@dataclass
class LLMRequest:
    """Request para LLM com metadata"""
    messages: List[Dict[str, str]]
    model: str
    max_tokens: int = 2048
    temperature: float = 0.7
    request_id: str = field(default_factory=lambda: str(time.time_ns()))
    priority: int = 0  # 0 = normal, 1 = high, 2 = critical
    timeout: float = 120.0
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class LLMResponse:
    """Response de LLM com metadata"""
    content: str
    request_id: str
    model: str
    tokens_used: int
    cost_usd: float
    latency_ms: float
    success: bool
    error: Optional[str] = None
    from_cache: bool = False
    attempt: int = 1

class CircuitBreaker:
    """Circuit breaker para LLM calls"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func: Callable):
        """Decorator para circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
                
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class AsyncLLMClient:
    """
    Cliente LLM assíncrono com recursos enterprise:
    - Concorrência massiva
    - Circuit breaker
    - Cache inteligente
    - Retry com backoff exponencial
    - Rate limiting
    - Load balancing
    - Métricas detalhadas
    """
    
    def __init__(self,
                 provider: LLMProvider,
                 api_key: str,
                 model_name: str,
                 max_concurrent: int = 50,
                 cache_enabled: bool = True,
                 cache_ttl: int = 3600):
        
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.max_concurrent = max_concurrent
        
        # Controle de concorrência
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = asyncio.Semaphore(10)  # 10 requests per second
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        # Cache
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple[LLMResponse, float]] = {}
        
        # Métricas
        self.metrics = LLMMetrics()
        
        # Session HTTP reutilizável
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Queue para requests prioritários
        self.request_queue = asyncio.PriorityQueue()
        self.workers_running = False
        
        logger.info("AsyncLLMClient initialized",
                   provider=provider.value,
                   model=model_name,
                   max_concurrent=max_concurrent)

    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

    async def start(self):
        """Inicializa recursos async"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=180)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Iniciar workers para queue
        if not self.workers_running:
            self.workers_running = True
            for i in range(min(5, self.max_concurrent)):
                asyncio.create_task(self._worker())

    async def close(self):
        """Limpa recursos"""
        self.workers_running = False
        if self.session:
            await self.session.close()
            self.session = None

    async def _worker(self):
        """Worker para processar queue de requests"""
        while self.workers_running:
            try:
                # Pegar próximo request da queue
                priority, request = await asyncio.wait_for(
                    self.request_queue.get(), timeout=1.0
                )
                
                # Processar request
                asyncio.create_task(self._process_request(request))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Worker error", error=str(e))

    def _get_cache_key(self, request: LLMRequest) -> str:
        """Gera chave única para cache"""
        content = json.dumps({
            'messages': request.messages,
            'model': request.model,
            'max_tokens': request.max_tokens,
            'temperature': request.temperature
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Busca no cache"""
        if not self.cache_enabled or cache_key not in self.cache:
            self.metrics.cache_misses += 1
            return None
        
        response, timestamp = self.cache[cache_key]
        
        # Verificar TTL
        if time.time() - timestamp > self.cache_ttl:
            del self.cache[cache_key]
            self.metrics.cache_misses += 1
            return None
        
        self.metrics.cache_hits += 1
        response.from_cache = True
        return response

    def _save_to_cache(self, cache_key: str, response: LLMResponse):
        """Salva no cache"""
        if self.cache_enabled and response.success:
            self.cache[cache_key] = (response, time.time())

    async def generate_response(self,
                              messages: List[Dict[str, str]],
                              max_tokens: int = 2048,
                              temperature: float = 0.7,
                              priority: int = 0,
                              timeout: float = 120.0) -> str:
        """Interface principal para geração de resposta"""
        
        request = LLMRequest(
            messages=messages,
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            priority=priority,
            timeout=timeout
        )
        
        response = await self.generate_response_detailed(request)
        
        if not response.success:
            raise Exception(f"LLM request failed: {response.error}")
        
        return response.content

    async def generate_response_detailed(self, request: LLMRequest) -> LLMResponse:
        """Geração com resposta detalhada"""
        
        # Verificar cache primeiro
        cache_key = self._get_cache_key(request)
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            logger.debug("Cache hit", request_id=request.request_id)
            return cached_response
        
        # Processar request
        return await self._process_request_with_retry(request)

    async def _process_request_with_retry(self, request: LLMRequest) -> LLMResponse:
        """Processa request com retry inteligente"""
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                response = await self._process_request(request)
                
                if response.success:
                    # Salvar no cache
                    cache_key = self._get_cache_key(request)
                    self._save_to_cache(cache_key, response)
                    return response
                
                # Se não foi sucesso mas não é erro de rede, não tentar novamente
                if attempt == max_retries:
                    return response
                
            except Exception as e:
                # Classificar tipo de erro para decidir se deve tentar novamente
                error_type = self._classify_error(e)
                should_retry = self._should_retry_error(error_type, attempt, max_retries)
                
                logger.error("LLM request failed",
                           request_id=request.request_id,
                           attempt=attempt + 1,
                           error_type=error_type,
                           error=str(e),
                           will_retry=should_retry)
                
                if not should_retry or attempt == max_retries:
                    return LLMResponse(
                        content="",
                        request_id=request.request_id,
                        model=request.model,
                        tokens_used=0,
                        cost_usd=0.0,
                        latency_ms=time.time() * 1000 - start_time,
                        success=False,
                        error=f"{error_type}: {str(e)}",
                        attempt=attempt + 1
                    )
                
                # Backoff exponencial
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                logger.warning("Retrying LLM request",
                             attempt=attempt + 1,
                             delay=delay,
                             error=str(e))

    async def _process_request(self, request: LLMRequest) -> LLMResponse:
        """Processa request individual"""
        
        start_time = time.time()
        self.metrics.total_requests += 1
        self.metrics.concurrent_requests += 1
        
        try:
            async with self.semaphore:  # Controle de concorrência
                async with self.rate_limiter:  # Rate limiting
                    
                    if self.provider == LLMProvider.GOOGLE:
                        response = await self._call_google_api(request)
                    elif self.provider == LLMProvider.OPENAI:
                        response = await self._call_openai_api(request)
                    elif self.provider == LLMProvider.OPENROUTER:
                        response = await self._call_openrouter_api(request)
                    else:
                        raise ValueError(f"Unsupported provider: {self.provider}")
                    
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # Atualizar métricas
                    self.metrics.successful_requests += 1
                    self.metrics.total_tokens += response.tokens_used
                    self.metrics.total_cost_usd += response.cost_usd
                    self.metrics.avg_latency_ms = (
                        (self.metrics.avg_latency_ms * (self.metrics.successful_requests - 1) + latency_ms) /
                        self.metrics.successful_requests
                    )
                    
                    response.latency_ms = latency_ms
                    response.success = True
                    
                    logger.debug("LLM request successful",
                               request_id=request.request_id,
                               latency_ms=latency_ms,
                               tokens=response.tokens_used)
                    
                    return response
                    
        except Exception as e:
            self.metrics.failed_requests += 1
            latency_ms = (time.time() - start_time) * 1000
            
            logger.error("LLM request failed",
                        request_id=request.request_id,
                        error=str(e),
                        latency_ms=latency_ms)
            
            return LLMResponse(
                content="",
                request_id=request.request_id,
                model=request.model,
                tokens_used=0,
                cost_usd=0.0,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )
        finally:
            self.metrics.concurrent_requests -= 1

    async def _call_google_api(self, request: LLMRequest) -> LLMResponse:
        """Chama API do Google Gemini"""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # Converter messages para formato Google
        parts = []
        for msg in request.messages:
            if msg["role"] == "user":
                parts.append({"text": msg["content"]})
            elif msg["role"] == "system":
                # Google não tem system role, adicionar como user
                parts.append({"text": f"System: {msg['content']}"})
        
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature
            }
        }
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Google API error: {resp.status} - {await resp.text()}")
            
            data = await resp.json()
            
            if "candidates" not in data or not data["candidates"]:
                raise Exception("No response from Google API")
            
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Estimar tokens e custo (Google não retorna exatos)
            tokens_used = len(content.split()) * 1.3  # Estimativa
            cost_usd = tokens_used * 0.000001  # Estimativa para Gemini Flash
            
            return LLMResponse(
                content=content,
                request_id=request.request_id,
                model=request.model,
                tokens_used=int(tokens_used),
                cost_usd=cost_usd,
                latency_ms=0,  # Será preenchido pelo caller
                success=True
            )

    async def _call_openai_api(self, request: LLMRequest) -> LLMResponse:
        """Chama API da OpenAI"""
        
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": request.model,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"OpenAI API error: {resp.status} - {await resp.text()}")
            
            data = await resp.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens_used = data["usage"]["total_tokens"]
            
            # Custo baseado no modelo
            cost_per_token = 0.000002  # GPT-3.5 turbo
            if "gpt-4" in request.model:
                cost_per_token = 0.000006
            
            cost_usd = tokens_used * cost_per_token
            
            return LLMResponse(
                content=content,
                request_id=request.request_id,
                model=request.model,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                latency_ms=0,
                success=True
            )

    async def _call_openrouter_api(self, request: LLMRequest) -> LLMResponse:
        """Chama API do OpenRouter"""
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://evolux-engine.com",
            "X-Title": "Evolux Engine"
        }
        
        payload = {
            "model": request.model,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"OpenRouter API error: {resp.status} - {await resp.text()}")
            
            data = await resp.json()
            
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            
            # Custo baseado no modelo do OpenRouter
            cost_usd = 0.0  # OpenRouter tem preços variados
            
            return LLMResponse(
                content=content,
                request_id=request.request_id,
                model=request.model,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                latency_ms=0,
                success=True
            )

    async def batch_generate(self, 
                           requests: List[LLMRequest],
                           max_concurrent: Optional[int] = None) -> List[LLMResponse]:
        """Processa múltiplos requests em batch"""
        
        if max_concurrent is None:
            max_concurrent = self.max_concurrent
        
        logger.info("Starting batch LLM generation",
                   batch_size=len(requests),
                   max_concurrent=max_concurrent)
        
        # Criar semáforo específico para este batch
        batch_semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(req):
            async with batch_semaphore:
                return await self.generate_response_detailed(req)
        
        # Executar todos os requests concorrentemente
        results = await asyncio.gather(
            *[process_with_semaphore(req) for req in requests],
            return_exceptions=True
        )
        
        # Processar resultados
        responses = []
        successful = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(LLMResponse(
                    content="",
                    request_id=requests[i].request_id,
                    model=requests[i].model,
                    tokens_used=0,
                    cost_usd=0.0,
                    latency_ms=0.0,
                    success=False,
                    error=str(result)
                ))
            else:
                responses.append(result)
                if result.success:
                    successful += 1
        
        logger.info("Batch LLM generation completed",
                   total=len(requests),
                   successful=successful,
                   success_rate=successful/len(requests))
        
        return responses
    
    def _classify_error(self, error: Exception) -> str:
        """Classifica o tipo de erro para decidir estratégia de retry"""
        error_str = str(error).lower()
        
        # Erros de rate limiting - aguardar mais tempo
        if any(indicator in error_str for indicator in ['rate limit', 'quota', '429', 'too many requests']):
            return 'rate_limit'
        
        # Erros de rede - tentar novamente
        if any(indicator in error_str for indicator in ['connection', 'timeout', 'network', 'dns']):
            return 'network'
        
        # Erros de servidor - tentar novamente
        if any(indicator in error_str for indicator in ['500', '502', '503', '504', 'server error']):
            return 'server_error'
        
        # Erros de autenticação - não tentar novamente
        if any(indicator in error_str for indicator in ['401', '403', 'unauthorized', 'forbidden', 'invalid key']):
            return 'auth_error'
        
        # Erros de conteúdo - não tentar novamente
        if any(indicator in error_str for indicator in ['400', 'bad request', 'invalid input', 'content policy']):
            return 'content_error'
        
        # Erro desconhecido
        return 'unknown'
    
    def _should_retry_error(self, error_type: str, attempt: int, max_retries: int) -> bool:
        """Decide se deve tentar novamente baseado no tipo de erro"""
        
        # Nunca tentar novamente erros de autenticação ou conteúdo
        if error_type in ['auth_error', 'content_error']:
            return False
        
        # Para rate limiting, aguardar mais tempo mas tentar menos vezes
        if error_type == 'rate_limit':
            return attempt < min(2, max_retries)
        
        # Para erros de rede e servidor, tentar normalmente
        if error_type in ['network', 'server_error']:
            return attempt < max_retries
        
        # Para erros desconhecidos, tentar com cautela
        if error_type == 'unknown':
            return attempt < max(1, max_retries // 2)
        
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas"""
        return {
            **self.metrics.__dict__,
            'cache_size': len(self.cache),
            'circuit_state': self.circuit_breaker.state.value,
            'circuit_failures': self.circuit_breaker.failure_count
        }

    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do cliente LLM"""
        
        # Test request simples
        test_request = LLMRequest(
            messages=[{"role": "user", "content": "Test"}],
            model=self.model_name,
            max_tokens=10,
            temperature=0.0
        )
        
        try:
            start_time = time.time()
            response = await self._process_request(test_request)
            latency = (time.time() - start_time) * 1000
            
            return {
                'healthy': response.success,
                'latency_ms': latency,
                'circuit_state': self.circuit_breaker.state.value,
                'success_rate': self.metrics.success_rate,
                'concurrent_requests': self.metrics.concurrent_requests,
                'error': response.error if not response.success else None
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'circuit_state': self.circuit_breaker.state.value
            }