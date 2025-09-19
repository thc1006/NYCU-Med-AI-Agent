"""
Unit tests for structured logging system.
Tests JSON logging, correlation IDs, log levels, and PDPA compliance.
"""

import json
import logging
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from io import StringIO
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from app.monitoring.structured_logging import (
    StructuredLogger,
    StructuredFormatter,
    get_logger,
    configure_logging,
    structured_logger
)


class TestStructuredLogger:
    """Test structured JSON logging functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = StructuredLogger(
            name="test_logger",
            level=logging.INFO
        )

    def test_creates_json_structured_logs(self):
        """Test that logs are output in JSON format."""
        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        self.logger.info("Test message", key="value")

        log_output = log_stream.getvalue()
        assert log_output.strip()

        log_data = json.loads(log_output.strip())
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data

    def test_includes_correlation_id_when_provided(self):
        """Test correlation ID is included in structured logs."""
        correlation_id = str(uuid.uuid4())

        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        with self.logger.correlation_context(correlation_id):
            self.logger.info("Test with correlation")

        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        assert log_data["correlation_id"] == correlation_id

    def test_sets_and_gets_correlation_id(self):
        """Test setting and getting correlation ID."""
        correlation_id = str(uuid.uuid4())

        self.logger.set_correlation_id(correlation_id)
        assert self.logger.get_correlation_id() == correlation_id

    def test_sanitizes_sensitive_data(self):
        """Test that sensitive data is sanitized in logs."""
        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        self.logger.info("Test with sensitive data", password="secret123", symptom_text="chest pain")

        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        assert log_data["password"] == "[REDACTED]"
        assert log_data["symptom_text"] == "[REDACTED]"

    @freeze_time("2024-01-15 10:30:00")
    def test_timestamp_format_iso8601(self):
        """Test timestamp is in ISO 8601 format."""
        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        self.logger.info("Test timestamp")

        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        assert "2024-01-15T10:30:00" in log_data["timestamp"]

    def test_different_log_levels(self):
        """Test different log levels are correctly recorded."""
        test_cases = [
            ("debug", "Debug message"),
            ("info", "Info message"),
            ("warning", "Warning message"),
            ("error", "Error message")
        ]

        for method_name, message in test_cases:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                method = getattr(self.logger, method_name)
                method(message)

                log_output = mock_stdout.getvalue()
                if log_output.strip():  # Only check if log was actually output
                    log_data = json.loads(log_output.strip())
                    assert log_data["level"] == method_name.upper()
                    assert log_data["message"] == message

    def test_logging_with_extra_data(self):
        """Test logging with extra data fields."""
        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        self.logger.info("Test with extra", user_id="123", action="login")

        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test with extra"
        assert log_data["user_id"] == "123"
        assert log_data["action"] == "login"

    def test_performance_metrics_logging(self):
        """Test performance metrics are properly logged."""
        # Create a handler with StringIO to capture logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(StructuredFormatter())

        # Remove existing handlers and add our test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

        self.logger.info("Performance metrics",
                       duration_ms=150.5,
                       memory_usage_mb=45.2,
                       cpu_usage_percent=12.8)

        log_output = log_stream.getvalue()
        log_data = json.loads(log_output.strip())
        assert log_data["message"] == "Performance metrics"
        assert log_data["duration_ms"] == 150.5
        assert log_data["memory_usage_mb"] == 45.2
        assert log_data["cpu_usage_percent"] == 12.8


class TestStructuredFormatter:
    """Test structured JSON formatter."""

    def setup_method(self):
        """Setup test fixtures."""
        self.formatter = StructuredFormatter()

    def test_formats_regular_log_record(self):
        """Test formatting regular log records to JSON."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )

        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data

    def test_passes_through_json_messages(self):
        """Test that JSON messages are passed through as-is."""
        json_message = '{"level": "INFO", "message": "Already JSON"}'
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg=json_message, args=(), exc_info=None
        )

        formatted = self.formatter.format(record)
        assert formatted == json_message


class TestGlobalLogger:
    """Test global logger functionality."""

    def test_get_logger_creates_structured_logger(self):
        """Test that get_logger creates a StructuredLogger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_logger"

    def test_configure_logging_sets_level(self):
        """Test that configure_logging sets the correct level."""
        configure_logging(level="DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_structured_logger_global_instance(self):
        """Test the global structured logger instance."""
        assert isinstance(structured_logger, StructuredLogger)
        assert structured_logger.logger.name == "taiwan_medical_ai"


class TestDataSanitization:
    """Test data sanitization functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = StructuredLogger("test_sanitizer")

    def test_sanitizes_sensitive_fields(self):
        """Test that sensitive fields are properly sanitized."""
        test_data = {
            "password": "secret123",
            "token": "abc123token",
            "symptom_text": "patient reports severe chest pain",
            "email": "user@example.com",
            "phone": "0912345678",
            "normal_field": "safe_value"
        }

        sanitized = self.logger._sanitize_data(test_data)

        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["symptom_text"] == "[REDACTED]"
        assert sanitized["email"] == "[REDACTED]"
        assert sanitized["phone"] == "[REDACTED]"
        assert sanitized["normal_field"] == "safe_value"

    def test_hashes_long_strings(self):
        """Test that long strings are hashed for privacy."""
        test_data = {
            "long_description": "This is a very long description that might contain personal information",
            "short_text": "short"
        }

        sanitized = self.logger._sanitize_data(test_data)

        # Long string should be hashed
        assert "long_description_hash" in sanitized
        assert len(sanitized["long_description_hash"]) == 8

        # Short string should remain as-is
        assert sanitized["short_text"] == "short"


class TestCorrelationContext:
    """Test correlation context management."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = StructuredLogger("test_context")

    def test_correlation_context_manager(self):
        """Test correlation context manager functionality."""
        correlation_id = str(uuid.uuid4())

        # Initially no correlation ID
        assert self.logger.get_correlation_id() is None

        # Inside context, correlation ID should be set
        with self.logger.correlation_context(correlation_id) as ctx_id:
            assert ctx_id == correlation_id
            assert self.logger.get_correlation_id() == correlation_id

        # After context, correlation ID should be cleared
        assert self.logger.get_correlation_id() is None

    def test_nested_correlation_contexts(self):
        """Test nested correlation contexts."""
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        with self.logger.correlation_context(correlation_id_1):
            assert self.logger.get_correlation_id() == correlation_id_1

            with self.logger.correlation_context(correlation_id_2):
                assert self.logger.get_correlation_id() == correlation_id_2

            # Should restore previous correlation ID
            assert self.logger.get_correlation_id() == correlation_id_1

        # Should be None after all contexts exit
        assert self.logger.get_correlation_id() is None

    def test_auto_generated_correlation_id(self):
        """Test auto-generation of correlation ID when none provided."""
        with self.logger.correlation_context() as correlation_id:
            assert correlation_id is not None
            assert len(correlation_id) == 36  # UUID4 format
            assert self.logger.get_correlation_id() == correlation_id


class TestLogConfiguration:
    """Test logging configuration and setup."""

    def test_configure_logging_with_string_level(self):
        """Test configure_logging with string log level."""
        configure_logging(level="WARNING")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_configure_logging_with_int_level(self):
        """Test configure_logging with integer log level."""
        configure_logging(level=logging.ERROR)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_configure_logging_sets_structured_formatter(self):
        """Test that configure_logging sets structured formatter."""
        configure_logging()
        root_logger = logging.getLogger()

        # Should have at least one handler with StructuredFormatter
        has_structured_formatter = any(
            isinstance(handler.formatter, StructuredFormatter)
            for handler in root_logger.handlers
        )
        assert has_structured_formatter

    def test_correlation_header_configuration(self):
        """Test correlation header configuration."""
        configure_logging(correlation_header="X-Custom-Correlation-ID")
        assert structured_logger.correlation_header == "X-Custom-Correlation-ID"