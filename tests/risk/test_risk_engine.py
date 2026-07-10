"""Unit tests for risk engine contracts."""

from __future__ import annotations

import pytest

from risk import RiskEngine, RiskState
from risk.exceptions import RiskNotFoundError
from risk.registry.risk_registry import RiskRegistry
from tests.risk_helpers import FailingRiskEngine, SampleRiskEngine, make_engine_metadata


def test_sample_engine_metadata() -> None:
    engine = SampleRiskEngine()
    metadata = engine.metadata()
    assert metadata.engine_id == "sample-engine"
    assert metadata.version == "1.0.0"


def test_sample_engine_assess() -> None:
    from risk import RiskContext

    engine = SampleRiskEngine()
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = engine.assess(context)
    assert result.engine_id == "sample-engine"
    assert result.state == RiskState.PROCESSING
    assert result.confidence is not None
    assert result.confidence.value == 0.85


def test_registry_register_and_resolve() -> None:
    registry = RiskRegistry()
    registry.register(make_engine_metadata())
    metadata = registry.resolve("sample-engine")
    assert metadata.name == "Sample Engine"
    assert registry.get_state("sample-engine") == RiskState.CREATED


def test_registry_register_type() -> None:
    registry = RiskRegistry()
    registry.register_type(SampleRiskEngine)
    assert registry.exists("sample-engine")
    assert registry.resolve_type("sample-engine") is SampleRiskEngine


def test_registry_not_found() -> None:
    registry = RiskRegistry()
    with pytest.raises(RiskNotFoundError):
        registry.resolve("missing")


def test_failing_engine_raises() -> None:
    from risk import RiskContext

    engine = FailingRiskEngine()
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    with pytest.raises(RuntimeError, match="risk assessment failed"):
        engine.assess(context)


def test_risk_engine_is_abstract() -> None:
    with pytest.raises(TypeError):
        RiskEngine()  # type: ignore[abstract]
