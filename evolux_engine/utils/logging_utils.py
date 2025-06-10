# evolux-engine/utils/logging_utils.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(
    log_level=logging.INFO,
    log_file="logs/evolux_engine.log",
    max_bytes=10*1024*1024, # 10 MB
    backup_count=5
):
    """Configura o logging para a aplicação."""

    # Garante que o diretório de logs exista
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Obter o logger raiz ou um logger específico da aplicação
    # Usar um logger nomeado é geralmente uma boa prática para bibliotecas/aplicações maiores
    logger = logging.getLogger("evolux_engine") # <- Pode ser logging.getLogger() para o root logger
                                             # ou um nome específico para seu app/engine
    if logger.hasHandlers(): # Evita adicionar handlers múltiplos se a função for chamada mais de uma vez
        logger.handlers.clear()

    logger.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)-25s %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    ) # Adicionei %(name) para ver qual logger está emitindo a msg

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Rotativo)
    try:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Se houver problema ao criar o file handler (ex: permissão), logue no console.
        console_handler.handle(
            logging.LogRecord(
                name="logging_setup",
                level=logging.ERROR,
                pathname=__file__,
                lineno=0, # Não é super preciso, mas ok
                msg=f"Falha ao configurar o file handler para {log_file}: {e}",
                args=(),
                exc_info=None,
                func="setup_logging"
            )
        )


    # Se você está usando getLogger() para o root logger e quer que bibliotecas usem o seu logging level
    # logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])
    # Mas como estamos configurando um logger nomeado ('evolux_engine'), isso é mais limpo.
    # Qualquer módulo que faça `logging.getLogger('evolux_engine.submodule')` ou
    # `logging.getLogger(__name__)` (se __name__ for 'evolux_engine.core.agent' por exemplo)
    # usará essa configuração.

    # Se você quiser que o logger raiz também seja afetado (para logs de bibliotecas de terceiros)
    # você pode configurar logging.basicConfig ou obter o root logger e adicionar handlers a ele.
    # Por enquanto, focar no logger da aplicação 'evolux_engine'.

    # Log inicial para confirmar que o logging foi configurado
    logger.info("Logging configurado pela logging_utils.")

    # Não é estritamente necessário retornar o logger se você sempre usa
    # logging.getLogger('evolux_engine') ou logging.getLogger(__name__) em outros lugares,
    # mas pode ser útil.
    return logger
