"""Feature dataset contract."""

from __future__ import annotations

import hashlib
import json

from pydantic import Field

from feature_store.models.feature_metadata import FeatureMetadata
from models.common import PlatformModel, UTCDateTime, utc_now


def compute_feature_dataset_hash(records: tuple[dict[str, str], ...]) -> str:
    """Return a stable SHA-256 hash for feature record payloads."""
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class FeatureDataset(PlatformModel):
    """Registered feature dataset definition."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    metadata: FeatureMetadata
    record_count: int = Field(ge=0, default=0)
    checksum: str = ""
    lineage: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    time_range_start: UTCDateTime | None = None
    time_range_end: UTCDateTime | None = None
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)

    def with_record_count(self, count: int) -> FeatureDataset:
        return self.model_copy(update={"record_count": count, "updated_at": utc_now()})

    def with_checksum(self, checksum: str) -> FeatureDataset:
        return self.model_copy(update={"checksum": checksum, "updated_at": utc_now()})

    def with_time_range(
        self,
        *,
        start: UTCDateTime | None,
        end: UTCDateTime | None,
    ) -> FeatureDataset:
        return self.model_copy(
            update={
                "time_range_start": start,
                "time_range_end": end,
                "updated_at": utc_now(),
            }
        )
