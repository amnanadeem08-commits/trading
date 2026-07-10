"""Unit tests for decision engine contracts."""

from __future__ import annotations

import pytest

from decision import DecisionEngine, DecisionState
from decision.exceptions import DecisionNotFoundError
from decision.registry.decision_registry import DecisionRegistry
from tests.decision_helpers import FailingDecisionEngine, SampleDecisionEngine, make_engine_metadata


def test_sample_engine_metadata() -> None:
    engine = SampleDecisionEngine()
    metadata = engine.metadata()
    assert metadata.engine_id == "sample-engine"
    assert metadata.name == "Sample Engine"
    assert metadata.version == "1.0.0"


def test_sample_engine_process() -> None:
    from decision import DecisionContext

    engine = SampleDecisionEngine()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = engine.process(context)
    assert result.engine_id == "sample-engine"
    assert result.state == DecisionState.PROCESSING
    assert result.confidence == 0.85


def test_registry_register_and_resolve() -> None:
    registry = DecisionRegistry()
    registry.register(make_engine_metadata())
    metadata = registry.resolve("sample-engine")
    assert metadata.name == "Sample Engine"
    assert registry.get_state("sample-engine") == DecisionState.CREATED


def test_registry_register_type() -> None:
    registry = DecisionRegistry()
    registry.register_type(SampleDecisionEngine)
    assert registry.exists("sample-engine")
    assert registry.resolve_type("sample-engine") is SampleDecisionEngine


def test_registry_not_found() -> None:
    registry = DecisionRegistry()
    with pytest.raises(DecisionNotFoundError):
        registry.resolve("missing")


def test_failing_engine_raises() -> None:
    from decision import DecisionContext

    engine = FailingDecisionEngine()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    with pytest.raises(RuntimeError, match="decision processing failed"):
        engine.process(context)


def test_decision_engine_is_abstract() -> None:
    with pytest.raises(TypeError):
        DecisionEngine()  # type: ignore[abstract]
