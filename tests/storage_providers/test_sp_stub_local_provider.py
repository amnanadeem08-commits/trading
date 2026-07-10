"""Unit tests for stub local provider."""

from __future__ import annotations

import pytest

from storage_providers import (
    STUB_LOCAL_PROVIDER_ID,
    ProviderCapability,
    ProviderType,
    StubLocalProvider,
    create_stub_local_provider,
)


@pytest.mark.unit
def test_stub_local_provider_contract() -> None:
    provider = create_stub_local_provider()
    assert provider.provider_id() == STUB_LOCAL_PROVIDER_ID
    assert provider.provider_type() == ProviderType.LOCAL
    assert ProviderCapability.METADATA_RESOLUTION in provider.capabilities()


@pytest.mark.unit
def test_stub_local_provider_deterministic_resolution() -> None:
    provider = StubLocalProvider()
    uri = "local://artifacts/stub-model/1.0.0/model.stub"
    first = provider.resolve(uri=uri)
    second = provider.resolve(uri=uri)
    assert first == second
    assert first["resolved"] is True
    assert first["scheme"] == "local"


@pytest.mark.unit
def test_stub_local_provider_fetch_metadata_is_complete() -> None:
    provider = StubLocalProvider()
    metadata = provider.fetch_metadata(uri="local://artifacts/stub-model/1.0.0/model.stub")
    assert metadata["complete"] is True
    assert metadata["checksum_algorithm"] == "sha256"
    assert metadata["manifest_files"] == ("model.stub", "manifest.json")


@pytest.mark.unit
def test_stub_local_provider_validate_returns_metadata() -> None:
    provider = StubLocalProvider()
    result = provider.validate()
    assert result["valid"] is True
    assert result["provider_id"] == STUB_LOCAL_PROVIDER_ID
