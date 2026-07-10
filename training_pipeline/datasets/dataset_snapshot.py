"""Dataset snapshot binding for training."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime


class DatasetSnapshot(PlatformModel):
    """Immutable snapshot of a feature store dataset for training."""

    snapshot_id: str
    dataset_id: str
    version: str
    record_count: int
    checksum: str
    captured_at: UTCDateTime
