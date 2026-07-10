"""Structured logger factory."""

from __future__ import annotations

from pathlib import Path

from config.settings import LoggingSettings
from platform_logging.context import LogContext, new_correlation_id
from platform_logging.filters import ContextLogFilter, LevelLogFilter
from platform_logging.formatters import ConsoleLogFormatter, JsonLogFormatter
from platform_logging.handlers import ConsoleLogHandler, FileLogHandler
from platform_logging.logger import ContextLogger, StructuredLogger


def create_logger(
    settings: LoggingSettings,
    *,
    service_name: str | None = None,
) -> StructuredLogger:
    """Create a structured logger from configuration."""
    formatter = JsonLogFormatter() if settings.format == "json" else ConsoleLogFormatter()
    handlers: list[ConsoleLogHandler | FileLogHandler] = []
    if settings.console_enabled:
        handlers.append(ConsoleLogHandler())
    if settings.file_path is not None:
        handlers.append(FileLogHandler(Path(settings.file_path)))

    filters: list[LevelLogFilter | ContextLogFilter] = [LevelLogFilter(settings.level)]
    if settings.include_correlation_id:
        filters.append(ContextLogFilter(require_correlation_id=False))

    context = LogContext(
        correlation_id=new_correlation_id() if settings.include_correlation_id else None,
        trace_id=new_correlation_id() if settings.include_trace_id else None,
        request_id=new_correlation_id() if settings.include_request_id else None,
        service_name=service_name,
    )
    return ContextLogger(
        formatter=formatter,
        handlers=tuple(handlers),
        filters=tuple(filters),
        default_context=context,
    )
