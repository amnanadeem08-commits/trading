"""Structured log formatters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from platform_logging.context import LogContext, get_log_context


@dataclass(frozen=True)
class LogRecord:
    """Structured log record."""

    level: str
    message: str
    timestamp: datetime
    fields: dict[str, Any]
    context: LogContext | None = None


class LogFormatter(ABC):
    """Interface for formatting log records."""

    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """Format a log record as a string."""


class JsonLogFormatter(LogFormatter):
    """JSON structured log formatter."""

    def format(self, record: LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": record.timestamp.astimezone(UTC).isoformat(),
            "level": record.level,
            "message": record.message,
            **record.fields,
        }
        context = record.context or get_log_context()
        if context is not None:
            payload.update(context.as_dict())
        return json.dumps(payload, default=str)


class ConsoleLogFormatter(LogFormatter):
    """Human-readable console log formatter."""

    def format(self, record: LogRecord) -> str:
        timestamp = record.timestamp.astimezone(UTC).isoformat()
        context = record.context or get_log_context()
        context_suffix = ""
        if context is not None and context.as_dict():
            context_suffix = f" {context.as_dict()}"
        return f"{timestamp} [{record.level}] {record.message}{context_suffix}"
