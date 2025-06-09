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

        # Clear any existing handlers
        logging.getLogger().handlers.clear()

        # Configure Python's built-in logging
        logging.basicConfig(
            level=console_level,
            format="%(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),  # Console output
                logging.FileHandler(log_file)        # File output
            ]
        )

        # Enhanced structlog configuration
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(sort_keys=True)
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, file_level)
            ),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure separate log levels for different outputs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        root_logger = logging.getLogger()
        root_logger.setLevel(min(
            getattr(logging, console_level),
            getattr(logging, file_level)
        ))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        log.info(
            "Logging system initialized",
            log_file=str(log_file),
            console_level=console_level,
            file_level=file_level
        )

    except Exception as e:
        print(f"Failed to initialize logging: {str(e)}", file=sys.stderr)
        raise

def get_logger(name: Optional[str] = None) -> FilteringBoundLogger:
    """Get a named logger instance with proper type hints"""
    return structlog.get_logger(name or "evolux_engine")
