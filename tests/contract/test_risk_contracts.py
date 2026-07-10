"""Contract tests for risk layer."""

from __future__ import annotations

import inspect

import pytest

from risk import (
    RiskContext,
    RiskEngine,
    RiskPolicy,
    RiskResult,
    ValidationRule,
)
from tests.risk_helpers import SampleRiskEngine


@pytest.mark.contract
def test_risk_engine_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(RiskEngine, predicate=inspect.isfunction)}
    assert "assess" in methods
    assert "engine_id" in methods


@pytest.mark.contract
def test_sample_engine_contract_compliance() -> None:
    engine = SampleRiskEngine()
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = engine.assess(context)
    assert isinstance(result, RiskResult)
    assert result.engine_id == "sample-engine"


@pytest.mark.contract
def test_risk_policy_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(RiskPolicy, predicate=inspect.isfunction)}
    assert "evaluate" in methods
    assert "policy_id" in methods


@pytest.mark.contract
def test_validation_rule_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ValidationRule, predicate=inspect.isfunction)}
    assert "validate" in methods
    assert "rule_id" in methods


@pytest.mark.contract
def test_risk_result_fields() -> None:
    result = RiskResult(
        risk_id="risk-1",
        engine_id="engine-1",
        validation={"passed": True},
        version_info={"engine_version": "1.0.0"},
    )
    assert result.risk_id == "risk-1"
    assert result.validation["passed"] is True
