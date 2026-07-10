"""Helpers for inference pipeline tests."""

from __future__ import annotations

from inference_pipeline import InferenceRuntime, build_inference_runtime, prepare_production_model
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.training_pipeline_helpers import make_training_runtime


def make_inference_runtime(*, approval_required: bool = False) -> InferenceRuntime:
    training_runtime = make_training_runtime()
    registry_runtime = build_model_registry_runtime(
        training_runtime,
        approval_required=approval_required,
    )
    register_model_from_training(
        registry_runtime,
        model_id="model-1",
        model_name="Inference Model",
        experiment_id="experiment-1",
        dataset_id="dataset-1",
    )
    prepare_production_model(registry_runtime, model_id="model-1")
    return build_inference_runtime(registry_runtime)
