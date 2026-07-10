"""Unit tests for risk policy contracts."""

from __future__ import annotations

import pytest

from risk import PolicyResult, RiskContext, RiskPolicy
from risk.exceptions import PolicyNotFoundError, PolicyRegistrationError
from risk.policy.policy_registry import PolicyRegistry
from risk.validation.validation_result import ValidationResult, ValidationState
from tests.risk_helpers import RejectingPolicy, SamplePolicy, make_policy_metadata


def test_sample_policy_metadata() -> None:
    policy = SamplePolicy()
    metadata = policy.metadata()
    assert metadata.policy_id == "sample-policy"


def test_sample_policy_evaluate() -> None:
    policy = SamplePolicy()
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    validation = ValidationResult(validation_id="val-1", state=ValidationState.PASSED)
    result = policy.evaluate(context, validation_result=validation, decision_output={"a": 1})
    assert isinstance(result, PolicyResult)
    assert result.compliant is True
    assert result.score == 0.9


def test_rejecting_policy() -> None:
    policy = RejectingPolicy()
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    validation = ValidationResult(validation_id="val-1", state=ValidationState.PASSED)
    result = policy.evaluate(context, validation_result=validation, decision_output={})
    assert result.compliant is False


def test_policy_registry_register() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    metadata = registry.resolve("sample-policy")
    assert metadata.name == "Sample Policy"


def test_policy_registry_duplicate_raises() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    with pytest.raises(PolicyRegistrationError):
        registry.register(make_policy_metadata())


def test_policy_registry_not_found() -> None:
    registry = PolicyRegistry()
    with pytest.raises(PolicyNotFoundError):
        registry.resolve("missing")


def test_risk_policy_is_abstract() -> None:
    with pytest.raises(TypeError):
        RiskPolicy()  # type: ignore[abstract]
