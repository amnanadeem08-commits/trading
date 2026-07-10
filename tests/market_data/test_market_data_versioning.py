"""Unit tests for market data versioning."""

from __future__ import annotations

import pytest

from market_data import MarketVersion, MarketVersionRegistry
from market_data.exceptions import MarketRecordNotFoundError, MarketVersionError


@pytest.mark.unit
def test_register_and_latest_version() -> None:
    registry = MarketVersionRegistry()
    version = MarketVersion(
        dataset_id="dataset-1",
        version="1.0.0",
        description="initial",
        snapshot_id="snap-1",
    )
    registry.register(version)
    latest = registry.latest("dataset-1")
    assert latest.version == "1.0.0"
    assert latest.snapshot_id == "snap-1"


@pytest.mark.unit
def test_list_versions_and_datasets() -> None:
    registry = MarketVersionRegistry()
    registry.register(
        MarketVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snap-1",
        )
    )
    registry.register(
        MarketVersion(
            dataset_id="dataset-1",
            version="1.1.0",
            snapshot_id="snap-2",
        )
    )
    versions = registry.list_versions("dataset-1")
    assert len(versions) == 2
    assert registry.list_datasets() == ("dataset-1",)


@pytest.mark.unit
def test_snapshot_lookup() -> None:
    registry = MarketVersionRegistry()
    registry.register(
        MarketVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snap-lookup",
        )
    )
    resolved = registry.snapshot("snap-lookup")
    assert resolved.dataset_id == "dataset-1"


@pytest.mark.unit
def test_missing_dataset_raises() -> None:
    registry = MarketVersionRegistry()
    with pytest.raises(MarketRecordNotFoundError):
        registry.latest("missing")


@pytest.mark.unit
def test_missing_snapshot_raises() -> None:
    registry = MarketVersionRegistry()
    with pytest.raises(MarketVersionError):
        registry.snapshot("missing")
