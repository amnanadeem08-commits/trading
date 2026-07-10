"""Feature window contract."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature_vector import FeatureVector
from models.common import PlatformModel


class FeatureWindow(PlatformModel):
    """Sliding window of feature vectors."""

    window_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    vectors: tuple[FeatureVector, ...] = Field(default_factory=tuple)
    window_size: int = Field(ge=1, default=1)
    offset: int = Field(ge=0, default=0)
