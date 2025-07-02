import asyncio
import time
from typing import Optional, Deque
from collections import deque
from loguru import logger

class CircuitBreaker:
    """
    Implementa um padrão Circuit Breaker para evitar chamadas repetidas a um serviço com falha.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = "default"):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self._failures: Deque[float] = deque(maxlen=failure_threshold)
        self._last_failure_time: Optional[float] = None
        self._state = "closed"
        self._lock = asyncio.Lock()
        logger.info(f"CircuitBreaker '{self.name}' inicializado: limite={failure_threshold}, timeout={recovery_timeout}s")

    @property
    def state(self) -> str:
        return self._state

    async def __aenter__(self):
        async with self._lock:
            if self._state == "open":
                if time.monotonic() - (self._last_failure_time or 0) > self.recovery_timeout:
                    self._state = "half-open"
                    logger.warning(f"CircuitBreaker '{self.name}' está em modo HALF-OPEN. Permitindo uma requisição de teste.")
                else:
                    raise ConnectionAbortedError(f"CircuitBreaker '{self.name}' está aberto. As chamadas estão bloqueadas.")
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        async with self._lock:
            if exc_type:
                if self._state == "half-open":
                    self._open_circuit()
                    logger.error(f"CircuitBreaker '{self.name}' falhou no estado HALF-OPEN. Reabrindo o circuito.")
                else:
                    self._failures.append(time.monotonic())
                    if len(self._failures) >= self.failure_threshold:
                        self._open_circuit()
            elif self._state == "half-open":
                self._reset()
                logger.success(f"CircuitBreaker '{self.name}' bem-sucedido no estado HALF-OPEN. Fechando o circuito.")

    def _open_circuit(self):
        self._state = "open"
        self._last_failure_time = time.monotonic()
        self._failures.clear()
        logger.error(f"CircuitBreaker '{self.name}' está ABERTO devido a falhas repetidas.")

    def _reset(self):
        self._state = "closed"
        self._failures.clear()
        self._last_failure_time = None
        logger.info(f"CircuitBreaker '{self.name}' está FECHADO.")

class RateLimiter:
    """
    Um limitador de taxa simples baseado no algoritmo de token bucket.
    """
    def __init__(self, requests_per_minute: int, name: str = "default"):
        self.rate_limit = requests_per_minute
        self.tokens = float(self.rate_limit)
        self.last_refill = time.monotonic()
        self.name = name
        self._lock = asyncio.Lock()
        logger.info(f"RateLimiter '{self.name}' inicializado: {requests_per_minute} reqs/min")

    async def wait_for_token(self):
        async with self._lock:
            now = time.monotonic()
            time_since_refill = now - self.last_refill
            
            refill_amount = time_since_refill * (self.rate_limit / 60.0)
            if refill_amount > 0:
                self.tokens = min(self.rate_limit, self.tokens + refill_amount)
                self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60.0 / self.rate_limit)
                logger.warning(f"RateLimiter '{self.name}' atingiu o limite. Aguardando {wait_time:.2f}s.")
                await asyncio.sleep(wait_time)
            
            self.tokens -= 1
