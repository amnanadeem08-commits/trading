"""Structured logging scaffolds."""

from platform_logging.context import (
    LogContext,
    clear_log_context,
    get_log_context,
    new_correlation_id,
    set_log_context,
)
from platform_logging.factory import create_logger
from platform_logging.filters import ContextLogFilter, LevelLogFilter, LogFilter
from platform_logging.formatters import (
    ConsoleLogFormatter,
    JsonLogFormatter,
    LogFormatter,
    LogRecord,
)
from platform_logging.handlers import ConsoleLogHandler, FileLogHandler, LogHandler
from platform_logging.logger import ContextLogger, StructuredLogger

__all__ = [
    "ConsoleLogFormatter",
    "ConsoleLogHandler",
    "ContextLogFilter",
    "ContextLogger",
    "FileLogHandler",
    "JsonLogFormatter",
    "LevelLogFilter",
    "LogContext",
    "LogFilter",
    "LogFormatter",
    "LogHandler",
    "LogRecord",
    "StructuredLogger",
    "clear_log_context",
    "create_logger",
    "get_log_context",
    "new_correlation_id",
    "set_log_context",
]
