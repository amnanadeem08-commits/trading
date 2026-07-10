"""Feature engineering contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo


class IndicatorSnapshot(PlatformModel):
    """Single indicator value at a point in time."""

    name: str = Field(min_length=1)
    value: float
    metadata: dict[str, str | float | int | bool] = Field(default_factory=dict)


class TechnicalProfile(PlatformModel):
    """Output of the Technical Analysis Engine."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    indicators: tuple[IndicatorSnapshot, ...]
    last_close: float = Field(gt=0)


class FeatureSet(PlatformModel):
    """Feature bundle ready for ML and AI consumption."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    technical: TechnicalProfile
    supplemental_features: dict[str, float | str | int | bool] = Field(default_factory=dict)


class FeatureSnapshot(PlatformModel):
    """Immutable, versioned feature snapshot for reproducibility."""

    snapshot_id: str = Field(min_length=1)
    version: VersionInfo
    feature_set: FeatureSet
    schema_version: str = Field(min_length=1)
