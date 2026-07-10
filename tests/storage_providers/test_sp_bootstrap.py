"""Unit tests for storage provider bootstrap."""

from __future__ import annotations

import pytest

from storage_providers import (
    LOCAL_PROVIDER_ID,
    STUB_LOCAL_PROVIDER_ID,
    ProviderNotFoundError,
    bootstrap_storage_runtime,
    build_storage_bridge,
)
from tests.storage_providers_helpers import make_stub_storage_bridge


@pytest.mark.unit
def test_build_storage_bridge_auto_registers_local_provider() -> None:
    bridge = build_storage_bridge()
    record = bridge.provider_registry.lookup(LOCAL_PROVIDER_ID)
    assert record.provider_id == LOCAL_PROVIDER_ID


@pytest.mark.unit
def test_bootstrap_storage_runtime_registers_local_provider() -> None:
    _, _, _, storage_bridge = bootstrap_storage_runtime()
    assert storage_bridge.provider_registry.lookup(LOCAL_PROVIDER_ID).provider_id == (
        LOCAL_PROVIDER_ID
    )


@pytest.mark.unit
def test_build_storage_bridge_can_disable_auto_registration() -> None:
    bridge = build_storage_bridge(auto_register_defaults=False)
    with pytest.raises(ProviderNotFoundError):
        bridge.provider_registry.lookup(LOCAL_PROVIDER_ID)


@pytest.mark.unit
def test_stub_storage_bridge_registers_stub_provider_only() -> None:
    bridge = make_stub_storage_bridge()
    assert bridge.provider_registry.lookup(STUB_LOCAL_PROVIDER_ID).provider_id == (
        STUB_LOCAL_PROVIDER_ID
    )
    with pytest.raises(ProviderNotFoundError):
        bridge.provider_registry.lookup(LOCAL_PROVIDER_ID)
