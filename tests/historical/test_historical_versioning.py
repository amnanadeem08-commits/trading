"""Unit tests for historical versioning."""

from __future__ import annotations

import pytest

from historical import HistoricalVersionRegistry, VersionError
from historical.datasets.dataset_version import DatasetVersion


def test_version_registry_register_and_latest() -> None:
    registry = HistoricalVersionRegistry()
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snapshot-1",
            record_count=1,
            checksum="abc",
        )
    )
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.1.0",
            snapshot_id="snapshot-2",
            record_count=2,
            checksum="def",
        )
    )
    latest = registry.latest("dataset-1")
    assert latest.version == "1.1.0"
    assert len(registry.list_versions("dataset-1")) == 2


def test_version_snapshot_and_rollback_metadata() -> None:
    registry = HistoricalVersionRegistry()
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snapshot-1",
        )
    )
    snapshot = registry.snapshot("snapshot-1")
    assert snapshot.dataset_id == "dataset-1"
    rollback = registry.rollback_metadata("dataset-1", target_version="1.0.0")
    assert rollback.rollback_target == "1.0.0"


def test_version_snapshot_missing_raises() -> None:
    registry = HistoricalVersionRegistry()
    with pytest.raises(VersionError):
        registry.snapshot("missing")
