# Async File Service com I/O não-bloqueante

import asyncio
import aiofiles
import aiofiles.os
import hashlib
import os
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import time
from dataclasses import dataclass

from .observability_service import log

@dataclass
class FileOperationResult:
    """Resultado de operação de arquivo"""
    success: bool
    file_path: str
    operation: str
    duration_ms: float
    size_bytes: Optional[int] = None
    error: Optional[str] = None

class AsyncFileService:
    """
    File Service com async I/O completo para máxima performance.
    Suporta operações concorrentes e batch processing.
    """
    
    def __init__(self, workspace_path: str, max_concurrent_ops: int = 10):
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_ops = max_concurrent_ops
        self.semaphore = asyncio.Semaphore(max_concurrent_ops)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Metrics tracking
        self.operation_count = 0
        self.total_bytes_written = 0
        self.total_bytes_read = 0
        
        log.info(f"AsyncFileService initialized", 
                workspace=str(self.workspace_path),
                max_concurrent=max_concurrent_ops)

    def _get_full_path(self, relative_path: str) -> Path:
        """Resolve caminho relativo com segurança"""
        full_path = self.workspace_path.joinpath(relative_path).resolve()
        if self.workspace_path.resolve() not in full_path.parents and full_path != self.workspace_path.resolve():
            raise PermissionError(f"Access denied: Cannot access files outside workspace: {relative_path}")
        return full_path

    async def write_file(self, file_path: str, content: str) -> FileOperationResult:
        """Escreve arquivo de forma assíncrona"""
        async with self.semaphore:
            start_time = time.time()
            path = self._get_full_path(file_path)
            
            try:
                # Criar diretórios parent assincronamente
                await aiofiles.os.makedirs(path.parent, exist_ok=True)
                
                # Escrever arquivo
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                
                # Atualizar métricas
                content_bytes = len(content.encode('utf-8'))
                self.total_bytes_written += content_bytes
                self.operation_count += 1
                
                duration_ms = (time.time() - start_time) * 1000
                
                log.info(f"File written successfully", 
                        file=file_path, 
                        size_bytes=content_bytes,
                        duration_ms=duration_ms)
                
                return FileOperationResult(
                    success=True,
                    file_path=file_path,
                    operation="write",
                    duration_ms=duration_ms,
                    size_bytes=content_bytes
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(e)
                log.error(f"Failed to write file", 
                         file=file_path, 
                         error=error_msg,
                         duration_ms=duration_ms)
                
                return FileOperationResult(
                    success=False,
                    file_path=file_path,
                    operation="write",
                    duration_ms=duration_ms,
                    error=error_msg
                )

    async def read_file(self, file_path: str) -> tuple[Optional[str], FileOperationResult]:
        """Lê arquivo de forma assíncrona"""
        async with self.semaphore:
            start_time = time.time()
            path = self._get_full_path(file_path)
            
            try:
                # Verificar se arquivo existe
                if not await aiofiles.os.path.isfile(path):
                    duration_ms = (time.time() - start_time) * 1000
                    return None, FileOperationResult(
                        success=False,
                        file_path=file_path,
                        operation="read",
                        duration_ms=duration_ms,
                        error="File not found"
                    )
                
                # Ler arquivo
                async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Atualizar métricas
                content_bytes = len(content.encode('utf-8'))
                self.total_bytes_read += content_bytes
                self.operation_count += 1
                
                duration_ms = (time.time() - start_time) * 1000
                
                log.debug(f"File read successfully", 
                         file=file_path, 
                         size_bytes=content_bytes,
                         duration_ms=duration_ms)
                
                return content, FileOperationResult(
                    success=True,
                    file_path=file_path,
                    operation="read",
                    duration_ms=duration_ms,
                    size_bytes=content_bytes
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(e)
                log.error(f"Failed to read file", 
                         file=file_path, 
                         error=error_msg,
                         duration_ms=duration_ms)
                
                return None, FileOperationResult(
                    success=False,
                    file_path=file_path,
                    operation="read",
                    duration_ms=duration_ms,
                    error=error_msg
                )

    async def batch_write_files(self, files: Dict[str, str]) -> List[FileOperationResult]:
        """Escreve múltiplos arquivos de forma concorrente"""
        log.info(f"Starting batch write operation", file_count=len(files))
        
        # Criar tarefas concorrentes
        tasks = [
            self.write_file(file_path, content) 
            for file_path, content in files.items()
        ]
        
        # Executar todas as tarefas concorrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        successful_ops = sum(1 for r in results if isinstance(r, FileOperationResult) and r.success)
        total_duration = sum(r.duration_ms for r in results if isinstance(r, FileOperationResult))
        
        log.info(f"Batch write completed", 
                successful=successful_ops,
                total=len(files),
                total_duration_ms=total_duration)
        
        return [r if isinstance(r, FileOperationResult) else 
                FileOperationResult(False, "unknown", "batch_write", 0, error=str(r)) 
                for r in results]

    async def batch_read_files(self, file_paths: List[str]) -> Dict[str, tuple[Optional[str], FileOperationResult]]:
        """Lê múltiplos arquivos de forma concorrente"""
        log.info(f"Starting batch read operation", file_count=len(file_paths))
        
        # Criar tarefas concorrentes
        tasks = [self.read_file(file_path) for file_path in file_paths]
        
        # Executar todas as tarefas concorrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        result_dict = {}
        successful_ops = 0
        
        for i, result in enumerate(results):
            file_path = file_paths[i]
            if isinstance(result, Exception):
                result_dict[file_path] = (None, FileOperationResult(
                    False, file_path, "batch_read", 0, error=str(result)
                ))
            else:
                content, op_result = result
                result_dict[file_path] = (content, op_result)
                if op_result.success:
                    successful_ops += 1
        
        log.info(f"Batch read completed", 
                successful=successful_ops,
                total=len(file_paths))
        
        return result_dict

    async def get_file_hash(self, file_path: str) -> tuple[str, FileOperationResult]:
        """Calcula hash de arquivo de forma assíncrona"""
        async with self.semaphore:
            start_time = time.time()
            path = self._get_full_path(file_path)
            
            try:
                if not await aiofiles.os.path.isfile(path):
                    duration_ms = (time.time() - start_time) * 1000
                    return "", FileOperationResult(
                        False, file_path, "hash", duration_ms, error="File not found"
                    )
                
                # Usar thread pool para operação CPU-intensiva
                hash_hex = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self._compute_file_hash, path
                )
                
                duration_ms = (time.time() - start_time) * 1000
                file_size = await aiofiles.os.path.getsize(path)
                
                return hash_hex, FileOperationResult(
                    True, file_path, "hash", duration_ms, size_bytes=file_size
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return "", FileOperationResult(
                    False, file_path, "hash", duration_ms, error=str(e)
                )

    def _compute_file_hash(self, path: Path) -> str:
        """Computa hash em thread separada (CPU-bound)"""
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def list_files_async(self, sub_dir: str = ".") -> tuple[List[str], FileOperationResult]:
        """Lista arquivos de forma assíncrona"""
        start_time = time.time()
        dir_path = self._get_full_path(sub_dir)
        
        try:
            if not await aiofiles.os.path.isdir(dir_path):
                duration_ms = (time.time() - start_time) * 1000
                return [], FileOperationResult(
                    False, sub_dir, "list", duration_ms, error="Directory not found"
                )
            
            # Usar thread pool para os.walk (I/O bound mas não async)
            files = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool, self._walk_directory, dir_path
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return files, FileOperationResult(
                True, sub_dir, "list", duration_ms, size_bytes=len(files)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return [], FileOperationResult(
                False, sub_dir, "list", duration_ms, error=str(e)
            )

    def _walk_directory(self, dir_path: Path) -> List[str]:
        """Percorre diretório em thread separada"""
        all_files = []
        for root, _, files in os.walk(dir_path):
            for name in files:
                full_file_path = Path(root) / name
                relative_path = full_file_path.relative_to(self.workspace_path)
                all_files.append(str(relative_path))
        return all_files

    async def delete_file(self, file_path: str) -> FileOperationResult:
        """Deleta arquivo de forma assíncrona"""
        async with self.semaphore:
            start_time = time.time()
            path = self._get_full_path(file_path)
            
            try:
                if not await aiofiles.os.path.isfile(path):
                    duration_ms = (time.time() - start_time) * 1000
                    return FileOperationResult(
                        False, file_path, "delete", duration_ms, error="File not found"
                    )
                
                await aiofiles.os.remove(path)
                duration_ms = (time.time() - start_time) * 1000
                
                log.info(f"File deleted successfully", 
                        file=file_path,
                        duration_ms=duration_ms)
                
                return FileOperationResult(
                    True, file_path, "delete", duration_ms
                )
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return FileOperationResult(
                    False, file_path, "delete", duration_ms, error=str(e)
                )

    async def file_exists(self, file_path: str) -> bool:
        """Verifica se arquivo existe de forma assíncrona"""
        path = self._get_full_path(file_path)
        return await aiofiles.os.path.isfile(path)

    async def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Retorna estatísticas do arquivo"""
        path = self._get_full_path(file_path)
        try:
            stat = await aiofiles.os.stat(path)
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'exists': True
            }
        except FileNotFoundError:
            return {'exists': False}

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        return {
            'total_operations': self.operation_count,
            'bytes_written': self.total_bytes_written,
            'bytes_read': self.total_bytes_read,
            'max_concurrent': self.max_concurrent_ops,
            'workspace': str(self.workspace_path)
        }

    async def close(self):
        """Limpa recursos"""
        self.thread_pool.shutdown(wait=True)
        log.info("AsyncFileService closed")

    # Compatibilidade com interface anterior
    async def save_file(self, file_path: str, content: str) -> FileOperationResult:
        """Alias para write_file"""
        return await self.write_file(file_path, content)