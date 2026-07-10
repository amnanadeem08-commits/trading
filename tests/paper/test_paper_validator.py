"""Unit tests for paper validator."""

from __future__ import annotations

from connectors import PaperState, PaperValidator
from tests.paper_helpers import make_paper_adapter_context, make_paper_settings


def test_paper_validator_request_success() -> None:
    validator = PaperValidator(make_paper_settings())
    result = validator.validate_request(make_paper_adapter_context())
    assert result.valid is True
    assert result.checks["request_id_present"] is True


def test_paper_validator_request_missing_context() -> None:
    validator = PaperValidator()
    result = validator.validate_request(None)
    assert result.valid is False
    assert "Adapter context is required" in result.errors


def test_paper_validator_request_missing_request_id() -> None:
    validator = PaperValidator()
    context = make_paper_adapter_context()
    context = context.model_copy(update={"request_id": "   "})
    result = validator.validate_request(context)
    assert result.valid is False
    assert "Request id is required" in result.errors


def test_paper_validator_request_missing_execution_id() -> None:
    validator = PaperValidator()
    context = make_paper_adapter_context()
    context = context.model_copy(update={"execution_id": ""})
    result = validator.validate_request(context)
    assert result.valid is False
    assert "Execution id is required" in result.errors


def test_paper_validator_state_success() -> None:
    validator = PaperValidator()
    result = validator.validate_adapter_state(PaperState.ACCEPTED)
    assert result.valid is True


def test_paper_validator_state_missing() -> None:
    validator = PaperValidator()
    result = validator.validate_adapter_state(None)
    assert result.valid is False


def test_paper_validator_state_not_eligible() -> None:
    validator = PaperValidator()
    result = validator.validate_adapter_state(PaperState.CANCELLED)
    assert result.valid is False
    assert result.checks["state_eligible"] is False


def test_paper_validator_configuration_disabled() -> None:
    validator = PaperValidator(make_paper_settings(enabled=False))
    result = validator.validate_configuration()
    assert result.valid is False
    assert "Paper adapter is disabled" in result.errors


def test_paper_validator_configuration_success() -> None:
    validator = PaperValidator(make_paper_settings())
    result = validator.validate_configuration()
    assert result.valid is True


def test_paper_validator_dispatch_combined() -> None:
    validator = PaperValidator(make_paper_settings())
    result = validator.validate_dispatch(
        make_paper_adapter_context(),
        state=PaperState.ACCEPTED,
    )
    assert result.valid is True
    assert "enabled" in result.checks
