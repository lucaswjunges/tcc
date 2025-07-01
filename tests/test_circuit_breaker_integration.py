# Testes de Integração para Circuit Breaker Avançado

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from evolux_engine.utils.circuit_breaker import (
    AdvancedCircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitState, 
    CircuitBreakerError,
    get_circuit_breaker,
    reset_all_circuit_breakers
)

class TestAdvancedCircuitBreaker:
    
    @pytest.fixture
    async def circuit_breaker(self):
        """Fixture para circuit breaker básico"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,  # 1 segundo para testes rápidos
            success_threshold=2,
            failure_rate_threshold=0.5,
            minimum_requests=5,
            slow_call_threshold=0.1,  # 100ms
            slow_call_rate_threshold=0.3
        )
        cb = AdvancedCircuitBreaker("test_circuit", config)
        yield cb
        await cb.reset()
    
    @pytest.fixture
    async def failing_function(self):
        """Função que sempre falha"""
        async def fail():
            raise Exception("Test failure")
        return fail
    
    @pytest.fixture
    async def slow_function(self):
        """Função que é lenta"""
        async def slow():
            await asyncio.sleep(0.2)  # 200ms - maior que threshold
            return "slow result"
        return slow
    
    @pytest.fixture
    async def success_function(self):
        """Função que sempre tem sucesso"""
        async def success():
            return "success"
        return success

    @pytest.mark.asyncio
    async def test_circuit_breaker_basic_operation(self, circuit_breaker, success_function):
        """Testa operação básica do circuit breaker"""
        # Estado inicial deve ser CLOSED
        assert circuit_breaker.state == CircuitState.CLOSED
        
        # Função de sucesso deve passar
        result = await circuit_breaker.call(success_function)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, circuit_breaker, failing_function):
        """Testa se circuito abre após falhas consecutivas"""
        
        # Falhar 3 vezes (threshold)
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_function)
            assert circuit_breaker.state == CircuitState.CLOSED
        
        # Na 4ª falha, circuito deve abrir
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_function)
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Próximas chamadas devem ser rejeitadas
        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit_breaker.call(success_function)
        assert "is open" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_recovery(self, circuit_breaker, failing_function, success_function):
        """Testa recuperação via estado HALF_OPEN"""
        
        # Abrir circuito com falhas
        for i in range(4):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_function)
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Aguardar recovery timeout
        await asyncio.sleep(1.1)
        
        # Próxima chamada deve transicionar para HALF_OPEN
        result = await circuit_breaker.call(success_function)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        
        # Segunda chamada de sucesso deve fechar circuito
        result = await circuit_breaker.call(success_function)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_slow_call_detection(self, circuit_breaker, slow_function):
        """Testa detecção de chamadas lentas"""
        
        # Fazer várias chamadas lentas
        for i in range(6):  # Mais que minimum_requests
            result = await circuit_breaker.call(slow_function)
            assert result == "slow result"
        
        # Circuit breaker deve detectar alta taxa de chamadas lentas
        # e eventualmente abrir (dependendo da configuração)
        slow_call_rate = await circuit_breaker._get_slow_call_rate()
        assert slow_call_rate > 0.3  # Acima do threshold
    
    @pytest.mark.asyncio
    async def test_failure_rate_threshold(self, circuit_breaker):
        """Testa threshold de taxa de falha"""
        
        # Mix de sucessos e falhas para atingir minimum_requests
        calls = []
        
        # 3 sucessos, 3 falhas = 50% failure rate
        for i in range(3):
            calls.append(self._success_call())
        for i in range(3):
            calls.append(self._failure_call())
        
        # Executar chamadas
        for call_func in calls:
            try:
                await circuit_breaker.call(call_func)
            except Exception:
                pass  # Esperado para chamadas de falha
        
        # Verificar taxa de falha
        failure_rate = await circuit_breaker._get_failure_rate()
        assert abs(failure_rate - 0.5) < 0.1  # Aproximadamente 50%
    
    async def _success_call(self):
        """Chamada que sempre tem sucesso"""
        return "success"
    
    async def _failure_call(self):
        """Chamada que sempre falha"""
        raise Exception("Expected test failure")
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, circuit_breaker, success_function, failing_function):
        """Testa coleta de métricas"""
        
        # Fazer algumas chamadas mistas
        await circuit_breaker.call(success_function)
        await circuit_breaker.call(success_function)
        
        try:
            await circuit_breaker.call(failing_function)
        except Exception:
            pass
        
        # Verificar métricas
        metrics = circuit_breaker.get_metrics()
        
        assert metrics['name'] == 'test_circuit'
        assert metrics['state'] == CircuitState.CLOSED.value
        assert metrics['total_calls'] > 0
        assert metrics['failure_count'] > 0
        assert metrics['success_count'] > 0
    
    @pytest.mark.asyncio
    async def test_manual_control(self, circuit_breaker):
        """Testa controle manual do circuit breaker"""
        
        # Forçar abertura
        await circuit_breaker.force_open()
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Forçar fechamento
        await circuit_breaker.force_close()
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        
        # Reset completo
        await circuit_breaker.reset()
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.total_calls == 0

class TestCircuitBreakerIntegration:
    """Testes de integração com outros sistemas"""
    
    @pytest.mark.asyncio
    async def test_global_circuit_breaker_registry(self):
        """Testa registro global de circuit breakers"""
        
        # Limpar registros existentes
        await reset_all_circuit_breakers()
        
        # Criar circuit breakers
        cb1 = get_circuit_breaker("service1")
        cb2 = get_circuit_breaker("service2")
        cb3 = get_circuit_breaker("service1")  # Mesmo nome
        
        # Verificar que cb1 e cb3 são a mesma instância
        assert cb1 is cb3
        assert cb1 is not cb2
        
        # Reset global
        await reset_all_circuit_breakers()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Testa acesso concorrente ao circuit breaker"""
        
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=1
        )
        cb = AdvancedCircuitBreaker("concurrent_test", config)
        
        async def concurrent_call(call_id: int):
            """Chamada concorrente"""
            try:
                if call_id % 3 == 0:  # 1/3 das chamadas falham
                    raise Exception(f"Failure {call_id}")
                else:
                    await asyncio.sleep(0.01)  # Simular processamento
                    return f"Success {call_id}"
            except Exception as e:
                raise e
        
        # Executar 50 chamadas concorrentes
        tasks = []
        for i in range(50):
            task = asyncio.create_task(cb.call(concurrent_call, i))
            tasks.append(task)
        
        # Aguardar conclusão (algumas vão falhar)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar resultados
        successes = [r for r in results if isinstance(r, str)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        assert len(successes) > 0
        assert len(failures) > 0
        
        # Verificar métricas
        metrics = cb.get_metrics()
        assert metrics['total_calls'] == 50
        
        await cb.reset()
    
    @pytest.mark.asyncio
    async def test_llm_client_integration(self):
        """Testa integração com cliente LLM (mock)"""
        
        # Mock do cliente LLM
        mock_llm_client = AsyncMock()
        
        # Configurar diferentes cenários
        call_count = 0
        
        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 3:
                return {"content": "success", "tokens": 100}
            elif call_count <= 6:
                raise Exception("Rate limit exceeded")
            else:
                return {"content": "recovered", "tokens": 150}
        
        mock_llm_client.call_api = mock_api_call
        
        # Circuit breaker para LLM
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.5,
            success_threshold=1
        )
        llm_cb = AdvancedCircuitBreaker("llm_client", config)
        
        # Primeiras 3 chamadas devem ter sucesso
        for i in range(3):
            result = await llm_cb.call(mock_llm_client.call_api)
            assert result["content"] == "success"
        
        # Próximas 3 falham e abrem o circuito
        for i in range(3):
            with pytest.raises(Exception):
                await llm_cb.call(mock_llm_client.call_api)
        
        # Circuito deve estar aberto
        assert llm_cb.state == CircuitState.OPEN
        
        # Aguardar recovery
        await asyncio.sleep(0.6)
        
        # Próxima chamada deve recuperar
        result = await llm_cb.call(mock_llm_client.call_api)
        assert result["content"] == "recovered"
        assert llm_cb.state == CircuitState.CLOSED
        
        await llm_cb.reset()
    
    @pytest.mark.asyncio
    async def test_database_connection_simulation(self):
        """Testa simulação de conexão com banco de dados"""
        
        class MockDatabase:
            def __init__(self):
                self.connection_failures = 0
                self.max_failures = 5
            
            async def query(self, sql: str):
                if self.connection_failures < self.max_failures:
                    self.connection_failures += 1
                    raise Exception("Connection timeout")
                else:
                    return [{"id": 1, "name": "test"}]
        
        db = MockDatabase()
        
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.1,
            success_threshold=1
        )
        db_cb = AdvancedCircuitBreaker("database", config)
        
        # Primeiras chamadas falham
        for i in range(3):
            with pytest.raises(Exception):
                await db_cb.call(db.query, "SELECT * FROM users")
        
        # Circuit breaker deve abrir
        with pytest.raises(CircuitBreakerError):
            await db_cb.call(db.query, "SELECT * FROM users")
        
        assert db_cb.state == CircuitState.OPEN
        
        # Simular recuperação do banco
        db.connection_failures = db.max_failures
        
        # Aguardar recovery timeout
        await asyncio.sleep(0.2)
        
        # Tentar novamente - deve recuperar
        result = await db_cb.call(db.query, "SELECT * FROM users")
        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert db_cb.state == CircuitState.CLOSED
        
        await db_cb.reset()

class TestCircuitBreakerPerformance:
    """Testes de performance do circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Testa alta throughput de chamadas"""
        
        config = CircuitBreakerConfig(
            failure_threshold=100,
            minimum_requests=50
        )
        cb = AdvancedCircuitBreaker("performance_test", config)
        
        async def fast_call():
            await asyncio.sleep(0.001)  # 1ms
            return "fast"
        
        start_time = time.time()
        
        # 1000 chamadas concorrentes
        tasks = [cb.call(fast_call) for _ in range(1000)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verificar resultados
        assert len(results) == 1000
        assert all(r == "fast" for r in results)
        
        # Performance check - deve processar >100 calls/second
        calls_per_second = 1000 / duration
        assert calls_per_second > 100
        
        print(f"Performance: {calls_per_second:.2f} calls/second")
        
        await cb.reset()
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Testa uso de memória com sliding window"""
        
        config = CircuitBreakerConfig(
            sliding_window_size=100,  # Window pequena
            failure_threshold=1000    # Threshold alto para não abrir
        )
        cb = AdvancedCircuitBreaker("memory_test", config)
        
        async def dummy_call():
            return "result"
        
        # Fazer muitas chamadas para testar sliding window
        for i in range(500):
            await cb.call(dummy_call)
        
        # Window deve estar limitada
        assert len(cb.call_history) <= 100
        
        # Métricas devem estar corretas
        metrics = cb.get_metrics()
        assert metrics['total_calls'] == 500
        assert metrics['window_size'] == 100
        
        await cb.reset()

if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])