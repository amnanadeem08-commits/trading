"""Helpers for model registry tests."""

from __future__ import annotations

from model_registry import (
    ModelRegistry,
    ModelRegistryRuntime,
    RegisteredModel,
    build_model_registry_runtime,
)
from tests.training_pipeline_helpers import make_training_runtime


def make_model_registry() -> ModelRegistry:
    return ModelRegistry()


def make_registered_model(
    *,
    model_id: str = "model-1",
    name: str = "Baseline Model",
) -> RegisteredModel:
    return RegisteredModel.create(model_id=model_id, name=name)


def make_registry_runtime(*, approval_required: bool = False) -> ModelRegistryRuntime:
    training_runtime = make_training_runtime()
    return build_model_registry_runtime(training_runtime, approval_required=approval_required)


def seed_trained_model(
    *,
    model_id: str = "model-1",
    experiment_id: str = "experiment-1",
    approval_required: bool = False,
) -> ModelRegistryRuntime:
    runtime = make_registry_runtime(approval_required=approval_required)
    register_model_from_training(
        runtime,
        model_id=model_id,
        model_name="Baseline Model",
        experiment_id=experiment_id,
        dataset_id="dataset-1",
    )
    return runtime


from model_registry import register_model_from_training  # noqa: E402
