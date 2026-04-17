"""
Structured JSON Logging
Provides consistent, machine-readable log format for production monitoring
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback

class StructuredLogFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "sport_key"):
            log_data["sport_key"] = record.sport_key
        if hasattr(record, "event_id"):
            log_data["event_id"] = record.event_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith("_") and key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName"
            ]:
                try:
                    # Try to serialize value
                    json.dumps({key: value})
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data, default=str)

def setup_structured_logging(
    level: int = logging.INFO,
    enable_console: bool = True,
    enable_file: bool = False,
    file_path: Optional[str] = None
) -> logging.Logger:
    """
    Setup structured logging for the application
    """
    # Create formatter
    formatter = StructuredLogFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if enable_file and file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

class ContextualLogger:
    """
    Logger wrapper that adds context to all log messages
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        extra = kwargs.get("extra", {})
        extra.update(self.context)
        kwargs["extra"] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def with_context(self, **additional_context) -> "ContextualLogger":
        """Create new logger with additional context"""
        new_context = {**self.context, **additional_context}
        return ContextualLogger(self.logger, new_context)

def get_logger(name: str, **context) -> ContextualLogger:
    """Get a contextual logger"""
    logger = logging.getLogger(name)
    return ContextualLogger(logger, context)
