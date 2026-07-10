"""Feature pipeline interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ml.features.feature_metadata import FeatureMetadata
from ml.features.feature_set import FeatureSet


class FeaturePipeline(ABC):
    """Transforms raw records into feature sets."""

    @abstractmethod
    def feature_set_id(self) -> str:
        """Return the feature set identifier."""

    @abstractmethod
    def metadata(self) -> FeatureMetadata:
        """Return feature set metadata."""

    def transform(self, records: tuple[dict[str, Any], ...]) -> FeatureSet:
        """Transform records into a feature set. Default is identity mapping."""
        metadata = self.metadata()
        return FeatureSet(
            feature_set_id=self.feature_set_id(),
            metadata=metadata.model_copy(update={"field_count": len(records)}),
            records=records,
        )


class IdentityFeaturePipeline(FeaturePipeline):
    """Identity feature pipeline for platform scaffolding."""

    def __init__(
        self,
        *,
        feature_set_id: str,
        name: str,
        version: str,
        source_dataset_id: str,
    ) -> None:
        self._feature_set_id = feature_set_id
        self._metadata = FeatureMetadata(
            feature_set_id=feature_set_id,
            name=name,
            version=version,
            source_dataset_id=source_dataset_id,
        )

    def feature_set_id(self) -> str:
        return self._feature_set_id

    def metadata(self) -> FeatureMetadata:
        return self._metadata
