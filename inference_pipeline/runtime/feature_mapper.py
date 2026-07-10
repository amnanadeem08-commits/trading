"""Schema-driven feature mapping for model inputs."""

from __future__ import annotations

import time
from typing import Any

from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema


class FeatureMapper:
    """Maps dataset rows to ordered model inputs using schema metadata."""

    def map_row(
        self,
        *,
        schema: InputSchema,
        features: dict[str, Any],
    ) -> tuple[list[list[float]], float]:
        """Map a feature dictionary to a single-sample input matrix."""
        started = time.monotonic() * 1000.0
        ordered_values: list[float] = []
        for spec in schema.features:
            value = self._resolve_feature_value(spec, features)
            ordered_values.append(float(value))
        matrix = [ordered_values]
        duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        return matrix, duration_ms

    def map_batch(
        self,
        *,
        schema: InputSchema,
        feature_rows: tuple[dict[str, Any], ...],
    ) -> tuple[list[list[float]], float]:
        """Prepare a batch matrix while enforcing batch_size = 1 for now."""
        if schema.batch.batch_size != 1:
            msg = "only single-sample execution is supported"
            raise ValueError(msg)
        if len(feature_rows) != 1:
            msg = "batch execution is not enabled"
            raise ValueError(msg)
        return self.map_row(schema=schema, features=feature_rows[0])

    @staticmethod
    def _resolve_feature_value(spec: FeatureSpec, features: dict[str, Any]) -> float:
        if spec.name in features:
            return float(features[spec.name])
        if spec.optional and spec.default is not None:
            return float(spec.default)
        msg = f"missing required feature: {spec.name}"
        raise ValueError(msg)
