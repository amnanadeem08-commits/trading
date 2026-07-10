"""Feature extraction context."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class FeatureExtractionContext(PlatformModel):
    """Configuration for a feature extraction run."""

    pipeline_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    schema_id: str = Field(min_length=1, default="feature-schema-v1")
    extractor_id: str = Field(min_length=1, default="attribute-extractor")
    batch_size: int = Field(ge=1, default=10)
    window_size: int = Field(ge=1, default=1)
    correlation_id: str = "feature-extraction"
    trace_id: str = "feature-extraction"
    version: str = Field(min_length=1, default="1.0.0")
