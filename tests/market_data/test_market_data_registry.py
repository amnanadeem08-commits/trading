"""Unit tests for market data registry."""

from __future__ import annotations

import pytest

from market_data import MarketDataRegistry, get_market_data_registry, reset_market_data_registry
from market_data.exceptions import MarketRecordNotFoundError, MarketRegistrationError
from tests.market_data_helpers import make_catalog_entry


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_market_data_registry()
    yield
    reset_market_data_registry()


@pytest.mark.unit
def test_register_and_lookup() -> None:
    registry = MarketDataRegistry()
    entry = make_catalog_entry()
    registry.register(entry)
    resolved = registry.lookup("dataset-1")
    assert resolved.name == "Sample Market Dataset"
    assert registry.exists("dataset-1") is True


@pytest.mark.unit
def test_register_rejects_empty_dataset_id() -> None:
    registry = MarketDataRegistry()
    entry = make_catalog_entry(dataset_id=" ")
    with pytest.raises(MarketRegistrationError):
        registry.register(entry)


@pytest.mark.unit
def test_lookup_missing_dataset_raises() -> None:
    registry = MarketDataRegistry()
    with pytest.raises(MarketRecordNotFoundError):
        registry.lookup("missing")


@pytest.mark.unit
def test_unregister_dataset() -> None:
    registry = MarketDataRegistry()
    registry.register(make_catalog_entry())
    registry.unregister("dataset-1")
    assert registry.exists("dataset-1") is False


@pytest.mark.unit
def test_version_metadata_capabilities() -> None:
    registry = MarketDataRegistry()
    registry.register(make_catalog_entry(version="1.0.0"))
    assert registry.version("dataset-1") == "1.0.0"
    metadata = registry.metadata("dataset-1")
    assert metadata.symbol_id == "symbol-1"
    assert registry.capabilities("dataset-1") == ("normalize", "stream")


@pytest.mark.unit
def test_list_versions_tracks_multiple_versions() -> None:
    registry = MarketDataRegistry()
    registry.register(make_catalog_entry(version="1.0.0"))
    registry.register(make_catalog_entry(version="1.1.0"))
    versions = registry.list_versions("dataset-1")
    assert versions == ("1.0.0", "1.1.0")


@pytest.mark.unit
def test_list_registered_datasets() -> None:
    registry = MarketDataRegistry()
    registry.register(make_catalog_entry(dataset_id="alpha"))
    registry.register(make_catalog_entry(dataset_id="beta"))
    assert registry.list() == ("alpha", "beta")


@pytest.mark.unit
def test_get_market_data_registry_singleton() -> None:
    first = get_market_data_registry()
    second = get_market_data_registry()
    assert first is second
