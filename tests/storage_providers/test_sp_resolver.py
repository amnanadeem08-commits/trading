"""Unit tests for provider resolver."""

from __future__ import annotations

import pytest

from storage_providers import (
    ProviderRegistry,
    ProviderResolutionError,
    ProviderResolver,
    ProviderType,
)
from tests.storage_providers_helpers import STUB_PROVIDER_ID, make_stub_storage_provider


@pytest.mark.unit
def test_provider_resolver_maps_uri_to_provider() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider())
    resolver = ProviderResolver(registry=registry)
    provider = resolver.resolve("local://artifacts/stub-model/1.0.0/model.stub")
    assert provider.provider_id() == STUB_PROVIDER_ID


@pytest.mark.unit
def test_provider_resolver_extracts_provider_type() -> None:
    registry = ProviderRegistry()
    resolver = ProviderResolver(registry=registry)
    assert resolver.resolve_provider_type("s3://bucket/key") == ProviderType.S3
    assert resolver.resolve_provider_type("gs://bucket/key") == ProviderType.GCS
    assert resolver.resolve_provider_type("custom://bucket/key") == ProviderType.CUSTOM


@pytest.mark.unit
def test_provider_resolver_rejects_unsupported_scheme() -> None:
    registry = ProviderRegistry()
    registry.register(make_stub_storage_provider(supported_schemes=("local",)))
    resolver = ProviderResolver(registry=registry)
    with pytest.raises(ProviderResolutionError):
        resolver.resolve("s3://bucket/key")


@pytest.mark.unit
def test_provider_resolver_rejects_invalid_uri() -> None:
    registry = ProviderRegistry()
    resolver = ProviderResolver(registry=registry)
    with pytest.raises(ProviderResolutionError):
        resolver.extract_scheme("invalid-uri")
