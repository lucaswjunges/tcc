# evolux_engine/utils/logging_utils.py
import logging
from pythonjsonlogger import jsonlogger

def get_structured_logger(name):
    """
    Creates and returns a logger with structured JSON output.
    
    Args:
        name (str): The name of the logger, typically the module name.
    
    Returns:
        logging.Logger: A configured logger instance with JSON formatting.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evita duplicar handlers se o logger já foi configurado
    if not logger.handlers:
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        
    return logger
