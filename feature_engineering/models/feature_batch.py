"""Feature batch contract."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature_vector import FeatureVector
from models.common import PlatformModel


class FeatureBatch(PlatformModel):
    """Batch of feature vectors produced by extraction."""

    batch_id: str = Field(min_length=1)
    pipeline_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    vectors: tuple[FeatureVector, ...] = Field(default_factory=tuple)
    offset: int = Field(ge=0, default=0)
    total: int = Field(ge=0, default=0)
    completed: bool = False
