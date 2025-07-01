#!/usr/bin/env python3
# Demo e Teste do Sistema de Circuit Breaker Avançado

import asyncio
import time
import random
from typing import List, Dict, Any

from evolux_engine.utils.circuit_breaker import (
    AdvancedCircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitState,
    get_circuit_breaker,
    list_circuit_breakers,
    reset_all_circuit_breakers
)
from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("circuit_breaker_demo")

class SimulatedService:
    """Serviço simulado para teste do circuit breaker"""
    
    def __init__(self, name: str, failure_rate: float = 0.3, latency_ms: float = 100):
        self.name = name
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0
        self.is_healthy = True
    
    async def call(self, request_data: str = "test") -> Dict[str, Any]:
        """Simula chamada para serviço"""
        self.call_count += 1
        
        # Simular latência
        await asyncio.sleep(self.latency_ms / 1000)
        
        # Simular falhas baseado na taxa
        if not self.is_healthy or random.random() < self.failure_rate:
            raise Exception(f"{self.name} service unavailable (call #{self.call_count})")
        
        return {
            "service": self.name,
            "result": f"Success for {request_data}",
            "call_number": self.call_count,
            "timestamp": time.time()
        }
    
    def set_health(self, healthy: bool):
        """Controla saúde do serviço"""
        self.is_healthy = healthy
        logger.info(f"Service {self.name} health changed", healthy=healthy)

async def demo_basic_circuit_breaker():
    """Demonstra operação básica do circuit breaker"""
    
    logger.info("=== DEMO: Circuit Breaker Básico ===")
    
    # Configurar circuit breaker
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=2,
        success_threshold=2
    )
    
    cb = AdvancedCircuitBreaker("demo_service", config)
    service = SimulatedService("demo", failure_rate=0.8)  # 80% de falhas
    
    logger.info("Testando falhas consecutivas...")
    
    # Provocar falhas para abrir circuito
    for i in range(5):
        try:
            result = await cb.call(service.call, f"request_{i}")
            logger.info("Call succeeded", request=f"request_{i}", result=result)
        except Exception as e:
            logger.warning("Call failed", request=f"request_{i}", error=str(e))
        
        # Mostrar estado atual
        metrics = cb.get_metrics()
        logger.info("Circuit state", state=metrics['state'], failures=metrics['failure_count'])
        
        await asyncio.sleep(0.1)
    
    logger.info("Aguardando recovery timeout...")
    await asyncio.sleep(2.5)
    
    # Recuperar serviço
    service.set_health(True)
    service.failure_rate = 0.1  # Reduzir taxa de falha
    
    logger.info("Testando recuperação...")
    
    # Tentar chamadas de recuperação
    for i in range(3):
        try:
            result = await cb.call(service.call, f"recovery_{i}")
            logger.info("Recovery call succeeded", request=f"recovery_{i}")
        except Exception as e:
            logger.warning("Recovery call failed", error=str(e))
        
        metrics = cb.get_metrics()
        logger.info("Circuit state", state=metrics['state'], success_count=metrics['success_count'])
        
        await asyncio.sleep(0.2)
    
    logger.info("Demo básico concluído\n")
    await cb.reset()

async def demo_slow_call_detection():
    """Demonstra detecção de chamadas lentas"""
    
    logger.info("=== DEMO: Detecção de Chamadas Lentas ===")
    
    config = CircuitBreakerConfig(
        failure_threshold=10,  # Threshold alto para focar em latência
        slow_call_threshold=0.05,  # 50ms
        slow_call_rate_threshold=0.7,  # 70% de chamadas lentas
        minimum_requests=5
    )
    
    cb = AdvancedCircuitBreaker("slow_service", config)
    slow_service = SimulatedService("slow", failure_rate=0.1, latency_ms=100)  # 100ms latência
    
    logger.info("Fazendo chamadas lentas...")
    
    for i in range(8):
        try:
            start_time = time.time()
            result = await cb.call(slow_service.call, f"slow_request_{i}")
            duration_ms = (time.time() - start_time) * 1000
            logger.info("Slow call completed", request=f"slow_request_{i}", duration_ms=duration_ms)
        except Exception as e:
            logger.warning("Slow call failed", error=str(e))
        
        # Verificar taxa de chamadas lentas
        slow_rate = await cb._get_slow_call_rate()
        logger.info("Slow call metrics", slow_rate=slow_rate, calls=len(cb.call_history))
        
        await asyncio.sleep(0.1)
    
    logger.info("Demo de chamadas lentas concluído\n")
    await cb.reset()

async def demo_concurrent_access():
    """Demonstra acesso concorrente"""
    
    logger.info("=== DEMO: Acesso Concorrente ===")
    
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=1
    )
    
    cb = AdvancedCircuitBreaker("concurrent_service", config)
    service = SimulatedService("concurrent", failure_rate=0.3, latency_ms=50)
    
    async def concurrent_worker(worker_id: int, calls: int):
        """Worker que faz múltiplas chamadas"""
        successes = 0
        failures = 0
        
        for i in range(calls):
            try:
                result = await cb.call(service.call, f"worker_{worker_id}_call_{i}")
                successes += 1
            except Exception:
                failures += 1
            
            await asyncio.sleep(0.01)  # Pequena pausa
        
        return {"worker_id": worker_id, "successes": successes, "failures": failures}
    
    logger.info("Iniciando 10 workers concorrentes...")
    
    # Executar workers concorrentemente
    tasks = [concurrent_worker(i, 20) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Compilar estatísticas
    total_successes = sum(r["successes"] for r in results)
    total_failures = sum(r["failures"] for r in results)
    total_calls = total_successes + total_failures
    
    logger.info("Concurrent access results",
               total_calls=total_calls,
               successes=total_successes,
               failures=total_failures,
               success_rate=total_successes/total_calls if total_calls > 0 else 0)
    
    # Métricas finais do circuit breaker
    final_metrics = cb.get_metrics()
    logger.info("Final circuit breaker metrics", **final_metrics)
    
    logger.info("Demo de acesso concorrente concluído\n")
    await cb.reset()

async def demo_global_registry():
    """Demonstra registro global de circuit breakers"""
    
    logger.info("=== DEMO: Registro Global ===")
    
    # Limpar registro
    await reset_all_circuit_breakers()
    
    # Criar vários circuit breakers
    services = ["user_service", "payment_service", "inventory_service", "email_service"]
    
    for service_name in services:
        cb = get_circuit_breaker(service_name)
        logger.info("Circuit breaker created", service=service_name, instance_id=id(cb))
    
    # Verificar que instâncias são reutilizadas
    cb1 = get_circuit_breaker("user_service")
    cb2 = get_circuit_breaker("user_service")
    
    logger.info("Instance reuse test",
               same_instance=cb1 is cb2,
               cb1_id=id(cb1),
               cb2_id=id(cb2))
    
    # Listar todos os circuit breakers
    all_circuit_breakers = list_circuit_breakers()
    logger.info("All circuit breakers", count=len(all_circuit_breakers))
    
    for name, metrics in all_circuit_breakers.items():
        logger.info("Circuit breaker info", name=name, state=metrics.get('state'))
    
    logger.info("Demo de registro global concluído\n")

async def demo_metrics_and_monitoring():
    """Demonstra coleta de métricas"""
    
    logger.info("=== DEMO: Métricas e Monitoramento ===")
    
    config = CircuitBreakerConfig(
        failure_threshold=4,
        sliding_window_size=20,
        minimum_requests=5
    )
    
    cb = AdvancedCircuitBreaker("metrics_service", config)
    service = SimulatedService("metrics", failure_rate=0.4, latency_ms=30)
    
    logger.info("Fazendo 25 chamadas para coletar métricas...")
    
    for i in range(25):
        try:
            result = await cb.call(service.call, f"metrics_call_{i}")
        except Exception:
            pass  # Ignorar falhas para este demo
        
        # Log métricas a cada 5 chamadas
        if (i + 1) % 5 == 0:
            metrics = cb.get_metrics()
            failure_rate = await cb._get_failure_rate()
            slow_call_rate = await cb._get_slow_call_rate()
            
            logger.info("Metrics checkpoint",
                       calls=i+1,
                       state=metrics['state'],
                       total_calls=metrics['total_calls'],
                       failure_count=metrics['failure_count'],
                       success_count=metrics['success_count'],
                       failure_rate=failure_rate,
                       slow_call_rate=slow_call_rate,
                       window_size=metrics['window_size'])
        
        await asyncio.sleep(0.05)
    
    # Métricas finais detalhadas
    final_metrics = cb.get_metrics()
    logger.info("Final detailed metrics", **final_metrics)
    
    logger.info("Demo de métricas concluído\n")
    await cb.reset()

async def performance_benchmark():
    """Benchmark de performance"""
    
    logger.info("=== BENCHMARK: Performance ===")
    
    config = CircuitBreakerConfig(
        failure_threshold=1000,  # Threshold alto para não interferir
        sliding_window_size=500
    )
    
    cb = AdvancedCircuitBreaker("benchmark_service", config)
    
    async def fast_call():
        await asyncio.sleep(0.001)  # 1ms
        return "fast_result"
    
    # Teste de throughput
    logger.info("Iniciando benchmark de throughput...")
    
    start_time = time.time()
    call_count = 1000
    
    # Execução sequencial
    seq_start = time.time()
    for i in range(call_count):
        await cb.call(fast_call)
    seq_duration = time.time() - seq_start
    
    await cb.reset()
    
    # Execução concorrente
    conc_start = time.time()
    tasks = [cb.call(fast_call) for _ in range(call_count)]
    await asyncio.gather(*tasks)
    conc_duration = time.time() - conc_start
    
    # Resultados
    seq_throughput = call_count / seq_duration
    conc_throughput = call_count / conc_duration
    speedup = conc_throughput / seq_throughput
    
    logger.info("Performance benchmark results",
               call_count=call_count,
               sequential_duration=seq_duration,
               concurrent_duration=conc_duration,
               sequential_throughput=seq_throughput,
               concurrent_throughput=conc_throughput,
               speedup_factor=speedup)
    
    await cb.reset()
    logger.info("Benchmark concluído\n")

async def main():
    """Executa todos os demos"""
    
    logger.info("🔄 Iniciando Circuit Breaker Demo Suite")
    logger.info("=" * 50)
    
    try:
        # Executar demos
        await demo_basic_circuit_breaker()
        await demo_slow_call_detection()
        await demo_concurrent_access()
        await demo_global_registry()
        await demo_metrics_and_monitoring()
        await performance_benchmark()
        
        logger.info("✅ Todos os demos executados com sucesso!")
        
    except Exception as e:
        logger.error("❌ Erro durante execução dos demos", error=str(e))
        raise
    
    finally:
        # Limpeza final
        await reset_all_circuit_breakers()
        logger.info("🧹 Limpeza concluída")

if __name__ == "__main__":
    # Executar demo
    asyncio.run(main())