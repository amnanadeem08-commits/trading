"""Unit tests for provider versioning."""

from __future__ import annotations

import pytest

from storage_providers import ProviderVersionRegistry, StorageProviderError


@pytest.mark.unit
def test_provider_version_registry_register_and_latest() -> None:
    registry = ProviderVersionRegistry()
    version = registry.register(version_id="sp-v1", provider_schema="1.0.0")
    assert version.version_id == "sp-v1"
    assert registry.latest() == version


@pytest.mark.unit
def test_provider_version_registry_rejects_empty_id() -> None:
    registry = ProviderVersionRegistry()
    with pytest.raises(StorageProviderError):
        registry.register(version_id="", provider_schema="1.0.0")
