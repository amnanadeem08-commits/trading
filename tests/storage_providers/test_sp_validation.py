"""Unit tests for storage provider validator."""

from __future__ import annotations

import pytest

from storage_providers import (
    ProviderRegistry,
    ProviderValidationError,
    StorageProviderValidator,
)
from tests.storage_providers_helpers import make_stub_storage_provider


@pytest.mark.unit
def test_validator_accepts_stub_provider() -> None:
    validator = StorageProviderValidator()
    provider = make_stub_storage_provider(provider_id="provider-new")
    result = validator.validate_provider(provider)
    assert result.valid is True


@pytest.mark.unit
def test_validator_rejects_duplicate_registration() -> None:
    registry = ProviderRegistry()
    validator = StorageProviderValidator(registry=registry)
    provider = make_stub_storage_provider()
    registry.register(provider)
    result = validator.validate_provider(provider)
    assert result.valid is False
    assert "already registered" in result.errors[0]


@pytest.mark.unit
def test_validator_rejects_unsupported_uri_scheme() -> None:
    provider = make_stub_storage_provider(supported_schemes=("local",))
    validator = StorageProviderValidator()
    result = validator.validate_uri_scheme("s3://bucket/key", provider)
    assert result.valid is False


@pytest.mark.unit
def test_validator_validate_resolution_checks_health_and_metadata() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider(provider_id="provider-runtime")
    registry.register(provider)
    validator = StorageProviderValidator(registry=registry)
    result = validator.validate_resolution(uri="local://artifacts/model.stub", provider=provider)
    assert result.valid is True


@pytest.mark.unit
def test_validator_rejects_incomplete_metadata() -> None:
    provider = make_stub_storage_provider(complete_metadata=False)
    validator = StorageProviderValidator()
    result = validator.validate_metadata_completeness(
        provider=provider,
        uri="local://artifacts/model.stub",
    )
    assert result.valid is False


@pytest.mark.unit
def test_validator_ensure_valid_raises() -> None:
    validator = StorageProviderValidator()
    with pytest.raises(ProviderValidationError):
        validator.ensure_valid(
            validator.validate_uri_scheme("bad-uri", make_stub_storage_provider())
        )


@pytest.mark.unit
def test_validator_provider_exists() -> None:
    registry = ProviderRegistry()
    provider = make_stub_storage_provider(provider_id="exists")
    registry.register(provider)
    validator = StorageProviderValidator(registry=registry)
    assert validator.validate_provider_exists("exists").valid is True
    assert validator.validate_provider_exists("missing").valid is False
