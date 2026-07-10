"""Unit tests for model registry runtime."""

from __future__ import annotations

import pytest

from model_registry import ModelStage, register_model_from_training
from tests.model_registry_helpers import make_registry_runtime


@pytest.mark.unit
def test_runtime_register_and_ingest() -> None:
    runtime = make_registry_runtime()
    runtime.register_model(model_id="model-1", name="Baseline")
    from training_pipeline import schedule_training_from_dataset

    result = schedule_training_from_dataset(
        runtime.training_runtime,
        experiment_id="exp-1",
        model_family="baseline",
        dataset_id="dataset-1",
    )
    version = runtime.ingest_training_result(
        model_id="model-1",
        training_result=result,
        experiment_id="exp-1",
    )
    assert version.model_id == "model-1"
    assert len(runtime.lineage.nodes()) >= 6


@pytest.mark.unit
def test_register_model_from_training_helper() -> None:
    runtime = make_registry_runtime()
    registry = register_model_from_training(
        runtime,
        model_id="model-2",
        model_name="Helper Model",
        experiment_id="exp-2",
        dataset_id="dataset-1",
    )
    assert registry.lookup("model-2").latest_version_id is not None


@pytest.mark.unit
def test_runtime_promote_version() -> None:
    runtime = make_registry_runtime(approval_required=False)
    register_model_from_training(
        runtime,
        model_id="model-3",
        model_name="Promoted",
        experiment_id="exp-3",
        dataset_id="dataset-1",
    )
    version = runtime.registry.latest("model-3")
    promoted = runtime.promote_version(
        version_id=version.version_id,
        to_stage=ModelStage.STAGING,
    )
    assert promoted.stage == ModelStage.STAGING
