import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.types import FilteringBoundLogger

# Configure the global logger with type hints
log: FilteringBoundLogger = structlog.get_logger("evolux_engine")

def init_logging(log_dir: str, console_level: str = "INFO", file_level: str = "DEBUG") -> None:
    """
    Initialize structured logging for the application with enhanced configuration.
    
    Args:
        log_dir: Directory where log files will be stored
        console_level: Minimum log level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_level: Minimum log level for file output
    """
    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / "events.log"

        # Configure structlog first
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(sort_keys=True),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure Python's built-in logging
        root_logger = logging.getLogger()
        
        # Clear any existing handlers to prevent duplication
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Set the overall minimum level for the root logger
        min_level = min(getattr(logging, console_level.upper()), getattr(logging, file_level.upper()))
        root_logger.setLevel(min_level)

        # Create and configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level.upper())
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Create and configure file handler for JSON logs
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(file_level.upper())
        # The JSONRenderer from structlog will format the file logs, so no formatter is needed here.
        root_logger.addHandler(file_handler)

        # Get a logger instance after configuration
        logger = structlog.get_logger("evolux_engine.init")
        logger.info(
            "Logging system initialized",
            log_file=str(log_file),
            console_level=console_level,
            file_level=file_level
        )

    except Exception as e:
        # Use a basic print for critical errors during logging setup
        print(f"Failed to initialize logging: {str(e)}", file=sys.stderr)
        raise

def get_logger(name: Optional[str] = None) -> FilteringBoundLogger:
    """Get a named logger instance with proper type hints"""
    return structlog.get_logger(name or "evolux_engine")
