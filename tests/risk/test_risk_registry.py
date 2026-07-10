"""Unit tests for risk registry."""

from __future__ import annotations

import pytest

from risk import RiskRegistry, RiskState, get_risk_registry, reset_risk_registry
from risk.exceptions import RiskNotFoundError, RiskRegistrationError
from tests.risk_helpers import SampleRiskEngine, make_engine_metadata


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_risk_registry()
    yield
    reset_risk_registry()


def test_singleton_registry() -> None:
    registry = get_risk_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_risk_registry().list() == ("singleton",)


def test_unregister() -> None:
    registry = RiskRegistry()
    registry.register(make_engine_metadata())
    registry.unregister("sample-engine")
    with pytest.raises(RiskNotFoundError):
        registry.resolve("sample-engine")


def test_list_types() -> None:
    registry = RiskRegistry()
    registry.register_type(SampleRiskEngine)
    assert registry.list_types() == ("sample-engine",)


def test_empty_id_raises() -> None:
    registry = RiskRegistry()
    with pytest.raises(RiskRegistrationError):
        registry.register(make_engine_metadata(engine_id="  "))


def test_set_state_not_found() -> None:
    registry = RiskRegistry()
    with pytest.raises(RiskNotFoundError):
        registry.set_state("missing", RiskState.PROCESSING)
