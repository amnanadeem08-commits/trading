"""Unit tests for dataset lineage and provenance."""

from __future__ import annotations

import pytest

from data import LineageTracker, ProvenanceTracker


@pytest.mark.unit
def test_lineage_tracker_records_and_lists() -> None:
    tracker = LineageTracker()
    record = tracker.record(
        dataset_id="records",
        operation="load",
        correlation_id="corr-1",
        source_dataset_ids=("source-a",),
        metadata={"step": "initial"},
    )
    assert record.dataset_id == "records"
    listed = tracker.list_for_dataset("records")
    assert len(listed) == 1
    assert tracker.list_all() == (record,)


@pytest.mark.unit
def test_lineage_tracker_clear() -> None:
    tracker = LineageTracker()
    tracker.record(
        dataset_id="records",
        operation="load",
        correlation_id="corr-1",
    )
    tracker.clear()
    assert tracker.list_all() == ()


@pytest.mark.unit
def test_provenance_tracker_records_and_latest() -> None:
    tracker = ProvenanceTracker()
    first = tracker.record(
        dataset_id="records",
        version="1.0.0",
        producer="loader",
        configuration_hash="abc123",
        correlation_id="corr-1",
    )
    second = tracker.record(
        dataset_id="records",
        version="1.0.1",
        producer="loader",
        configuration_hash="def456",
        correlation_id="corr-2",
    )
    latest = tracker.latest_for_dataset("records")
    assert latest == second
    assert tracker.list_for_dataset("records") == (first, second)


@pytest.mark.unit
def test_provenance_tracker_latest_missing_returns_none() -> None:
    tracker = ProvenanceTracker()
    assert tracker.latest_for_dataset("missing") is None


@pytest.mark.unit
def test_provenance_tracker_clear() -> None:
    tracker = ProvenanceTracker()
    tracker.record(
        dataset_id="records",
        version="1.0.0",
        producer="loader",
        configuration_hash="abc123",
        correlation_id="corr-1",
    )
    tracker.clear()
    assert tracker.list_all() == ()
