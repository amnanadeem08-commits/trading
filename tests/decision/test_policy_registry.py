"""Unit tests for policy registry singleton."""

from __future__ import annotations

import pytest

from decision import PolicyRegistry, get_policy_registry, reset_policy_registry
from decision.exceptions import PolicyNotFoundError
from tests.decision_helpers import SamplePolicy, make_policy_metadata


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_policy_registry()
    yield
    reset_policy_registry()


def test_singleton_registry() -> None:
    registry = get_policy_registry()
    registry.register(make_policy_metadata(policy_id="singleton"))
    assert get_policy_registry().list() == ("singleton",)


def test_unregister() -> None:
    registry = PolicyRegistry()
    registry.register(make_policy_metadata())
    registry.unregister("sample-policy")
    with pytest.raises(PolicyNotFoundError):
        registry.resolve("sample-policy")


def test_list_types() -> None:
    registry = PolicyRegistry()
    registry.register_type(SamplePolicy)
    assert registry.list_types() == ("sample-policy",)
