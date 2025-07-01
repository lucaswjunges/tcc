#!/usr/bin/env python3
"""
Teste de Performance: Comparação entre Evolux Síncrono vs Assíncrono

Este script demonstra os ganhos de performance com assincronia extensiva.
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# Adicionar path do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Configurar ambiente
from dotenv import load_dotenv
load_dotenv()

from evolux_engine.services.config_manager import ConfigManager
from evolux_engine.services.advanced_context_manager import AdvancedContextManager
from evolux_engine.config.advanced_config import AdvancedSystemConfig
from evolux_engine.core.async_orchestrator import AsyncOrchestrator
from evolux_engine.core.orchestrator import Orchestrator

async def create_test_project(goal: str, project_suffix: str = ""):
    """Cria projeto de teste"""
    
    config = ConfigManager()
    advanced_config = AdvancedSystemConfig()
    context_manager = AdvancedContextManager(config=advanced_config)
    
    project_name = f"Test Performance Project {project_suffix}"
    project_context = context_manager.create_new_project_context(
        goal=goal,
        project_name=project_name
    )
    
    return project_context, config

async def test_async_orchestrator(goal: str) -> Dict[str, Any]:
    """Testa o Orchestrator assíncrono"""
    
    print("🚀 Testando AsyncOrchestrator...")
    start_time = time.time()
    
    try:
        # Criar projeto
        project_context, config = await create_test_project(goal, "Async")
        
        # Criar orchestrator assíncrono
        async_orchestrator = AsyncOrchestrator(
            project_context=project_context,
            config_manager=config
        )
        
        # Executar ciclo
        result_status = await async_orchestrator.run_project_cycle_parallel()
        
        # Obter métricas
        metrics = await async_orchestrator.get_parallel_metrics()
        
        execution_time = time.time() - start_time
        
        return {
            'type': 'async',
            'status': result_status.value,
            'execution_time': execution_time,
            'metrics': metrics,
            'project_id': project_context.project_id
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Erro no AsyncOrchestrator: {e}")
        return {
            'type': 'async',
            'status': 'error',
            'execution_time': execution_time,
            'error': str(e),
            'metrics': {}
        }

def test_sync_orchestrator(goal: str) -> Dict[str, Any]:
    """Testa o Orchestrator síncrono"""
    
    print("🐌 Testando Orchestrator síncrono...")
    start_time = time.time()
    
    try:
        # Usar asyncio.run para criar projeto mesmo no teste sync
        project_context, config = asyncio.run(create_test_project(goal, "Sync"))
        
        # Criar orchestrator síncrono
        sync_orchestrator = Orchestrator(
            project_context=project_context,
            config_manager=config
        )
        
        # Executar ciclo (precisa usar asyncio.run)
        result_status = asyncio.run(sync_orchestrator.run_project_cycle())
        
        execution_time = time.time() - start_time
        
        return {
            'type': 'sync',
            'status': result_status.value,
            'execution_time': execution_time,
            'project_id': project_context.project_id,
            'metrics': {}
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Erro no Orchestrator síncrono: {e}")
        return {
            'type': 'sync',
            'status': 'error',
            'execution_time': execution_time,
            'error': str(e),
            'metrics': {}
        }

def print_performance_comparison(async_result: Dict[str, Any], sync_result: Dict[str, Any]):
    """Imprime comparação de performance"""
    
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE PERFORMANCE - ASSINCRONIA NO EVOLUX")
    print("="*80)
    
    # Tempos de execução
    async_time = async_result.get('execution_time', 0)
    sync_time = sync_result.get('execution_time', 0)
    
    if sync_time > 0:
        speedup = sync_time / async_time
        improvement = ((sync_time - async_time) / sync_time) * 100
    else:
        speedup = 0
        improvement = 0
    
    print(f"\n⏱️  TEMPOS DE EXECUÇÃO:")
    print(f"   AsyncOrchestrator:  {async_time:.2f}s")
    print(f"   Orchestrator:       {sync_time:.2f}s")
    print(f"   Speedup:            {speedup:.2f}x")
    print(f"   Melhoria:           {improvement:.1f}%")
    
    # Status dos projetos
    print(f"\n✅ STATUS DOS PROJETOS:")
    print(f"   AsyncOrchestrator:  {async_result.get('status', 'unknown')}")
    print(f"   Orchestrator:       {sync_result.get('status', 'unknown')}")
    
    # Métricas detalhadas do async
    if 'metrics' in async_result and async_result['metrics']:
        metrics = async_result['metrics']
        
        print(f"\n📈 MÉTRICAS ASSÍNCRONAS:")
        
        # Métricas de paralelização
        if 'parallel_execution' in metrics:
            parallel = metrics['parallel_execution']
            print(f"   Total de tarefas:        {parallel.get('total_tasks', 0)}")
            print(f"   Tarefas paralelas:       {parallel.get('parallel_tasks', 0)}")
            print(f"   Tarefas sequenciais:     {parallel.get('sequential_tasks', 0)}")
            print(f"   Eficiência paralela:     {parallel.get('parallelization_efficiency', 0):.1%}")
            print(f"   Speedup estimado:        {parallel.get('speedup_factor', 1):.2f}x")
        
        # Métricas de LLM
        if 'llm_clients' in metrics:
            llm = metrics['llm_clients']
            total_requests = 0
            total_cache_hits = 0
            
            for client_name, client_metrics in llm.items():
                requests = client_metrics.get('total_requests', 0)
                cache_hits = client_metrics.get('cache_hits', 0)
                total_requests += requests
                total_cache_hits += cache_hits
            
            if total_requests > 0:
                cache_rate = (total_cache_hits / total_requests) * 100
                print(f"\n🧠 OTIMIZAÇÕES LLM:")
                print(f"   Total de requests:       {total_requests}")
                print(f"   Cache hits:              {total_cache_hits}")
                print(f"   Taxa de cache:           {cache_rate:.1f}%")
        
        # Métricas de arquivo
        if 'file_service' in metrics:
            file_metrics = metrics['file_service']
            print(f"\n📁 OPERAÇÕES DE ARQUIVO:")
            print(f"   Total de operações:      {file_metrics.get('total_operations', 0)}")
            print(f"   Bytes escritos:          {file_metrics.get('bytes_written', 0):,}")
            print(f"   Bytes lidos:             {file_metrics.get('bytes_read', 0):,}")
            print(f"   Max concorrentes:        {file_metrics.get('max_concurrent', 0)}")
    
    # Conclusões
    print(f"\n🎯 CONCLUSÕES:")
    if speedup > 1.5:
        print(f"   ✨ EXCELENTE! Assincronia trouxe {speedup:.1f}x de melhoria")
    elif speedup > 1.2:
        print(f"   ✅ BOM! Assincronia melhorou performance em {improvement:.1f}%")
    elif speedup > 1.0:
        print(f"   ⚡ Pequena melhoria de {improvement:.1f}% com assincronia")
    else:
        print(f"   ⚠️  Overhead assíncrono pode estar afetando performance")
    
    print(f"\n💡 BENEFÍCIOS DA ASSINCRONIA IMPLEMENTADA:")
    print(f"   • Execução paralela de tarefas independentes")
    print(f"   • I/O não-bloqueante para arquivos")
    print(f"   • Concorrência em chamadas LLM")
    print(f"   • Cache inteligente com circuit breaker")
    print(f"   • Observabilidade em tempo real")
    print(f"   • Detecção automática de dependências")
    
    print("\n" + "="*80)

async def main():
    """Função principal de teste"""
    
    print("🧪 TESTE DE PERFORMANCE - ASSINCRONIA NO EVOLUX")
    print("Este teste compara o Orchestrator original vs AsyncOrchestrator")
    print("\nConfigurando testes...")
    
    # Goal simples para teste rápido
    test_goal = "Criar uma aplicação Python simples com 3 arquivos: main.py, utils.py e requirements.txt"
    
    print(f"🎯 Objetivo do teste: {test_goal}\n")
    
    # Executar testes
    try:
        # Teste assíncrono
        async_result = await test_async_orchestrator(test_goal)
        
        # Teste síncrono
        sync_result = test_sync_orchestrator(test_goal)
        
        # Comparar resultados
        print_performance_comparison(async_result, sync_result)
        
        # Salvar resultados
        results = {
            'async': async_result,
            'sync': sync_result,
            'test_goal': test_goal,
            'timestamp': time.time()
        }
        
        results_file = Path('performance_test_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Resultados salvos em: {results_file}")
        
    except KeyboardInterrupt:
        print("\n⛔ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Executar teste
    asyncio.run(main())