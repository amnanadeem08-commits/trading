"""Helpers for inference execution pipeline tests."""

from __future__ import annotations

from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema, OutputType


def make_identity_input_schema() -> InputSchema:
    return InputSchema(
        features=(FeatureSpec(name="X", dtype="float32", shape=(1,)),),
        output_type=OutputType.REGRESSION,
        schema_version="1.0.0",
    )
