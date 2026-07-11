"""Build Provenance from market/feature intake artifacts."""

from __future__ import annotations

from models.signal import Provenance
from signal_engine.exceptions import SignalIntakeError
from signal_engine.intake.feature_intake import FeatureIntakePayload
from signal_engine.intake.market_intake import MarketIntakeFrame
from signal_engine.intake.snapshot_intake import SnapshotIntakeRef


def provenance_from_intake(
    *,
    market: MarketIntakeFrame,
    features: FeatureIntakePayload,
    snapshot: SnapshotIntakeRef | None = None,
    connector_version: str = "0.0.0",
    prompt_version: str = "prompt-unset",
    strategy_version: str = "strategy-unset",
    provider: str | None = None,
) -> Provenance:
    """Populate Provenance using intake market_id and feature snapshot version."""
    if market.symbol_id != features.symbol_id:
        raise SignalIntakeError("market and feature intake symbol_id must match for provenance")
    feature_snapshot_version = snapshot.version if snapshot is not None else features.version
    if not feature_snapshot_version.strip():
        raise SignalIntakeError("feature_snapshot_version must not be empty")
    return Provenance(
        market_id=market.market_id,
        connector_version=connector_version,
        model_versions={},
        prompt_version=prompt_version,
        strategy_version=strategy_version,
        provider=provider,
        feature_snapshot_version=feature_snapshot_version,
    )
