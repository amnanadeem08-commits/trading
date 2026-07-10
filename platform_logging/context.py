"""Structured log context with correlation, trace, and request identifiers."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, replace
from uuid import uuid4

_log_context: ContextVar[LogContext | None] = ContextVar("log_context", default=None)


@dataclass(frozen=True)
class LogContext:
    """Immutable structured logging context."""

    correlation_id: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    service_name: str | None = None

    def with_correlation_id(self, correlation_id: str) -> LogContext:
        return replace(self, correlation_id=correlation_id)

    def with_trace_id(self, trace_id: str) -> LogContext:
        return replace(self, trace_id=trace_id)

    def with_request_id(self, request_id: str) -> LogContext:
        return replace(self, request_id=request_id)

    def as_dict(self) -> dict[str, str]:
        fields: dict[str, str] = {}
        if self.correlation_id is not None:
            fields["correlation_id"] = self.correlation_id
        if self.trace_id is not None:
            fields["trace_id"] = self.trace_id
        if self.request_id is not None:
            fields["request_id"] = self.request_id
        if self.service_name is not None:
            fields["service_name"] = self.service_name
        return fields


def new_correlation_id() -> str:
    return str(uuid4())


def get_log_context() -> LogContext | None:
    return _log_context.get()


def set_log_context(context: LogContext) -> None:
    _log_context.set(context)


def clear_log_context() -> None:
    _log_context.set(None)
