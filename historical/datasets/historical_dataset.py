"""Historical dataset domain contract."""

from __future__ import annotations

import hashlib
import json

from pydantic import Field

from historical.datasets.dataset_metadata import HistoricalDatasetMetadata
from models.common import PlatformModel, UTCDateTime


class HistoricalDatasetSchema(PlatformModel):
    """Generic schema definition for historical records."""

    fields: tuple[str, ...] = Field(default_factory=tuple)
    required_fields: tuple[str, ...] = Field(default_factory=tuple)
    timestamp_field: str = "timestamp"


class HistoricalDataset(PlatformModel):
    """Registered historical dataset definition."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    metadata: HistoricalDatasetMetadata
    dataset_schema: HistoricalDatasetSchema = Field(default_factory=HistoricalDatasetSchema)
    time_range_start: UTCDateTime | None = None
    time_range_end: UTCDateTime | None = None
    record_count: int = Field(ge=0, default=0)
    checksum: str = ""
    source: str = "internal"
    tags: tuple[str, ...] = Field(default_factory=tuple)

    def with_record_count(self, count: int) -> HistoricalDataset:
        """Return a copy with an updated record count."""
        return self.model_copy(update={"record_count": count})

    def with_checksum(self, checksum: str) -> HistoricalDataset:
        """Return a copy with an updated checksum."""
        return self.model_copy(update={"checksum": checksum})

    def with_time_range(
        self,
        *,
        start: UTCDateTime | None,
        end: UTCDateTime | None,
    ) -> HistoricalDataset:
        """Return a copy with an updated time range."""
        return self.model_copy(update={"time_range_start": start, "time_range_end": end})


def compute_dataset_checksum(records: tuple[dict[str, object], ...]) -> str:
    """Compute a stable checksum for dataset records."""
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
