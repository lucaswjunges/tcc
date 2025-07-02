import asyncio
import tempfile
import shutil
import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import uuid

from evolux_engine.utils.logging_utils import get_structured_logger
from evolux_engine.security import SecurityGateway, SecurityValidationResult, SecurityLevel

logger = get_structured_logger("secure_executor")

@dataclass
class ResourceLimits:
    """Limites de recursos para execução"""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_execution_time_seconds: int = 300
    max_disk_usage_mb: int = 100
    allow_network: bool = False

@dataclass
class ExecutionResult:
    """Resultado da execução segura"""
    command_executed: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    resource_usage: Dict[str, float]
    container_id: Optional[str] = None
    files_created: List[str] = None
    files_modified: List[str] = None
    security_warnings: List[str] = None
    
    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []
        if self.files_modified is None:
            self.files_modified = []
        if self.security_warnings is None:
            self.security_warnings = []

class SecureExecutor:
    """
    Executor seguro que executa comandos em containers Docker isolados.
    Implementa a especificação de segurança da Seção 6 do README.
    """
    
    def __init__(self, 
                 security_gateway: Optional[SecurityGateway] = None,
                 default_limits: Optional[ResourceLimits] = None,
                 config_manager: Optional[Any] = None):
        self.security_gateway = security_gateway or SecurityGateway(SecurityLevel.STRICT)
        self.default_limits = default_limits or ResourceLimits()
        self.config_manager = config_manager
        self.execution_count = 0
        self.active_containers: Dict[str, str] = {}  # execution_id -> container_id
        
        # Verificar se Docker está disponível
        self.docker_available = self._check_docker_availability()
        
        logger.info(f"SecureExecutor initialized, docker_available: {self.docker_available}, security_level: {self.security_gateway.security_level.value}")
    
    def _check_docker_availability(self) -> bool:
        """Verifica se Docker está disponível no sistema"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Docker not available, falling back to local execution")
            return False
    
    async def execute_command(self,
                            command: str,
                            working_directory: str,
                            limits: Optional[ResourceLimits] = None,
                            environment: Optional[Dict[str, str]] = None,
                            timeout_seconds: Optional[int] = None) -> ExecutionResult:
        """
        Executa comando de forma segura com isolamento.
        
        Args:
            command: Comando a ser executado
            working_directory: Diretório de trabalho
            limits: Limites de recursos (usa padrão se None)
            environment: Variáveis de ambiente
            timeout_seconds: Timeout específico
            
        Returns:
            Resultado da execução
        """
        
        execution_id = str(uuid.uuid4())
        self.execution_count += 1
        
        logger.info(f"Starting secure command execution for execution_id: {execution_id}, command: {command[:100]}, working_dir: {working_directory}")
        
        # 1. Validação de segurança
        security_result = await self.security_gateway.validate_command(command)
        if not security_result.is_safe:
            logger.warning(f"Command blocked by security gateway for execution_id: {execution_id}, reason: {security_result.blocked_reason}")
            return ExecutionResult(
                command_executed=command,
                exit_code=1,
                stdout="",
                stderr=f"Command blocked: {security_result.blocked_reason}",
                execution_time_ms=0,
                resource_usage={},
                security_warnings=[security_result.blocked_reason or "Security violation"]
            )
        
        # 2. Preparar limites
        exec_limits = limits or self.default_limits
        exec_timeout = timeout_seconds or exec_limits.max_execution_time_seconds
        
        # 3. Executar baseado na disponibilidade do Docker
        if self.docker_available:
            result = await self._execute_in_docker(
                execution_id=execution_id,
                command=security_result.sanitized_command or command,
                working_directory=working_directory,
                limits=exec_limits,
                environment=environment,
                timeout_seconds=exec_timeout
            )
        else:
            result = await self._execute_local_sandbox(
                execution_id=execution_id,
                command=security_result.sanitized_command or command,
                working_directory=working_directory,
                limits=exec_limits,
                environment=environment,
                timeout_seconds=exec_timeout
            )
        
        # 4. Adicionar warnings de segurança
        result.security_warnings.extend(security_result.security_warnings)
        
        logger.info(f"Command execution completed for execution_id: {execution_id}, exit_code: {result.exit_code}, execution_time: {result.execution_time_ms}")
        
        return result
    
    async def _execute_in_docker(self,
                                execution_id: str,
                                command: str,
                                working_directory: str,
                                limits: ResourceLimits,
                                environment: Optional[Dict[str, str]],
                                timeout_seconds: int) -> ExecutionResult:
        """Executa comando em container Docker isolado"""
        
        import subprocess
        import tempfile
        
        start_time = time.time()
        container_id = None
        
        try:
            # Criar diretório temporário para bind mount
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copiar arquivos do working_directory para temp_dir
                if os.path.exists(working_directory):
                    shutil.copytree(working_directory, f"{temp_dir}/workspace", dirs_exist_ok=True)
                else:
                    os.makedirs(f"{temp_dir}/workspace", exist_ok=True)
                
                # Construir comando Docker
                docker_cmd = [
                    'docker', 'run',
                    '--rm',
                    '--network=none' if not limits.allow_network else '--network=bridge',
                    f'--memory={limits.max_memory_mb}m',
                    f'--cpus={limits.max_cpu_percent/100}',
                    f'--ulimit=fsize={limits.max_disk_usage_mb*1024*1024}',  # bytes
                    '--security-opt=no-new-privileges',
                    '--cap-drop=ALL',
                    '--user=1000:1000',  # Non-root user
                    f'--volume={temp_dir}/workspace:/workspace:rw',
                    '--workdir=/workspace',
                    'python:3.11-slim',  # Base image segura
                    'bash', '-c', command
                ]
                
                # Adicionar variáveis de ambiente
                if environment:
                    for key, value in environment.items():
                        docker_cmd.insert(-4, f'--env={key}={value}')
                
                # Executar comando
                logger.debug(f"Executing Docker command for execution_id: {execution_id}, docker_cmd: {docker_cmd[:5]}")
                
                process = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout_seconds
                    )
                    
                    exit_code = process.returncode
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Docker execution timeout for execution_id: {execution_id}")
                    process.kill()
                    await process.wait()
                    
                    return ExecutionResult(
                        command_executed=command,
                        exit_code=124,  # Timeout exit code
                        stdout="",
                        stderr="Execution timed out",
                        execution_time_ms=int(timeout_seconds * 1000),
                        resource_usage={'timeout': True},
                        container_id=container_id
                    )
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Copiar arquivos modificados de volta
                files_created, files_modified = await self._detect_file_changes(
                    working_directory, f"{temp_dir}/workspace"
                )
                
                if os.path.exists(f"{temp_dir}/workspace"):
                    shutil.copytree(f"{temp_dir}/workspace", working_directory, dirs_exist_ok=True)
                
                return ExecutionResult(
                    command_executed=command,
                    exit_code=exit_code,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    execution_time_ms=execution_time_ms,
                    resource_usage=self._estimate_resource_usage(execution_time_ms),
                    container_id=container_id,
                    files_created=files_created,
                    files_modified=files_modified
                )
                
        except Exception as e:
            logger.error(f"Docker execution failed for execution_id: {execution_id}, error: {str(e)}")
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                command_executed=command,
                exit_code=1,
                stdout="",
                stderr=f"Docker execution error: {str(e)}",
                execution_time_ms=execution_time_ms,
                resource_usage={},
                container_id=container_id
            )
    
    async def _execute_local_sandbox(self,
                                   execution_id: str,
                                   command: str,
                                   working_directory: str,
                                   limits: ResourceLimits,
                                   environment: Optional[Dict[str, str]],
                                   timeout_seconds: int) -> ExecutionResult:
        """Executa comando em sandbox local (fallback quando Docker não disponível)"""
        
        import subprocess
        
        start_time = time.time()

        # Otimização para modo de teste: não reinstalar dependências
        execution_mode = self.config_manager.get_global_setting("execution_mode", "producao") if self.config_manager else "producao"
        if execution_mode == "teste" and "pip install" in command:
            logger.info(f"Modo de teste: Pulando a instalação de dependências para o comando: {command}")
            return ExecutionResult(
                command_executed=command,
                exit_code=0,
                stdout="Dependencies installation skipped in test mode.",
                stderr="",
                execution_time_ms=int((time.time() - start_time) * 1000),
                resource_usage=self._estimate_resource_usage(0),
                security_warnings=["Dependency installation skipped due to test mode."]
            )
        
        try:
            # Preparar ambiente
            env = os.environ.copy()
            if environment:
                env.update(environment)
            
            # Executar comando com timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
                
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                logger.warning(f"Local execution timeout for execution_id: {execution_id}")
                process.kill()
                await process.wait()
                
                return ExecutionResult(
                    command_executed=command,
                    exit_code=124,
                    stdout="",
                    stderr="Execution timed out",
                    execution_time_ms=int(timeout_seconds * 1000),
                    resource_usage={'timeout': True}
                )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Detectar mudanças em arquivos (simplificado para modo local)
            files_created = []
            files_modified = []
            
            return ExecutionResult(
                command_executed=command,
                exit_code=exit_code,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                execution_time_ms=execution_time_ms,
                resource_usage=self._estimate_resource_usage(execution_time_ms),
                files_created=files_created,
                files_modified=files_modified,
                security_warnings=["Executed in local sandbox (Docker not available)"]
            )
            
        except Exception as e:
            logger.error(f"Local execution failed for execution_id: {execution_id}, error: {str(e)}")
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                command_executed=command,
                exit_code=1,
                stdout="",
                stderr=f"Local execution error: {str(e)}",
                execution_time_ms=execution_time_ms,
                resource_usage={}
            )
    
    async def _detect_file_changes(self, 
                                 original_dir: str, 
                                 modified_dir: str) -> tuple[List[str], List[str]]:
        """Detecta arquivos criados e modificados"""
        
        files_created = []
        files_modified = []
        
        try:
            if not os.path.exists(modified_dir):
                return files_created, files_modified
            
            # Listar arquivos no diretório modificado
            for root, dirs, files in os.walk(modified_dir):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), modified_dir)
                    original_file = os.path.join(original_dir, rel_path)
                    
                    if not os.path.exists(original_file):
                        files_created.append(rel_path)
                    else:
                        # Verificar se foi modificado (timestamp ou tamanho)
                        modified_stat = os.stat(os.path.join(root, file))
                        original_stat = os.stat(original_file)
                        
                        if (modified_stat.st_mtime > original_stat.st_mtime or 
                            modified_stat.st_size != original_stat.st_size):
                            files_modified.append(rel_path)
            
        except Exception as e:
            logger.warning(f"Error detecting file changes: {str(e)}")
        
        return files_created, files_modified
    
    def _estimate_resource_usage(self, execution_time_ms: int) -> Dict[str, float]:
        """Estima uso de recursos baseado no tempo de execução"""
        
        # Estimativas simplificadas
        # Em produção, isso seria coletado via Docker stats ou ferramentas de monitoramento
        
        base_cpu = min(50.0, execution_time_ms / 100)  # Estimativa de CPU
        base_memory = min(100.0, execution_time_ms / 50)  # Estimativa de memória em MB
        
        return {
            'cpu_percent_peak': base_cpu,
            'memory_mb_peak': base_memory,
            'execution_time_ms': execution_time_ms
        }
    
    async def cleanup_execution(self, execution_id: str):
        """Limpa recursos de uma execução específica com timeout e força"""
        
        if execution_id in self.active_containers:
            container_id = self.active_containers[execution_id]
            
            try:
                # Primeiro tenta parar graciosamente
                stop_proc = await asyncio.create_subprocess_exec(
                    'docker', 'stop', '--time', '10', container_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(stop_proc.communicate(), timeout=15)
                    if stop_proc.returncode != 0:
                        logger.warning(f"Docker stop failed, trying force kill for execution_id: {execution_id}, stderr: {stderr.decode()}")
                        
                        # Se falhar, força a remoção
                        kill_proc = await asyncio.create_subprocess_exec(
                            'docker', 'rm', '--force', container_id,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await asyncio.wait_for(kill_proc.communicate(), timeout=10)
                        
                except asyncio.TimeoutError:
                    logger.error(f"Container cleanup timeout, forcing removal for execution_id: {execution_id}, container_id: {container_id}")
                    
                    # Último recurso: force remove
                    try:
                        force_proc = await asyncio.create_subprocess_exec(
                            'docker', 'rm', '--force', container_id,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await asyncio.wait_for(force_proc.communicate(), timeout=5)
                    except:
                        logger.error(f"Failed to force remove container: {container_id}")
                
                logger.info(f"Container stopped and cleaned up for execution_id: {execution_id}, container_id: {container_id}")
                
            except Exception as e:
                logger.error(f"Failed to cleanup container for execution_id: {execution_id}, container_id: {container_id}, error: {str(e)}")
            
            finally:
                # Sempre remove da lista ativa, mesmo se cleanup falhou
                self.active_containers.pop(execution_id, None)
                
                # Limpa também volumes temporários se existirem
                await self._cleanup_temp_volumes(execution_id)
    
    async def _cleanup_temp_volumes(self, execution_id: str):
        """Limpa volumes temporários associados a uma execução"""
        try:
            # Lista volumes com o padrão de nome da execução
            list_proc = await asyncio.create_subprocess_exec(
                'docker', 'volume', 'ls', '--filter', f'name=evolux-{execution_id}',
                '--format', '{{.Name}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            stdout, _ = await list_proc.communicate()
            volume_names = stdout.decode().strip().split('\n')
            
            # Remove cada volume encontrado
            for volume_name in volume_names:
                if volume_name and volume_name.startswith(f'evolux-{execution_id}'):
                    try:
                        rm_proc = await asyncio.create_subprocess_exec(
                            'docker', 'volume', 'rm', volume_name,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await rm_proc.communicate()
                        logger.debug(f"Cleaned up volume: {volume_name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup volume: {volume_name}, error: {str(e)}")
                        
        except Exception as e:
            logger.warning(f"Error during volume cleanup for execution_id: {execution_id}, error: {str(e)}")
    
    async def cleanup_all(self):
        """Limpa todos os recursos ativos"""
        
        cleanup_tasks = []
        for execution_id in list(self.active_containers.keys()):
            cleanup_tasks.append(self.cleanup_execution(execution_id))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info(f"All executions cleaned up: {self.execution_count}")
    
    def get_executor_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do executor"""
        
        security_stats = self.security_gateway.get_security_stats()
        
        return {
            'total_executions': self.execution_count,
            'active_containers': len(self.active_containers),
            'docker_available': self.docker_available,
            'security_stats': security_stats,
            'default_limits': {
                'max_memory_mb': self.default_limits.max_memory_mb,
                'max_cpu_percent': self.default_limits.max_cpu_percent,
                'max_execution_time_seconds': self.default_limits.max_execution_time_seconds,
                'allow_network': self.default_limits.allow_network
            }
        }
