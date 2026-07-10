"""Unit tests for decision policy contracts."""

from __future__ import annotations

import pytest

from decision import DecisionContext, DecisionPolicy, PolicyResult
from decision.exceptions import PolicyNotFoundError, PolicyRegistrationError
from decision.policy.policy_registry import PolicyRegistry
from tests.decision_helpers import RejectingPolicy, SamplePolicy, make_policy_metadata


def test_sample_policy_metadata() -> None:
    policy = SamplePolicy()
    metadata = policy.metadata()
    assert metadata.policy_id == "sample-policy"
    assert metadata.version == "1.0.0"


def test_sample_policy_evaluate() -> None:
    policy = SamplePolicy()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = policy.evaluate(context, ai_output={"score": 0.9}, ml_output={"value": 0.8})
    assert isinstance(result, PolicyResult)
    assert result.accepted is True
    assert result.confidence == 0.9


def test_rejecting_policy() -> None:
    policy = RejectingPolicy()
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = policy.evaluate(context, ai_output={}, ml_output={})
    assert result.accepted is False


def test_policy_registry_register() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    metadata = registry.resolve("sample-policy")
    assert metadata.name == "Sample Policy"


def test_policy_registry_register_type() -> None:
    registry = PolicyRegistry()
    registry.register_type(SamplePolicy)
    assert registry.exists("sample-policy")
    policy_type = registry.resolve_type("sample-policy")
    assert policy_type is SamplePolicy


def test_policy_registry_duplicate_raises() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    with pytest.raises(PolicyRegistrationError):
        registry.register(make_policy_metadata())


def test_policy_registry_not_found() -> None:
    registry = PolicyRegistry()
    with pytest.raises(PolicyNotFoundError):
        registry.resolve("missing")


def test_decision_policy_is_abstract() -> None:
    with pytest.raises(TypeError):
        DecisionPolicy()  # type: ignore[abstract]
