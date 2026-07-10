"""Unit tests for provider registry."""

from __future__ import annotations

import pytest

from storage_providers import ProviderNotFoundError, ProviderRegistry, ProviderState
from tests.storage_providers_helpers import STUB_PROVIDER_ID, make_stub_storage_provider


@pytest.mark.unit
def test_provider_registry_register_and_lookup() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider(provider_id="provider-1")
    record = registry.register(provider)
    assert record.provider_id == "provider-1"
    assert record.state == ProviderState.REGISTERED
    assert registry.lookup("provider-1").provider_id == "provider-1"


@pytest.mark.unit
def test_provider_registry_resolve_by_scheme() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider()
    registry.register(provider)
    resolved = registry.resolve("local://artifacts/model.stub")
    assert resolved.provider_id() == STUB_PROVIDER_ID


@pytest.mark.unit
def test_provider_registry_update_state_and_clear() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider())
    registry.update_state(STUB_PROVIDER_ID, ProviderState.VALIDATED)
    assert registry.lookup(STUB_PROVIDER_ID).state == ProviderState.VALIDATED
    registry.clear()
    assert registry.list() == ()


@pytest.mark.unit
def test_provider_registry_lookup_missing() -> None:
    registry = ProviderRegistry()
    with pytest.raises(ProviderNotFoundError):
        registry.lookup("missing")
