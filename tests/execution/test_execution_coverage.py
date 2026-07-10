"""Coverage tests for execution layer edge cases."""

from __future__ import annotations

import pytest

from execution import ExecutionRegistry, ExecutionState
from execution.exceptions import (
    DispatchError,
    ExecutionNotFoundError,
    ExecutionRegistrationError,
    ExecutionStateError,
    OrchestrationError,
    QueueError,
    ValidationError,
)
from execution.registry.execution_registry import ExecutionRegistry as Registry
from execution.versioning.execution_version import ExecutionVersion
from tests.execution_helpers import make_engine_metadata
from versioning.strategy_registry import reset_strategy_registry


def test_registry_empty_engine_id_raises() -> None:
    registry = ExecutionRegistry()
    metadata = make_engine_metadata(engine_id="   ")
    with pytest.raises(ExecutionRegistrationError):
        registry.register(metadata)


def test_registry_execution_not_found() -> None:
    registry = Registry()
    with pytest.raises(ExecutionNotFoundError):
        registry.get_execution_state("missing")


def test_registry_set_execution_state_not_found() -> None:
    registry = Registry()
    with pytest.raises(ExecutionNotFoundError):
        registry.set_execution_state("missing", ExecutionState.FAILED)


def test_registry_get_version_not_found() -> None:
    registry = Registry()
    with pytest.raises(ExecutionNotFoundError):
        registry.get_version("missing")


def test_exception_types() -> None:
    assert ExecutionNotFoundError("id").execution_id == "id"
    assert ExecutionStateError("id", "created", "cancel").operation == "cancel"
    assert isinstance(ValidationError("bad"), Exception)
    assert isinstance(DispatchError("bad"), Exception)
    assert isinstance(QueueError("bad"), Exception)
    assert isinstance(OrchestrationError("bad"), Exception)


def test_validator_version_incompatible() -> None:
    reset_strategy_registry()
    from execution.validation.execution_validator import ExecutionValidator

    version = ExecutionVersion(execution_id="exec-1", version_id="9.9.9")
    version.register(set_current=False)
    validator = ExecutionValidator(version=version)
    from tests.execution_helpers import make_execution_context

    result = validator.validate(
        execution_id="exec-1",
        risk_result=None,
        context=make_execution_context(),
        require_core_context=False,
    )
    assert result.version_compatible is False
