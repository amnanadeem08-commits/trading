"""Feature set contract."""

from __future__ import annotations

from pydantic import Field

from feature_engineering.models.feature_metadata import FeatureMetadata
from feature_engineering.models.feature_vector import FeatureVector
from models.common import PlatformModel


class FeatureSet(PlatformModel):
    """Named collection of feature vectors."""

    feature_set_id: str = Field(min_length=1)
    vectors: tuple[FeatureVector, ...] = Field(default_factory=tuple)
    metadata: FeatureMetadata
