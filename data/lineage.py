"""Dataset lineage tracking."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class LineageRecord(PlatformModel):
    """Lineage record for a dataset operation."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    source_dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    correlation_id: str = Field(min_length=1)
    occurred_at: UTCDateTime = Field(default_factory=utc_now)
    metadata: dict[str, str] = Field(default_factory=dict)


class LineageTracker:
    """Tracks dataset lineage records."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: list[LineageRecord] = []

    def record(
        self,
        *,
        dataset_id: str,
        operation: str,
        correlation_id: str,
        source_dataset_ids: tuple[str, ...] = (),
        metadata: dict[str, str] | None = None,
    ) -> LineageRecord:
        """Record a lineage event."""
        entry = LineageRecord(
            record_id=str(uuid4()),
            dataset_id=dataset_id,
            operation=operation,
            source_dataset_ids=source_dataset_ids,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._records.append(entry)
        return entry

    def list_for_dataset(self, dataset_id: str) -> tuple[LineageRecord, ...]:
        """Return lineage records for a dataset."""
        with self._lock:
            return tuple(record for record in self._records if record.dataset_id == dataset_id)

    def list_all(self) -> tuple[LineageRecord, ...]:
        """Return all lineage records."""
        with self._lock:
            return tuple(self._records)

    def clear(self) -> None:
        """Clear all lineage records."""
        with self._lock:
            self._records.clear()
