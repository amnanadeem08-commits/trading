"""Feature binding helpers for execution requests."""

from __future__ import annotations

from typing import Any

from inference_pipeline.runtime.feature_mapper import FeatureMapper
from inference_pipeline.runtime.input_schema import InputSchema


class FeatureBinding:
    """Binds feature rows to model input payloads."""

    def __init__(self, *, mapper: FeatureMapper | None = None) -> None:
        self._mapper = mapper or FeatureMapper()

    def bind(
        self,
        *,
        schema: InputSchema,
        features: dict[str, Any],
    ) -> tuple[dict[str, object], float]:
        matrix, duration_ms = self._mapper.map_row(schema=schema, features=features)
        payload = {
            "input": matrix,
            "feature_names": [spec.name for spec in schema.features],
            "dtype": schema.features[0].dtype if schema.features else "float32",
            "batch_size": schema.batch.batch_size,
            "batch_dimension": schema.batch.batch_dimension,
        }
        return payload, duration_ms
