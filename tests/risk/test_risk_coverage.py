"""Additional risk layer coverage tests."""

from __future__ import annotations

import pytest

from risk import (
    OrchestrationError,
    PolicyNotFoundError,
    PolicyRegistrationError,
    RiskError,
    RiskNotFoundError,
    RiskRegistrationError,
    RiskStateError,
    ScoringError,
    ValidationError,
    get_policy_registry,
    get_risk_registry,
    reset_policy_registry,
    reset_risk_registry,
)
from risk.policy.policy_registry import PolicyRegistry
from tests.risk_helpers import SamplePolicy, make_policy_metadata


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_risk_registry()
    reset_policy_registry()
    yield
    reset_risk_registry()
    reset_policy_registry()


def test_exception_codes() -> None:
    assert RiskError("msg").code == "risk_error"
    assert RiskNotFoundError("id").code == "risk_not_found"
    assert RiskRegistrationError("msg").code == "risk_registration_error"
    assert RiskStateError("id", "created", "run").code == "risk_state_error"
    assert PolicyNotFoundError("id").code == "policy_not_found"
    assert PolicyRegistrationError("msg").code == "policy_registration_error"
    assert ValidationError("msg").code == "validation_error"
    assert OrchestrationError("msg").code == "orchestration_error"
    assert ScoringError("msg").code == "scoring_error"


def test_policy_registry_singleton() -> None:
    registry = get_policy_registry()
    registry.register(make_policy_metadata(policy_id="singleton"))
    assert get_policy_registry().list() == ("singleton",)


def test_policy_registry_unregister() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    registry.unregister("sample-policy")
    with pytest.raises(PolicyNotFoundError):
        registry.resolve("sample-policy")


def test_policy_registry_resolve_type_not_found() -> None:
    registry = PolicyRegistry()
    with pytest.raises(PolicyNotFoundError):
        registry.resolve_type("missing")


def test_policy_registry_list_types() -> None:
    registry = PolicyRegistry()
    registry.register_type(SamplePolicy)
    assert registry.list_types() == ("sample-policy",)


def test_risk_registry_singleton() -> None:
    from tests.risk_helpers import make_engine_metadata

    registry = get_risk_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_risk_registry().list() == ("singleton",)
