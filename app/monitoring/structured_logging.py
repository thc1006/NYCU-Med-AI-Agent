"""
Structured logging system for Taiwan Medical AI Assistant.
Provides JSON-structured logging with correlation IDs and PDPA compliance.
"""

import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
import os
import sys


class StructuredLogger:
    """JSON-structured logger with correlation ID support."""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

        # Thread-local storage for correlation ID
        self._thread_local = threading.local()

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread."""
        self._thread_local.correlation_id = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread."""
        return getattr(self._thread_local, 'correlation_id', None)

    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal logging method with structured data."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': logging.getLevelName(level),
            'message': message,
            'correlation_id': self.get_correlation_id(),
            'thread_id': threading.get_ident(),
            'process_id': os.getpid()
        }

        if extra:
            # Ensure no PII in logs
            sanitized_extra = self._sanitize_data(extra)
            log_data.update(sanitized_extra)

        self.logger.log(level, json.dumps(log_data, ensure_ascii=False))

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or hash potential PII from log data."""
        sanitized = {}

        for key, value in data.items():
            if key.lower() in ['password', 'token', 'key', 'secret', 'symptom_text', 'phone', 'email']:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 10:
                # Hash long strings that might contain PII
                import hashlib
                sanitized[f"{key}_hash"] = hashlib.sha256(value.encode()).hexdigest()[:8]
            else:
                sanitized[key] = value

        return sanitized

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, kwargs)

    @contextmanager
    def correlation_context(self, correlation_id: Optional[str] = None):
        """Context manager for correlation ID."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        old_correlation_id = self.get_correlation_id()
        self.set_correlation_id(correlation_id)

        try:
            yield correlation_id
        finally:
            if old_correlation_id:
                self.set_correlation_id(old_correlation_id)
            else:
                self._thread_local.correlation_id = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record):
        """Format log record as JSON."""
        # If the message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # Not JSON, create structured format
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }

            if hasattr(record, 'correlation_id'):
                log_data['correlation_id'] = record.correlation_id

            return json.dumps(log_data, ensure_ascii=False)


# Global structured logger instance
structured_logger = StructuredLogger("taiwan_medical_ai")


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def configure_logging(level: Union[str, int] = "INFO",
                     correlation_header: str = "X-Correlation-ID"):
    """Configure application-wide structured logging."""
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(handler)

    # Set correlation header name
    structured_logger.correlation_header = correlation_header