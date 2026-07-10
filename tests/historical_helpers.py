"""Helpers for historical repository tests."""

from __future__ import annotations

from datetime import UTC, datetime

from historical import (
    HistoricalDataset,
    HistoricalDatasetMetadata,
    HistoricalDatasetSchema,
    Repository,
    RepositoryRecord,
)
from models.common import utc_now


def make_sample_dataset(
    *,
    dataset_id: str = "dataset-1",
    version: str = "1.0.0",
    tags: tuple[str, ...] = ("sample",),
) -> HistoricalDataset:
    return HistoricalDataset(
        dataset_id=dataset_id,
        version=version,
        metadata=HistoricalDatasetMetadata(
            dataset_id=dataset_id,
            name="Sample Dataset",
            source="test",
            tags=tags,
        ),
        dataset_schema=HistoricalDatasetSchema(
            fields=("timestamp", "value"),
            required_fields=("timestamp", "value"),
            timestamp_field="timestamp",
        ),
        source="test",
        tags=tags,
    )


def make_sample_record(
    *,
    record_id: str = "record-1",
    dataset_id: str = "dataset-1",
    version: str = "1.0.0",
    sequence: int = 0,
    value: float = 100.0,
    timestamp: datetime | None = None,
) -> RepositoryRecord:
    resolved_timestamp = timestamp or utc_now()
    return RepositoryRecord(
        record_id=record_id,
        dataset_id=dataset_id,
        version=version,
        timestamp=resolved_timestamp,
        sequence=sequence,
        payload={
            "timestamp": resolved_timestamp.isoformat(),
            "value": value,
        },
    )


def seed_repository(repository: Repository, *, record_count: int = 3) -> HistoricalDataset:
    dataset = make_sample_dataset()
    repository.register_dataset(dataset)
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    for index in range(record_count):
        timestamp = base.replace(minute=index)
        repository.store(
            make_sample_record(
                record_id=f"record-{index + 1}",
                sequence=index,
                value=100.0 + index,
                timestamp=timestamp,
            )
        )
    return repository.get_dataset(dataset.dataset_id)
