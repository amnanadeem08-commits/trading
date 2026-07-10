"""Additional core layer coverage tests."""

from __future__ import annotations

import pytest

from core import (
    TERMINAL_OPERATION_STATES,
    CoreError,
    CoreStateError,
    CoreValidationError,
    DecisionGeneratedEvent,
    EvaluationCompletedEvent,
    OperationState,
    ResourceCreatedEvent,
    build_dependency_graph,
    detect_cycle,
    entity_metadata,
    topological_order,
)
from core.dependency import DependencyGraph
from tests.core_helpers import SampleEntity, make_entity


@pytest.mark.unit
def test_exception_codes() -> None:
    assert CoreError("x").code == "core_error"
    assert CoreValidationError("x").code == "core_validation_error"
    assert CoreStateError("e", "active", "archive").code == "core_state_error"


@pytest.mark.unit
def test_terminal_operation_states() -> None:
    assert OperationState.COMPLETED in TERMINAL_OPERATION_STATES
    assert OperationState.ACTIVE not in TERMINAL_OPERATION_STATES


@pytest.mark.unit
def test_entity_metadata_decorator() -> None:
    metadata = entity_metadata(SampleEntity)
    assert metadata["entity_id"] == "sample-entity"
    assert metadata["auto_register"] is False


@pytest.mark.unit
def test_dependency_graph_utilities() -> None:
    graph = build_dependency_graph(("a", "b"), {"b": ("a",)})
    assert detect_cycle(graph) is None
    assert topological_order(graph) == ("a", "b")


@pytest.mark.unit
def test_dependency_graph_cycle_detection() -> None:
    graph = DependencyGraph(nodes=("a", "b"), edges={"a": ("b",), "b": ("a",)})
    cycle = detect_cycle(graph)
    assert cycle is not None
    assert "a" in cycle


@pytest.mark.unit
def test_domain_event_contracts() -> None:
    resource = ResourceCreatedEvent(
        event_id="evt-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        entity_id="resource-1",
        resource_type="artifact",
        resource_id="resource-1",
        resource_version="1.0.0",
    )
    evaluation = EvaluationCompletedEvent(
        event_id="evt-2",
        correlation_id="corr-1",
        trace_id="trace-1",
        entity_id="resource-1",
        evaluation_id="eval-1",
        subject_id="resource-1",
        status="completed",
        score=0.9,
    )
    decision = DecisionGeneratedEvent(
        event_id="evt-3",
        correlation_id="corr-1",
        trace_id="trace-1",
        entity_id="resource-1",
        decision_id="dec-1",
        source_id="resource-1",
        outcome_type="accepted",
        confidence=0.8,
    )
    assert resource.event_type.value == "resource_created"
    assert evaluation.score == 0.9
    assert decision.outcome_type == "accepted"


@pytest.mark.unit
def test_make_entity_defaults() -> None:
    entity = make_entity()
    assert entity.state == OperationState.REGISTERED
