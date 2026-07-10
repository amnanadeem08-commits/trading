"""Feature vector contract."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature import Feature
from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureVector(PlatformModel):
    """ML-ready vector of features derived from a single market record."""

    vector_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    features: tuple[Feature, ...] = Field(default_factory=tuple)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    sequence: int = Field(ge=0, default=0)
    version: str = Field(min_length=1, default="1.0.0")
