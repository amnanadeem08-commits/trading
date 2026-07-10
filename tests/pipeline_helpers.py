"""Helpers for pipeline tests."""

from __future__ import annotations

from models.common import ReproducibilityKey
from pipeline.request import PipelineRequest


def make_pipeline_request(*, configuration_hash: str = "abc123") -> PipelineRequest:
    return PipelineRequest(
        configuration_hash=configuration_hash,
        feature_flags={"signal_only": True},
        metadata={"test": True},
        reproducibility_key=ReproducibilityKey(
            feature_snapshot_version="1.0.0",
            model_version="1.0.0",
            prompt_version="1.0.0",
            strategy_version="1.0.0",
            schema_version="1.0.0",
            config_hash=configuration_hash,
        ),
    )
