import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from evolux_engine.utils.logging_utils import get_structured_logger

logger = get_structured_logger("backup_system")

@dataclass
class BackupManifest:
    """Manifesto de um backup contendo metadados"""
    backup_id: str
    project_id: str
    created_at: datetime
    project_status: str
    total_files: int
    backup_size_bytes: int
    backup_path: str
    description: Optional[str] = None

class BackupSystem:
    """
    Sistema de backup para snapshots do projeto conforme especificação.
    Implementa backup/restore de contexto e artefatos.
    """
    
    def __init__(self, base_backup_dir: str = "./project_workspaces/backups"):
        self.backup_dir = Path(base_backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info("BackupSystem initialized", backup_dir=str(self.backup_dir))
    
    def create_snapshot(self, project_context, artifacts_dir: str, description: str = None) -> str:
        """
        Cria snapshot completo do projeto (contexto + artefatos).
        
        Args:
            project_context: Instância do ProjectContext
            artifacts_dir: Caminho para diretório de artefatos
            description: Descrição opcional do backup
            
        Returns:
            Caminho para o arquivo de backup criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{project_context.project_id}_{timestamp}"
        backup_file = self.backup_dir / f"{backup_id}.zip"
        
        logger.info("Creating project snapshot", 
                   project_id=project_context.project_id,
                   backup_id=backup_id)
        
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 1. Backup do contexto (context.json)
                context_data = project_context.model_dump_json(indent=2)
                backup_zip.writestr("context.json", context_data)
                
                # 2. Backup dos artefatos
                artifacts_path = Path(artifacts_dir)
                if artifacts_path.exists():
                    for file_path in artifacts_path.rglob("*"):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(artifacts_path)
                            backup_zip.write(file_path, f"artifacts/{relative_path}")
                
                # 3. Backup de logs se existirem
                logs_dir = Path(project_context.workspace_path) / "logs"
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        backup_zip.write(log_file, f"logs/{log_file.name}")
                
                # 4. Criar manifesto do backup
                manifest = BackupManifest(
                    backup_id=backup_id,
                    project_id=project_context.project_id,
                    created_at=datetime.now(),
                    project_status=project_context.status.value,
                    total_files=len(backup_zip.namelist()),
                    backup_size_bytes=0,  # Será atualizado após fechar o zip
                    backup_path=str(backup_file),
                    description=description
                )
                
                backup_zip.writestr("manifest.json", json.dumps(manifest.__dict__, default=str, indent=2))
            
            # Atualizar tamanho no manifesto
            backup_size = backup_file.stat().st_size
            manifest.backup_size_bytes = backup_size
            
            logger.info("Snapshot created successfully",
                       backup_file=str(backup_file),
                       size_mb=round(backup_size / 1024 / 1024, 2))
            
            return str(backup_file)
            
        except Exception as e:
            logger.error("Failed to create snapshot", error=str(e), exc_info=True)
            if backup_file.exists():
                backup_file.unlink()  # Cleanup on failure
            raise
    
    def restore_snapshot(self, backup_file: str, restore_dir: str) -> Dict[str, Any]:
        """
        Restaura snapshot do projeto.
        
        Args:
            backup_file: Caminho para arquivo de backup
            restore_dir: Diretório onde restaurar
            
        Returns:
            Dicionário com informações da restauração
        """
        backup_path = Path(backup_file)
        restore_path = Path(restore_dir)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        logger.info("Restoring snapshot", backup_file=backup_file, restore_dir=restore_dir)
        
        try:
            # Criar diretório de restauração
            restore_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Extrair todos os arquivos
                backup_zip.extractall(restore_path)
                
                # Ler manifesto se disponível
                manifest_data = {}
                if "manifest.json" in backup_zip.namelist():
                    manifest_content = backup_zip.read("manifest.json").decode('utf-8')
                    manifest_data = json.loads(manifest_content)
            
            restored_files = list(restore_path.rglob("*"))
            
            logger.info("Snapshot restored successfully",
                       restored_files=len(restored_files),
                       restore_path=str(restore_path))
            
            return {
                "success": True,
                "restored_files": len(restored_files),
                "restore_path": str(restore_path),
                "manifest": manifest_data
            }
            
        except Exception as e:
            logger.error("Failed to restore snapshot", error=str(e), exc_info=True)
            raise
    
    def list_backups(self, project_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """Lista backups disponíveis, opcionalmente filtrados por projeto"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                    if "manifest.json" in backup_zip.namelist():
                        manifest_content = backup_zip.read("manifest.json").decode('utf-8')
                        manifest_data = json.loads(manifest_content)
                        
                        # Filtrar por projeto se especificado
                        if project_id is None or manifest_data.get("project_id") == project_id:
                            manifest_data["backup_file"] = str(backup_file)
                            backups.append(manifest_data)
                    else:
                        # Backup sem manifesto, criar entrada básica
                        stat = backup_file.stat()
                        backups.append({
                            "backup_id": backup_file.stem,
                            "project_id": "unknown",
                            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "backup_size_bytes": stat.st_size,
                            "backup_file": str(backup_file)
                        })
                        
            except Exception as e:
                logger.warning("Could not read backup manifest", 
                              backup_file=str(backup_file), 
                              error=str(e))
        
        # Ordenar por data de criação (mais recente primeiro)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return backups
    
    def cleanup_old_backups(self, project_id: str, keep_count: int = 5) -> int:
        """
        Remove backups antigos, mantendo apenas os mais recentes.
        
        Args:
            project_id: ID do projeto
            keep_count: Número de backups a manter
            
        Returns:
            Número de backups removidos
        """
        project_backups = self.list_backups(project_id)
        
        if len(project_backups) <= keep_count:
            return 0
        
        backups_to_remove = project_backups[keep_count:]
        removed_count = 0
        
        for backup in backups_to_remove:
            try:
                backup_path = Path(backup["backup_file"])
                if backup_path.exists():
                    backup_path.unlink()
                    removed_count += 1
                    logger.info("Old backup removed", backup_file=str(backup_path))
            except Exception as e:
                logger.error("Failed to remove old backup", 
                           backup_file=backup.get("backup_file"), 
                           error=str(e))
        
        return removed_count