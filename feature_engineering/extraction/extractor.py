"""Generic feature extractor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from feature_engineering.extraction.extraction_context import FeatureExtractionContext
from feature_engineering.models.feature import Feature
from feature_engineering.models.feature_vector import FeatureVector
from market_data.models.market_record import MarketRecord


def _coerce_value(raw: str) -> float | str | int | bool:
    """Coerce a string attribute value to a primitive type."""
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


class FeatureExtractor(ABC):
    """Base contract for market-record feature extractors."""

    @abstractmethod
    def extractor_id(self) -> str:
        """Return the extractor identifier."""

    @abstractmethod
    def extract(
        self,
        record: MarketRecord,
        *,
        context: FeatureExtractionContext,
    ) -> FeatureVector:
        """Extract a feature vector from a market record."""


class AttributeFeatureExtractor(FeatureExtractor):
    """Extracts generic features from market record attributes."""

    def __init__(self, *, field_names: tuple[str, ...] | None = None) -> None:
        self._field_names = field_names

    def extractor_id(self) -> str:
        return "attribute-extractor"

    def extract(
        self,
        record: MarketRecord,
        *,
        context: FeatureExtractionContext,
    ) -> FeatureVector:
        fields = self._field_names or tuple(sorted(record.attributes.keys()))
        features: list[Feature] = []
        for name in fields:
            if name not in record.attributes:
                continue
            raw = record.attributes[name]
            value = _coerce_value(raw)
            dtype = type(value).__name__
            features.append(Feature(name=name, value=value, dtype=dtype, source_field=name))
        return FeatureVector(
            vector_id=str(uuid4()),
            dataset_id=context.dataset_id,
            symbol_id=context.symbol_id,
            record_id=record.record_id,
            features=tuple(features),
            timestamp=record.timestamp,
            sequence=record.sequence,
            version=context.version,
        )
