"""Contract tests for paper execution adapter."""

from __future__ import annotations

import inspect

import pytest

from connectors import (
    TERMINAL_PAPER_STATES,
    PaperExecutionAdapter,
    PaperExecutionRecord,
    PaperExecutionResult,
    PaperSettings,
    PaperState,
    PaperValidationResult,
    PaperValidator,
    SimulationEngine,
    SimulationIdGenerator,
)
from tests.paper_helpers import make_paper_adapter, make_paper_adapter_context


@pytest.mark.contract
def test_paper_execution_adapter_contract() -> None:
    adapter = make_paper_adapter()
    assert adapter.adapter_id() == "paper-adapter"
    assert adapter.name() == "Paper Execution Adapter"
    assert adapter.version() == "1.0.0"


@pytest.mark.contract
def test_paper_adapter_required_methods() -> None:
    methods = {
        name for name, _ in inspect.getmembers(PaperExecutionAdapter, predicate=inspect.isfunction)
    }
    assert "initialize" in methods
    assert "validate" in methods
    assert "dispatch" in methods
    assert "shutdown" in methods
    assert "health" in methods


@pytest.mark.contract
def test_paper_execution_result_contract() -> None:
    fields = set(PaperExecutionResult.model_fields)
    assert "execution_id" in fields
    assert "request_id" in fields
    assert "status" in fields
    assert "latency_ms" in fields
    assert "duration_ms" in fields
    assert "metadata" in fields
    assert "validation_passed" in fields
    assert "started_at" in fields
    assert "completed_at" in fields


@pytest.mark.contract
def test_paper_execution_record_contract() -> None:
    fields = set(PaperExecutionRecord.model_fields)
    assert "record_id" in fields
    assert "execution_id" in fields
    assert "request_id" in fields
    assert "adapter_id" in fields
    assert "state" in fields


@pytest.mark.contract
def test_paper_settings_contract() -> None:
    fields = set(PaperSettings.model_fields)
    assert "enabled" in fields
    assert "deterministic" in fields
    assert "random_seed" in fields
    assert "failure_rate" in fields
    assert "latency_ms_min" in fields
    assert "latency_ms_max" in fields
    assert "simulate_delay" in fields


@pytest.mark.contract
def test_simulation_engine_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(SimulationEngine, predicate=inspect.isfunction)
    }
    assert "generate_execution_id" in methods
    assert "simulate" in methods
    assert "reset" in methods


@pytest.mark.contract
def test_paper_validator_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(PaperValidator, predicate=inspect.isfunction)}
    assert "validate_request" in methods
    assert "validate_adapter_state" in methods
    assert "validate_configuration" in methods
    assert "validate_dispatch" in methods


@pytest.mark.contract
def test_paper_dispatch_output_contract() -> None:
    adapter = make_paper_adapter()
    context = make_paper_adapter_context()
    adapter.initialize(context)
    output = adapter.dispatch(context)
    assert output["simulated"] is True
    assert output["execution_id"] == context.execution_id
    assert output["request_id"] == context.request_id
    assert output["status"] in {state.value for state in PaperState}
    assert isinstance(output["latency_ms"], int)
    assert isinstance(output["duration_ms"], int)
    assert isinstance(output["metadata"], dict)


@pytest.mark.contract
def test_paper_validation_result_contract() -> None:
    result = PaperValidationResult(valid=True, checks={"enabled": True})
    assert result.valid is True


@pytest.mark.contract
def test_terminal_paper_states_contract() -> None:
    assert PaperState.COMPLETED in TERMINAL_PAPER_STATES
    assert PaperState.FAILED in TERMINAL_PAPER_STATES
    assert PaperState.CANCELLED in TERMINAL_PAPER_STATES


@pytest.mark.contract
def test_simulation_id_generator_contract() -> None:
    generator = SimulationIdGenerator(deterministic=True, seed=1)
    assert generator.next_execution_id().startswith("sim-")
