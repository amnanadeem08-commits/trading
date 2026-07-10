"""Unit tests for structured logging scaffolds."""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime

import pytest

from platform_logging.context import LogContext, new_correlation_id
from platform_logging.filters import ContextLogFilter, LevelLogFilter
from platform_logging.formatters import JsonLogFormatter, LogRecord
from platform_logging.handlers import ConsoleLogHandler


@pytest.mark.unit
def test_log_context_fields() -> None:
    context = LogContext(correlation_id="c1", trace_id="t1", request_id="r1")
    assert context.as_dict() == {
        "correlation_id": "c1",
        "trace_id": "t1",
        "request_id": "r1",
    }


@pytest.mark.unit
def test_json_formatter_outputs_json() -> None:
    record = LogRecord(
        level="INFO",
        message="hello",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        fields={"key": "value"},
        context=LogContext(correlation_id="abc"),
    )
    payload = json.loads(JsonLogFormatter().format(record))
    assert payload["message"] == "hello"
    assert payload["correlation_id"] == "abc"


@pytest.mark.unit
def test_level_filter_blocks_debug() -> None:
    record = LogRecord(
        level="DEBUG",
        message="hidden",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        fields={},
    )
    assert LevelLogFilter("INFO").allow(record) is False


@pytest.mark.unit
def test_context_logger_emits_to_stream() -> None:
    from platform_logging.logger import ContextLogger

    stream = io.StringIO()
    logger = ContextLogger(
        formatter=JsonLogFormatter(),
        handlers=(ConsoleLogHandler(stream=stream),),
        filters=(LevelLogFilter("INFO"),),
        default_context=LogContext(correlation_id=new_correlation_id()),
    )
    logger.info("event", component="health")
    output = stream.getvalue()
    assert "event" in output


@pytest.mark.unit
def test_context_filter_requires_correlation_id() -> None:
    record = LogRecord(
        level="INFO",
        message="x",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        fields={},
    )
    assert ContextLogFilter(require_correlation_id=True).allow(record) is False
