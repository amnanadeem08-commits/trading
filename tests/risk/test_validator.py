"""Unit tests for validation framework."""

from __future__ import annotations

from risk import RiskContext, Validator
from risk.validation.validation_result import ValidationState
from tests.risk_helpers import FailingRule, PassingRule, make_decision_result


def test_validator_passing_rules() -> None:
    validator = Validator((PassingRule(),))
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = validator.validate(context)
    assert result.passed is True
    assert result.passed_rules == ("passing-rule",)
    assert result.failed_rules == ()


def test_validator_failing_rule() -> None:
    validator = Validator((FailingRule(),))
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = validator.validate(context)
    assert result.passed is False
    assert result.state == ValidationState.FAILED
    assert result.failed_rules == ("failing-rule",)


def test_validator_with_decision_result() -> None:
    validator = Validator((PassingRule(),))
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        decision_result=make_decision_result(),
    )
    result = validator.validate(context)
    assert result.passed is True


def test_validator_register_rule() -> None:
    validator = Validator()
    validator.register_rule(PassingRule())
    context = RiskContext(
        risk_id="risk-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    result = validator.validate(context)
    assert result.passed is True
