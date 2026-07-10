"""Structured logger interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from platform_logging.context import LogContext, get_log_context
from platform_logging.filters import LogFilter
from platform_logging.formatters import LogFormatter, LogRecord
from platform_logging.handlers import LogHandler


class StructuredLogger(ABC):
    """Interface for structured logging."""

    @abstractmethod
    def log(self, level: str, message: str, **fields: Any) -> None:
        """Emit a structured log record."""

    def debug(self, message: str, **fields: Any) -> None:
        self.log("DEBUG", message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self.log("INFO", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self.log("WARNING", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self.log("ERROR", message, **fields)


class ContextLogger(StructuredLogger):
    """Structured logger with formatter, filters, and handlers."""

    def __init__(
        self,
        *,
        formatter: LogFormatter,
        handlers: tuple[LogHandler, ...],
        filters: tuple[LogFilter, ...] = (),
        default_context: LogContext | None = None,
    ) -> None:
        self._formatter = formatter
        self._handlers = handlers
        self._filters = filters
        self._default_context = default_context

    def log(self, level: str, message: str, **fields: Any) -> None:
        record = LogRecord(
            level=level.upper(),
            message=message,
            timestamp=datetime.now(UTC),
            fields=fields,
            context=get_log_context() or self._default_context,
        )
        if not all(log_filter.allow(record) for log_filter in self._filters):
            return
        formatted = self._formatter.format(record)
        for handler in self._handlers:
            handler.emit(formatted)
