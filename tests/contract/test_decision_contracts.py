"""Contract tests for decision layer."""

from __future__ import annotations

import inspect

import pytest

from decision import (
    DecisionContext,
    DecisionEngine,
    DecisionPolicy,
    DecisionResult,
    PolicyResult,
)
from tests.decision_helpers import SampleDecisionEngine, SamplePolicy


@pytest.mark.contract
def test_decision_engine_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(DecisionEngine, predicate=inspect.isfunction)}
    assert "process" in methods
    assert "engine_id" in methods


@pytest.mark.contract
def test_sample_engine_contract_compliance() -> None:
    engine = SampleDecisionEngine()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = engine.process(context)
    assert isinstance(result, DecisionResult)
    assert result.engine_id == "sample-engine"


@pytest.mark.contract
def test_decision_policy_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(DecisionPolicy, predicate=inspect.isfunction)}
    assert "evaluate" in methods
    assert "policy_id" in methods


@pytest.mark.contract
def test_sample_policy_contract_compliance() -> None:
    policy = SamplePolicy()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = policy.evaluate(context, ai_output={"a": 1}, ml_output={"b": 2})
    assert isinstance(result, PolicyResult)
    assert result.policy_id == "sample-policy"


@pytest.mark.contract
def test_decision_result_fields() -> None:
    result = DecisionResult(
        decision_id="dec-1",
        engine_id="engine-1",
        confidence=0.9,
        evaluation={"quality_score": 0.9},
        version_info={"engine_version": "1.0.0"},
    )
    assert result.confidence == 0.9
    assert result.evaluation["quality_score"] == 0.9
