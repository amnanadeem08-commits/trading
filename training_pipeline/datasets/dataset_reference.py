"""Dataset reference for training jobs."""

from __future__ import annotations

from models.common import PlatformModel


class DatasetReference(PlatformModel):
    """Reference to a feature store dataset used for training."""

    dataset_id: str
    version: str
    snapshot_id: str | None = None
    record_count: int = 0
    checksum: str = ""
