"""Unit tests for feature store feature registry."""

from __future__ import annotations

import pytest

from feature_store import (
    FeatureRegistry,
    FeatureRegistryEntry,
    get_feature_store_registry,
    reset_feature_store_registry,
)
from feature_store.exceptions import FeatureRecordNotFoundError


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_feature_store_registry()
    yield
    reset_feature_store_registry()


@pytest.mark.unit
def test_feature_registry_register_and_lookup() -> None:
    registry = FeatureRegistry()
    entry = FeatureRegistryEntry(
        feature_name="close",
        dataset_id="dataset-1",
        schema_id="feature-schema-v1",
    )
    registry.register(entry)
    resolved = registry.lookup("close")
    assert resolved.dataset_id == "dataset-1"
    assert registry.exists("close") is True
    assert registry.list() == ("close",)


@pytest.mark.unit
def test_feature_registry_missing_raises() -> None:
    registry = FeatureRegistry()
    with pytest.raises(FeatureRecordNotFoundError):
        registry.lookup("missing")


@pytest.mark.unit
def test_get_feature_store_registry_singleton() -> None:
    first = get_feature_store_registry()
    second = get_feature_store_registry()
    assert first is second
