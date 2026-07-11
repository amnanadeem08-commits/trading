"""Feature snapshot intake references for provenance."""

from __future__ import annotations

from pydantic import Field

from feature_store.models.feature_snapshot import FeatureSnapshot
from models.common import PlatformModel, UTCDateTime, utc_now
from signal_engine.exceptions import SignalIntakeError


class SnapshotIntakeRef(PlatformModel):
    """Immutable reference to a feature-store snapshot for reproducibility."""

    snapshot_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    checksum: str = ""
    lineage: tuple[str, ...] = Field(default_factory=tuple)
    pinned_at: UTCDateTime = Field(default_factory=utc_now)


def snapshot_ref_from_snapshot(snapshot: FeatureSnapshot) -> SnapshotIntakeRef:
    """Map a feature snapshot into a provenance-friendly intake reference."""
    if not snapshot.snapshot_id.strip() or not snapshot.version.strip():
        raise SignalIntakeError("snapshot_id and version must not be empty")
    return SnapshotIntakeRef(
        snapshot_id=snapshot.snapshot_id,
        dataset_id=snapshot.dataset_id,
        version=snapshot.version,
        checksum=snapshot.checksum,
        lineage=snapshot.lineage,
        pinned_at=snapshot.created_at,
    )
