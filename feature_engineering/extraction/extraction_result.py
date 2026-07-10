"""Feature extraction result contract."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature_batch import FeatureBatch
from feature_engineering.models.feature_set import FeatureSet
from models.common import PlatformModel


class FeatureExtractionResult(PlatformModel):
    """Outcome of a feature extraction pipeline run."""

    pipeline_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    batch: FeatureBatch | None = None
    feature_set: FeatureSet | None = None
    vectors_extracted: int = Field(ge=0, default=0)
    completed: bool = False
