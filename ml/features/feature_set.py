"""Feature set contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ml.features.feature_metadata import FeatureMetadata
from models.common import PlatformModel


class FeatureSet(PlatformModel):
    """Transformed feature data contract."""

    feature_set_id: str = Field(min_length=1)
    metadata: FeatureMetadata
    records: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
