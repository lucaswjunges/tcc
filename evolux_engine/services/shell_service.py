import subprocess
import shlex
from pathlib import Path
from .observability_service import get_logger

log = get_logger("shell_service")

class ShellService:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        if not self.workspace_path.is_dir():
            log.error("Workspace path does not exist or is not a directory.", path=workspace_path)
            raise FileNotFoundError(f"Workspace path not found: {workspace_path}")
        log.info(f"ShellService initialized for workspace: {self.workspace_path.resolve()}")

    def run_shell_command(self, command: str, timeout: int = 120) -> str:
        """
        Executes a shell command inside the project's workspace.

        Args:
            command: The command to execute.
            timeout: The timeout for the command in seconds.

        Returns:
            A string containing the combined stdout and stderr of the command.
        """
        log.info(f"Executing shell command: '{command}'", workspace=str(self.workspace_path))

        try:
            # shlex.split is safer as it handles arguments correctly
            args = shlex.split(command)
            
            # Execute o comando
            result = subprocess.run(
                args,
                cwd=self.workspace_path,  # **CRITICAL SECURITY BOUNDARY**
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # We will check the return code manually
            )

            # Combine stdout and stderr for a complete log
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

            if result.returncode == 0:
                log.info(f"Command '{command}' executed successfully.", return_code=result.returncode)
            else:
                log.warn(f"Command '{command}' failed.", return_code=result.returncode, output=output)

            return output

        except FileNotFoundError:
            error_msg = f"Error: Command '{args[0]}' not found. Make sure it's installed and in the system's PATH."
            log.error(error_msg)
            return error_msg
        except subprocess.TimeoutExpired:
            error_msg = f"Error: Command '{command}' timed out after {timeout} seconds."
            log.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred while executing command '{command}': {str(e)}"
            log.error(error_msg, exc_info=True)
            return error_msg

