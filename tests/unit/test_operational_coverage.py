"""Additional unit tests for operational coverage."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from health import HealthRegistry, HealthState
from health.models import DependencyStatus
from platform_logging.formatters import ConsoleLogFormatter, LogRecord
from platform_logging.handlers import FileLogHandler


@pytest.mark.unit
def test_health_registry_dependency_and_failing_check() -> None:
    registry = HealthRegistry()

    def failing_check() -> tuple[HealthState, str]:
        raise RuntimeError("connection refused")

    registry.register("database", failing_check)
    registry.register_dependency(
        DependencyStatus(name="postgres", state=HealthState.HEALTHY, message="ok")
    )
    results = registry.check_all()
    assert results[0].state == HealthState.UNHEALTHY
    assert registry.dependency_status("postgres") is not None


@pytest.mark.unit
def test_file_log_handler_appends_record() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "app.log"
        handler = FileLogHandler(path)
        handler.emit('{"message":"test"}')
        content = path.read_text(encoding="utf-8")
        assert "test" in content


@pytest.mark.unit
def test_console_log_formatter_renders_text() -> None:
    record = LogRecord(
        level="INFO",
        message="ready",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        fields={},
    )
    rendered = ConsoleLogFormatter().format(record)
    assert "ready" in rendered
