"""Structured log filters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_logging.formatters import LogRecord


class LogFilter(ABC):
    """Interface for filtering log records."""

    @abstractmethod
    def allow(self, record: LogRecord) -> bool:
        """Return whether the record should be emitted."""


class LevelLogFilter(LogFilter):
    """Filter records below a minimum level."""

    _LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def __init__(self, min_level: str) -> None:
        normalized = min_level.upper()
        if normalized not in self._LEVELS:
            msg = f"Invalid log level: {min_level}"
            raise ValueError(msg)
        self._min_index = self._LEVELS.index(normalized)

    def allow(self, record: LogRecord) -> bool:
        try:
            index = self._LEVELS.index(record.level.upper())
        except ValueError:
            return True
        return index >= self._min_index


class ContextLogFilter(LogFilter):
    """Filter records that lack required context fields."""

    def __init__(self, *, require_correlation_id: bool = False) -> None:
        self._require_correlation_id = require_correlation_id

    def allow(self, record: LogRecord) -> bool:
        if not self._require_correlation_id:
            return True
        if record.context is None:
            return False
        return record.context.correlation_id is not None
