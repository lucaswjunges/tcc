# src/services/toolbelt.py

import subprocess
import os
from dataclasses import dataclass
from src.services.observability_service import log

@dataclass
class ShellCommandResult:
    """Estrutura para conter o resultado de um comando de shell."""
    return_code: int
    stdout: str
    stderr: str
    
    def was_successful(self) -> bool:
        return self.return_code == 0

class Toolbelt:
    """
    Fornece ao agente um conjunto de ferramentas para interagir com o sistema.
    Cada ferramenta deve ser segura e operar dentro do workspace do projeto.
    """
    def __init__(self, project_workspace_path: str):
        if not os.path.exists(project_workspace_path) or not os.path.isdir(project_workspace_path):
            raise ValueError(f"Project workspace path does not exist or is not a directory: {project_workspace_path}")
        self.workspace_path = project_workspace_path
        log.info("Toolbelt initialized.", workspace=self.workspace_path)

    def run_shell_command(self, command: str) -> ShellCommandResult:
        """
        Executa um comando shell dentro do diretório de trabalho do projeto.
        
        IMPORTANTE: Esta é uma função poderosa. A segurança é garantida
        pelo fato de que o agente só deve operar dentro de seu workspace.
        """
        log.info(f"Executing shell command: `{command}`", workspace=self.workspace_path)
        
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=300  # Timeout de 5 minutos para comandos longos (como instalações)
            )
            
            result = ShellCommandResult(
                return_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr
            )
            
            if result.was_successful():
                log.info(f"Command `{command}` executed successfully.", stdout=result.stdout[:200]) # Log p/ evitar poluição
            else:
                log.error(
                    f"Command `{command}` failed.",
                    return_code=result.return_code,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            return result

        except FileNotFoundError:
            # Isso acontece se o comando em si não for encontrado, e.g., 'pip' não está no PATH
            log.error(f"Command not found: {command.split()[0]}", exc_info=True)
            return ShellCommandResult(return_code=-1, stdout="", stderr=f"Command not found: {command}")
        except subprocess.TimeoutExpired:
            log.error(f"Command timed out: `{command}`", exc_info=True)
            return ShellCommandResult(return_code=-2, stdout="", stderr="Command timed out after 300 seconds.")
        except Exception as e:
            log.critical("An unexpected error occurred while running shell command.", command=command, error=str(e), exc_info=True)
            return ShellCommandResult(return_code=-3, stdout="", stderr=f"An unexpected error occurred: {e}")
