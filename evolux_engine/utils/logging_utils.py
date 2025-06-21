import sys
import os
from typing import Optional

from loguru import logger

# Não precisamos de uma variável global 'log' como antes,
# pois o `logger` importado de `loguru` já é globalmente acessível e configurável.
# No entanto, se você quiser um logger nomeado específico para seu engine,
# você pode obtê-lo assim, mas geralmente não é necessário com Loguru
# se você configurar o logger padrão corretamente.
# evolux_logger = logger.bind(name="evolux_engine")


def setup_logging(
    level: str = "INFO",
    sink_console: bool = True,
    console_format: Optional[str] = None,
    sink_file: bool = False, # Desabilitado por padrão, pode ser habilitado via config
    file_path: Optional[str] = "logs/evolux_engine.log",
    file_level: str = "DEBUG",
    file_rotation: str = "10 MB",
    file_retention: str = "7 days",
    file_format: Optional[str] = None,
    serialize_json: bool = False, # Para logs em JSON no arquivo, se desejado
):
    """
    Configura o Loguru para logging. Remove handlers existentes e adiciona novos.

    Args:
        level (str): Nível de log para o console (e padrão). Ex: "DEBUG", "INFO".
        sink_console (bool): Se True, adiciona um handler para o console (stderr).
        console_format (Optional[str]): Formato customizado para o console.
                                         Se None, usa um formato padrão com cores.
        sink_file (bool): Se True, adiciona um handler para logging em arquivo.
        file_path (Optional[str]): Caminho para o arquivo de log.
        file_level (str): Nível de log para o arquivo.
        file_rotation (str): Condição para rotacionar o arquivo (ex: "10 MB", "1 week").
        file_retention (str): Período para manter os arquivos de log rotacionados.
        file_format (Optional[str]): Formato customizado para o arquivo.
                                     Se None, usa um formato padrão.
        serialize_json (bool): Se True e sink_file for True, os logs no arquivo
                               serão serializados como JSON.
    """
    logger.remove()  # Remove todos os handlers previamente configurados

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
            colorize=True,  # Habilita cores no console
            diagnose=True, # Mostra variáveis em exceções por padrão
            catch=True    # Captura exceções não tratadas e as loga (cuidado em produção)
        )

    if sink_file and file_path:
        # Garante que o diretório do log exista
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"Não foi possível criar o diretório de log '{os.path.dirname(file_path)}': {e}. Logging em arquivo desabilitado.")
            sink_file = False # Desabilita se não puder criar

    if sink_file and file_path: # Verifica novamente caso tenha sido desabilitado acima
        default_file_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        logger.add(
            file_path,
            level=file_level.upper(),
            rotation=file_rotation,
            retention=file_retention,
            format=file_format or default_file_format,
            encoding="utf-8",
            serialize=serialize_json, # Loga como JSON se True
            diagnose=True,
            catch=True
        )

    logger.info(f"Logging configurado. Nível Console: {level.upper() if sink_console else 'DESABILITADO'}. "
                f"Nível Arquivo: {file_level.upper() if sink_file else 'DESABILITADO'}.")

# Como usar em outros módulos:
# from loguru import logger # Importar diretamente o logger do loguru
#
# # Você chamaria setup_logging() uma vez no início da sua aplicação (ex: em run.py)
# # setup_logging(level="DEBUG", sink_file=True, file_path="meu_app.log")
#
# def minha_funcao():
#     logger.info("Esta é uma mensagem de info.", dado_extra="valor")
#     logger.debug("Detalhes para depuração.")
#     try:
#         x = 1 / 0
#     except ZeroDivisionError:
#         logger.exception("Ocorreu um erro!") # Loga a exceção com traceback
#
# logger.warning("Isso é um aviso fora de qualquer função específica.")
