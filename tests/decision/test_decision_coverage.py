"""Additional decision layer coverage tests."""

from __future__ import annotations

import pytest

from decision import (
    DecisionError,
    DecisionNotFoundError,
    DecisionRegistrationError,
    DecisionStateError,
    EvaluationError,
    OrchestrationError,
    PolicyNotFoundError,
    PolicyRegistrationError,
    get_decision_registry,
    get_policy_registry,
    reset_decision_registry,
    reset_policy_registry,
)
from decision.registry.decision_registry import DecisionRegistry
from tests.decision_helpers import SampleDecisionEngine, make_engine_metadata


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_decision_registry()
    reset_policy_registry()
    yield
    reset_decision_registry()
    reset_policy_registry()


def test_exception_codes() -> None:
    assert DecisionError("msg").code == "decision_error"
    assert DecisionNotFoundError("id").code == "decision_not_found"
    assert DecisionRegistrationError("msg").code == "decision_registration_error"
    assert DecisionStateError("id", "created", "run").code == "decision_state_error"
    assert PolicyNotFoundError("id").code == "policy_not_found"
    assert PolicyRegistrationError("msg").code == "policy_registration_error"
    assert OrchestrationError("msg").code == "orchestration_error"
    assert EvaluationError("msg").code == "evaluation_error"


def test_decision_registry_singleton() -> None:
    registry = get_decision_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_decision_registry().list() == ("singleton",)


def test_decision_registry_unregister() -> None:
    registry = DecisionRegistry()
    registry.register(make_engine_metadata())
    registry.unregister("sample-engine")
    with pytest.raises(DecisionNotFoundError):
        registry.resolve("sample-engine")


def test_decision_registry_empty_id_raises() -> None:
    registry = DecisionRegistry()
    metadata = make_engine_metadata(engine_id="  ")
    with pytest.raises(DecisionRegistrationError):
        registry.register(metadata)


def test_decision_registry_duplicate_raises() -> None:
    registry = DecisionRegistry()
    registry.register(make_engine_metadata())
    with pytest.raises(DecisionRegistrationError):
        registry.register(make_engine_metadata())


def test_decision_registry_resolve_type_not_found() -> None:
    registry = DecisionRegistry()
    with pytest.raises(DecisionNotFoundError):
        registry.resolve_type("missing")


def test_decision_registry_set_state_not_found() -> None:
    from decision import DecisionState

    registry = DecisionRegistry()
    with pytest.raises(DecisionNotFoundError):
        registry.set_state("missing", DecisionState.PROCESSING)


def test_decision_registry_list_types() -> None:
    registry = DecisionRegistry()
    registry.register_type(SampleDecisionEngine)
    assert registry.list_types() == ("sample-engine",)


def test_policy_registry_singleton() -> None:
    registry = get_policy_registry()
    assert registry.list() == ()
