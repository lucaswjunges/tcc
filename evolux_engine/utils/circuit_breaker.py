# Sistema de Circuit Breaker Avançado para Prevenir Cascata de Falhas

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("circuit_breaker")

class CircuitState(Enum):
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Falhas frequentes, bloqueando chamadas
    HALF_OPEN = "half_open"  # Testando se serviço voltou

@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker"""
    failure_threshold: int = 5          # Falhas para abrir circuito
    recovery_timeout: int = 60          # Tempo para tentar novamente (segundos)
    success_threshold: int = 2          # Sucessos para fechar circuito
    timeout: float = 30.0               # Timeout para operações
    expected_exception: type = Exception
    
    # Configurações avançadas
    failure_rate_threshold: float = 0.5  # Taxa de falha (0.0-1.0)
    minimum_requests: int = 10           # Mínimo de requests para calcular taxa
    sliding_window_size: int = 100       # Tamanho da janela deslizante
    slow_call_threshold: float = 5.0     # Chamadas lentas (segundos)
    slow_call_rate_threshold: float = 0.3 # Taxa de chamadas lentas

@dataclass
class CallRecord:
    """Registro de uma chamada"""
    timestamp: float
    success: bool
    duration: float
    error: Optional[str] = None

class AdvancedCircuitBreaker:
    """
    Circuit Breaker avançado com:
    - Taxa de falha configurável
    - Janela deslizante de estatísticas
    - Detecção de chamadas lentas
    - Métricas detalhadas
    - Backoff exponencial
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # Estado atual
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        
        # Janela deslizante de chamadas
        self.call_history: list[CallRecord] = []
        self.total_calls = 0
        self.total_failures = 0
        self.total_slow_calls = 0
        
        # Backoff exponencial
        self.consecutive_failures = 0
        self.base_timeout = self.config.recovery_timeout
        
        # Lock para thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized", 
                   config=self.config.__dict__)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executa função com proteção do circuit breaker"""
        
        async with self._lock:
            # Verificar se pode executar
            if not await self._can_execute():
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is {self.state.value}",
                    self.state
                )
        
        # Executar função com monitoramento
        start_time = time.time()
        call_success = False
        error = None
        
        try:
            # Aplicar timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs) if asyncio.iscoroutinefunction(func) 
                else asyncio.create_task(asyncio.to_thread(func, *args, **kwargs)),
                timeout=self.config.timeout
            )
            
            call_success = True
            await self._on_success(time.time() - start_time)
            return result
            
        except asyncio.TimeoutError as e:
            error = f"Timeout after {self.config.timeout}s"
            await self._on_failure(time.time() - start_time, error)
            raise CircuitBreakerTimeoutError(error) from e
            
        except self.config.expected_exception as e:
            error = str(e)
            await self._on_failure(time.time() - start_time, error)
            raise
            
        except Exception as e:
            # Exceções inesperadas também contam como falha
            error = f"Unexpected error: {str(e)}"
            await self._on_failure(time.time() - start_time, error)
            raise
        
        finally:
            # Registrar chamada
            call_record = CallRecord(
                timestamp=time.time(),
                success=call_success,
                duration=time.time() - start_time,
                error=error
            )
            await self._record_call(call_record)
    
    async def _can_execute(self) -> bool:
        """Verifica se pode executar baseado no estado atual"""
        
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Usar backoff exponencial para recovery timeout
            recovery_timeout = min(
                self.base_timeout * (2 ** self.consecutive_failures),
                300  # Máximo de 5 minutos
            )
            
            if current_time - self.last_failure_time >= recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN",
                           recovery_timeout=recovery_timeout)
                return True
            
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    async def _on_success(self, duration: float):
        """Processa sucesso da chamada"""
        
        async with self._lock:
            self.success_count += 1
            
            if self.state == CircuitState.HALF_OPEN:
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.consecutive_failures = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery")
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count em caso de sucesso
                if self.failure_count > 0:
                    self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self, duration: float, error: str):
        """Processa falha da chamada"""
        
        async with self._lock:
            self.failure_count += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Voltar para OPEN se falhar em HALF_OPEN
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' returned to OPEN state",
                             error=error)
            
            elif self.state == CircuitState.CLOSED:
                # Verificar se deve abrir
                if await self._should_open():
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit breaker '{self.name}' OPENED due to failures",
                               failure_count=self.failure_count,
                               failure_rate=await self._get_failure_rate(),
                               slow_call_rate=await self._get_slow_call_rate())
    
    async def _should_open(self) -> bool:
        """Decide se deve abrir o circuito baseado em múltiplas métricas"""
        
        # Critério 1: Número absoluto de falhas consecutivas
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Critério 2: Taxa de falha na janela deslizante
        if len(self.call_history) >= self.config.minimum_requests:
            failure_rate = await self._get_failure_rate()
            if failure_rate >= self.config.failure_rate_threshold:
                return True
        
        # Critério 3: Taxa de chamadas lentas
        slow_call_rate = await self._get_slow_call_rate()
        if slow_call_rate >= self.config.slow_call_rate_threshold:
            return True
        
        return False
    
    async def _record_call(self, call_record: CallRecord):
        """Registra chamada na janela deslizante"""
        
        self.call_history.append(call_record)
        self.total_calls += 1
        
        if not call_record.success:
            self.total_failures += 1
        
        if call_record.duration >= self.config.slow_call_threshold:
            self.total_slow_calls += 1
        
        # Manter apenas janela deslizante
        if len(self.call_history) > self.config.sliding_window_size:
            old_record = self.call_history.pop(0)
            if not old_record.success:
                self.total_failures -= 1
            if old_record.duration >= self.config.slow_call_threshold:
                self.total_slow_calls -= 1
    
    async def _get_failure_rate(self) -> float:
        """Calcula taxa de falha na janela atual"""
        if not self.call_history:
            return 0.0
        
        failures = sum(1 for call in self.call_history if not call.success)
        return failures / len(self.call_history)
    
    async def _get_slow_call_rate(self) -> float:
        """Calcula taxa de chamadas lentas"""
        if not self.call_history:
            return 0.0
        
        slow_calls = sum(1 for call in self.call_history 
                        if call.duration >= self.config.slow_call_threshold)
        return slow_calls / len(self.call_history)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas do circuit breaker"""
        
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.total_calls,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'consecutive_failures': self.consecutive_failures,
            'failure_rate': asyncio.create_task(self._get_failure_rate()) if self.call_history else 0.0,
            'slow_call_rate': asyncio.create_task(self._get_slow_call_rate()) if self.call_history else 0.0,
            'window_size': len(self.call_history),
            'last_failure_time': self.last_failure_time,
            'config': self.config.__dict__
        }
    
    async def force_open(self):
        """Força abertura do circuito (para testes ou manutenção)"""
        async with self._lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            logger.warning(f"Circuit breaker '{self.name}' forced OPEN")
    
    async def force_close(self):
        """Força fechamento do circuito (para testes ou manutenção)"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.consecutive_failures = 0
            logger.info(f"Circuit breaker '{self.name}' forced CLOSED")
    
    async def reset(self):
        """Reset completo do circuit breaker"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.consecutive_failures = 0
            self.last_failure_time = 0
            self.call_history.clear()
            self.total_calls = 0
            self.total_failures = 0
            self.total_slow_calls = 0
            logger.info(f"Circuit breaker '{self.name}' reset")

class CircuitBreakerError(Exception):
    """Exceção quando circuit breaker está aberto"""
    def __init__(self, message: str, state: CircuitState):
        super().__init__(message)
        self.state = state

class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Exceção para timeout do circuit breaker"""
    def __init__(self, message: str):
        super().__init__(message, CircuitState.OPEN)

# Registro global de circuit breakers
_circuit_breakers: Dict[str, AdvancedCircuitBreaker] = {}

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> AdvancedCircuitBreaker:
    """Obtém ou cria um circuit breaker pelo nome"""
    
    if name not in _circuit_breakers:
        _circuit_breakers[name] = AdvancedCircuitBreaker(name, config)
    
    return _circuit_breakers[name]

def list_circuit_breakers() -> Dict[str, Dict[str, Any]]:
    """Lista todos os circuit breakers e suas métricas"""
    
    return {
        name: cb.get_metrics() 
        for name, cb in _circuit_breakers.items()
    }

async def reset_all_circuit_breakers():
    """Reset de todos os circuit breakers"""
    
    for cb in _circuit_breakers.values():
        await cb.reset()
    
    logger.info("All circuit breakers reset", count=len(_circuit_breakers))