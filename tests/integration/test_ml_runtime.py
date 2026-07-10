"""Integration tests for ML layer runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from ml import (
    InMemoryEvaluator,
    InMemoryPredictor,
    InMemoryTrainer,
    MLLifecycleEventType,
    MLLifecycleManager,
    MLRegistry,
    ModelLifecycleState,
    get_ml_registry,
    reset_ml_registry,
)
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.ml_helpers import SampleMLModel, make_model_metadata


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_ml_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_ml_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_ml_runtime_train_infer_evaluate_flow() -> None:
    settings = get_settings()
    assert settings.ml.training_enabled is True
    assert settings.ml.inference_enabled is True

    bus = EventBus()
    application = build_application_context()
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    context = build_pipeline_context(updated_app)
    core_runtime = CoreRuntime(context=context)
    core_context = core_runtime.build_context(
        operation_type="ml_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = MLLifecycleManager(context)

    registry = MLRegistry()
    metadata = make_model_metadata()
    registry.register_model(metadata)
    registry.register_model_type(SampleMLModel)

    lifecycle.emit(
        MLLifecycleEventType.MODEL_REGISTERED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="model registered",
    )

    trainer = InMemoryTrainer()
    job = trainer.create_job(model_id="sample-model", dataset_id="records")
    lifecycle.emit(
        MLLifecycleEventType.TRAINING_STARTED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="training started",
    )
    training_result = trainer.run(job, SampleMLModel())
    registry.track_job(trainer.get_job(job.job_id) or job)
    lifecycle.emit(
        MLLifecycleEventType.TRAINING_COMPLETED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="training completed",
    )

    predictor = InMemoryPredictor()
    lifecycle.emit(
        MLLifecycleEventType.INFERENCE_STARTED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="inference started",
    )
    prediction = predictor.predict(
        SampleMLModel(),
        inputs=({"id": "1", "value": 10},),
    )
    lifecycle.emit(
        MLLifecycleEventType.INFERENCE_COMPLETED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="inference completed",
    )

    evaluator = InMemoryEvaluator()
    evaluation = evaluator.evaluate(
        SampleMLModel(),
        dataset_id="records",
        predictions=prediction.outputs,
    )
    lifecycle.emit(
        MLLifecycleEventType.EVALUATION_COMPLETED,
        model_id="sample-model",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="evaluation completed",
    )

    assert training_result.state.value == "completed"
    assert len(prediction.outputs) == 1
    assert evaluation.metrics.values["accuracy"] == 0.95
    assert registry.get_state("sample-model") == ModelLifecycleState.READY
    assert bus.persistence.count() >= 6


@pytest.mark.integration
def test_ml_runtime_singleton_registry() -> None:
    registry = get_ml_registry()
    registry.register_model(make_model_metadata(model_id="singleton"))
    assert get_ml_registry().list_models() == ("singleton",)
