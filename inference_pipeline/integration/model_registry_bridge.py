"""Model registry bridge for inference pipeline integration."""

from __future__ import annotations

from inference_pipeline.runtime.inference_runtime import (
    InferenceRuntime,
    build_inference_runtime,
    run_inference_for_model,
)
from model_registry.integration.training_pipeline_bridge import ModelRegistryRuntime
from model_registry.models.model_stage import ModelStage

__all__ = [
    "InferenceRuntime",
    "build_inference_runtime",
    "prepare_production_model",
    "run_inference_for_model",
]


def prepare_production_model(
    registry_runtime: ModelRegistryRuntime,
    *,
    model_id: str,
) -> None:
    """Promote the latest model version to production for inference."""
    version = registry_runtime.registry.latest(model_id)
    for stage in (
        ModelStage.STAGING,
        ModelStage.VALIDATION,
        ModelStage.APPROVED,
        ModelStage.PRODUCTION,
    ):
        registry_runtime.registry.promote(
            version_id=version.version_id,
            to_stage=stage,
            approved=True,
        )
        version = registry_runtime.registry.get_version(version.version_id)
