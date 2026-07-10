"""Dataset provenance tracking."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ProvenanceRecord(PlatformModel):
    """Provenance record for a dataset artifact."""

    record_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    configuration_hash: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    occurred_at: UTCDateTime = Field(default_factory=utc_now)
    attributes: dict[str, str] = Field(default_factory=dict)


class ProvenanceTracker:
    """Tracks dataset provenance records."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: list[ProvenanceRecord] = []

    def record(
        self,
        *,
        dataset_id: str,
        version: str,
        producer: str,
        configuration_hash: str,
        correlation_id: str,
        attributes: dict[str, str] | None = None,
    ) -> ProvenanceRecord:
        """Record a provenance event."""
        entry = ProvenanceRecord(
            record_id=str(uuid4()),
            dataset_id=dataset_id,
            version=version,
            producer=producer,
            configuration_hash=configuration_hash,
            correlation_id=correlation_id,
            attributes=attributes or {},
        )
        with self._lock:
            self._records.append(entry)
        return entry

    def list_for_dataset(self, dataset_id: str) -> tuple[ProvenanceRecord, ...]:
        """Return provenance records for a dataset."""
        with self._lock:
            return tuple(record for record in self._records if record.dataset_id == dataset_id)

    def latest_for_dataset(self, dataset_id: str) -> ProvenanceRecord | None:
        """Return the latest provenance record for a dataset."""
        records = self.list_for_dataset(dataset_id)
        if not records:
            return None
        return records[-1]

    def list_all(self) -> tuple[ProvenanceRecord, ...]:
        """Return all provenance records."""
        with self._lock:
            return tuple(self._records)

    def clear(self) -> None:
        """Clear all provenance records."""
        with self._lock:
            self._records.clear()
