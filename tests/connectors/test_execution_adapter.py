"""Unit tests for execution adapter."""

from __future__ import annotations

import inspect

import pytest

from connectors import ExecutionAdapter
from connectors.adapters.adapter_metadata import AdapterState
from tests.connectors_helpers import (
    FailingExecutionAdapter,
    RejectingExecutionAdapter,
    SampleExecutionAdapter,
    make_adapter_context,
)


def test_execution_adapter_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionAdapter, predicate=inspect.isfunction)
    }
    assert "initialize" in methods
    assert "validate" in methods
    assert "dispatch" in methods
    assert "shutdown" in methods
    assert "health" in methods


def test_sample_adapter_lifecycle() -> None:
    adapter = SampleExecutionAdapter()
    context = make_adapter_context()
    adapter.initialize(context)
    assert adapter.validate(context) is True
    output = adapter.dispatch(context)
    assert output["prepared"] is True
    adapter.shutdown(context)
    health = adapter.health()
    assert health.status.value == "healthy"


def test_sample_adapter_metadata() -> None:
    adapter = SampleExecutionAdapter()
    metadata = adapter.metadata()
    assert metadata.adapter_id == "sample-adapter"
    assert "dispatch" in metadata.capabilities


def test_failing_adapter_raises() -> None:
    adapter = FailingExecutionAdapter()
    with pytest.raises(RuntimeError, match="adapter dispatch failed"):
        adapter.dispatch(make_adapter_context(adapter_id="failing-adapter"))


def test_rejecting_adapter_validate() -> None:
    adapter = RejectingExecutionAdapter()
    assert adapter.validate(make_adapter_context(adapter_id="rejecting-adapter")) is False


def test_adapter_state_enum() -> None:
    assert AdapterState.REGISTERED.value == "registered"
    assert AdapterState.ACTIVE.value == "active"
