import sys
import os
from typing import Optional

from loguru import logger

def setup_logging(
    level: str = "INFO",
    sink_console: bool = True,
    console_format: Optional[str] = None,
    sink_file: bool = False,
    file_path: Optional[str] = "logs/evolux_engine.log",
    file_level: str = "DEBUG",
    file_rotation: str = "10 MB",
    file_retention: str = "7 days",
    file_format: Optional[str] = None,
    serialize_json: bool = False,
):
    """
    Configura o Loguru para logging. Remove handlers existentes e adiciona novos.
    """
    logger.remove()

    if sink_console:
        default_console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            sys.stderr,
            level=level.upper(),
            format=console_format or default_console_format,
            colorize=True,
            diagnose=True, # Melhor para debug e tracebacks
            catch=True # Captura exceções não tratadas (cuidado em produção)
        )

    if sink_file and file_path:
        try:
            log_dir = os.path.dirname(file_path)
            if log_dir: # Evita erro se file_path for apenas um nome de arquivo no diretório atual
                os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            # Usar o logger Loguru aqui pode ainda não estar totalmente configurado se este for o primeiro uso.
            # Um print pode ser mais seguro para este erro específico de setup.
            print(f"ALERTA DE LOGGING: Não foi possível criar o diretório de log '{os.path.dirname(file_path)}': {e}. Logging em arquivo desabilitado.")
            # Loguru ainda não terá o handler de console se sink_console=False e este for o primeiro log.
            # logger.warning(...) pode não aparecer.
            sink_file = False

    if sink_file and file_path:
        default_file_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}.{function}:{line} | {message}"
        # Adicionar um patcher para incluir component nos logs de arquivo, se desejado
        # def component_patcher(record):
        #     record["extra"]["component"] = record["extra"].get("component", "N/A")
        # logger = logger.patch(component_patcher)

        logger.add(
            file_path,
            level=file_level.upper(),
            rotation=file_rotation,
            retention=file_retention,
            format=file_format or default_file_format,
            encoding="utf-8",
            serialize=serialize_json,
            diagnose=True, # Bom para arquivos também
            catch=True
        )

    # Log inicial para confirmar que o setup foi chamado.
    # Este logger.info usará os handlers que acabaram de ser adicionados.
    logger.info(f"Logging configurado. Nível Console: {level.upper() if sink_console else 'DESABILITADO'}. "
                f"Nível Arquivo: {file_level.upper() if sink_file and file_path else 'DESABILITADO'}.")

