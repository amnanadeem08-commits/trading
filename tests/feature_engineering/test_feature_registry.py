"""Unit tests for feature registry."""

from __future__ import annotations

import pytest

from feature_engineering import FeatureRegistry, get_feature_registry, reset_feature_registry
from feature_engineering.exceptions import FeatureNotFoundError, FeatureRegistrationError
from tests.feature_engineering_helpers import make_catalog_entry


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_feature_registry()
    yield
    reset_feature_registry()


@pytest.mark.unit
def test_register_and_lookup() -> None:
    registry = FeatureRegistry()
    entry = make_catalog_entry()
    registry.register(entry)
    resolved = registry.lookup("feature-1")
    assert resolved.name == "Sample Feature"
    assert registry.exists("feature-1") is True


@pytest.mark.unit
def test_register_rejects_empty_feature_id() -> None:
    registry = FeatureRegistry()
    entry = make_catalog_entry(feature_id=" ")
    with pytest.raises(FeatureRegistrationError):
        registry.register(entry)


@pytest.mark.unit
def test_lookup_missing_raises() -> None:
    registry = FeatureRegistry()
    with pytest.raises(FeatureNotFoundError):
        registry.lookup("missing")


@pytest.mark.unit
def test_version_metadata_capabilities() -> None:
    registry = FeatureRegistry()
    registry.register(make_catalog_entry())
    assert registry.version("feature-1") == "1.0.0"
    assert registry.capabilities("feature-1") == ("extract", "validate")


@pytest.mark.unit
def test_list_versions() -> None:
    registry = FeatureRegistry()
    registry.register(make_catalog_entry())
    entry = make_catalog_entry()
    updated = entry.model_copy(update={"version": "1.1.0"})
    registry.register(updated)
    versions = registry.list_versions("feature-1")
    assert versions == ("1.0.0", "1.1.0")


@pytest.mark.unit
def test_get_feature_registry_singleton() -> None:
    first = get_feature_registry()
    second = get_feature_registry()
    assert first is second
