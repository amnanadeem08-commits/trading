"""Signal engine intake public surface."""

from __future__ import annotations

from signal_engine.intake.feature_intake import (
    FeatureIntakePayload,
    feature_intake_from_set,
    feature_intake_from_store_record,
    feature_intake_from_vector,
)
from signal_engine.intake.market_intake import (
    MarketIntakeFrame,
    market_intake_from_candle,
    market_intake_from_record,
)
from signal_engine.intake.provenance import provenance_from_intake
from signal_engine.intake.snapshot_intake import (
    SnapshotIntakeRef,
    snapshot_ref_from_snapshot,
)

__all__ = [
    "FeatureIntakePayload",
    "MarketIntakeFrame",
    "SnapshotIntakeRef",
    "feature_intake_from_set",
    "feature_intake_from_store_record",
    "feature_intake_from_vector",
    "market_intake_from_candle",
    "market_intake_from_record",
    "provenance_from_intake",
    "snapshot_ref_from_snapshot",
]
