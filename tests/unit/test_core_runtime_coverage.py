"""Additional core runtime coverage tests."""

from __future__ import annotations

import pytest

from config.settings import CoreSettings
from core import CoreContextError, CoreRuntime, reset_core_runtime
from pipeline import build_pipeline_context
from services import reset_application_context


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_core_runtime()
    yield
    reset_application_context()
    reset_core_runtime()


@pytest.mark.unit
def test_runtime_build_context_disabled_raises() -> None:
    settings = CoreSettings(context_enabled=False)
    runtime = CoreRuntime(context=build_pipeline_context(), settings=settings)
    runtime.initialize()
    with pytest.raises(CoreContextError):
        runtime.build_context(operation_type="disabled")


@pytest.mark.unit
def test_runtime_shutdown_without_initialize_is_noop() -> None:
    runtime = CoreRuntime()
    runtime.shutdown()
    assert runtime.active_context is None


@pytest.mark.unit
def test_runtime_health_check_uninitialized() -> None:
    from health.models import HealthState

    runtime = CoreRuntime()
    runtime.initialize()
    runtime._active_context = None
    state, message = runtime._health_check()
    assert state == HealthState.UNHEALTHY
    assert "not initialized" in message


@pytest.mark.unit
def test_runtime_audit_hook_records_action() -> None:
    settings = CoreSettings(audit_enabled=True)
    runtime = CoreRuntime(context=build_pipeline_context(), settings=settings)
    context = runtime.initialize()
    assert context.audit.attributes["action_recorded"] == "runtime_initialize"
