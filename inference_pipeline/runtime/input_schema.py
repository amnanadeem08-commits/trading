"""Schema contracts for model input binding."""

from __future__ import annotations

from enum import StrEnum

from inference_pipeline.runtime.batch_config import BatchConfig
from models.common import PlatformModel


class OutputType(StrEnum):
    """Supported normalized output categories."""

    REGRESSION = "regression"
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS = "multiclass"
    PROBABILITY_VECTOR = "probability_vector"


class FeatureSpec(PlatformModel):
    """Metadata for a single model input feature."""

    name: str
    dtype: str = "float32"
    shape: tuple[int, ...] = ()
    optional: bool = False
    default: float | int | None = None


class InputSchema(PlatformModel):
    """Schema-driven model input definition."""

    features: tuple[FeatureSpec, ...]
    output_type: OutputType = OutputType.REGRESSION
    batch: BatchConfig = BatchConfig()
    schema_version: str = "1.0.0"
