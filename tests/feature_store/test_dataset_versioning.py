"""Unit tests for dataset versioning."""

from __future__ import annotations

import pytest

from feature_store import DatasetVersion, DatasetVersionRegistry
from feature_store.exceptions import DatasetNotFoundError, FeatureVersionError


@pytest.mark.unit
def test_register_and_latest() -> None:
    registry = DatasetVersionRegistry()
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snap-1",
        )
    )
    latest = registry.latest("dataset-1")
    assert latest.version == "1.0.0"


@pytest.mark.unit
def test_list_versions() -> None:
    registry = DatasetVersionRegistry()
    registry.register(DatasetVersion(dataset_id="dataset-1", version="1.0.0", snapshot_id="snap-1"))
    registry.register(DatasetVersion(dataset_id="dataset-1", version="1.1.0", snapshot_id="snap-2"))
    versions = registry.list_versions("dataset-1")
    assert len(versions) == 2


@pytest.mark.unit
def test_snapshot_lookup() -> None:
    registry = DatasetVersionRegistry()
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snap-lookup",
        )
    )
    resolved = registry.snapshot("snap-lookup")
    assert resolved.dataset_id == "dataset-1"


@pytest.mark.unit
def test_missing_dataset_raises() -> None:
    registry = DatasetVersionRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.latest("missing")


@pytest.mark.unit
def test_missing_snapshot_raises() -> None:
    registry = DatasetVersionRegistry()
    with pytest.raises(FeatureVersionError):
        registry.snapshot("missing")
