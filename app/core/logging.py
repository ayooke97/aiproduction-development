import logging
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import json
from datetime import datetime

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO


class JsonFormatter(logging.Formatter):
    """Formatter for JSON-structured logs."""
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        validate: bool = True,
        *,
        defaults: Optional[Dict[str, Any]] = None
    ):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format LogRecord as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "thread": record.thread
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging(
    name: str = "bpk_api",
    log_file: Optional[str] = "bpk_api.log",
    level: int = LOG_LEVEL,
    json_format: bool = False
) -> logging.Logger:
    """
    Set up logging with the given name and level.
    
    Args:
        name: Logger name
        log_file: Path to log file (None for no file logging)
        level: Logging level
        json_format: Whether to format logs as JSON
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    If the logger doesn't exist, create it.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    # Check if logger exists
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logging(name)
    
    return logger