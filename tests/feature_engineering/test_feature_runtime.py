"""Integration tests for feature engineering runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from feature_engineering import (
    FeatureLifecycleEventType,
    FeatureLifecycleManager,
    FeatureRegistry,
    FeatureSchemaRegistry,
    FeatureSchemaValidator,
    FeatureValidator,
    FeatureVersionRegistry,
    NonEmptyVectorRule,
    build_pipeline_from_stream,
    register_feature_from_schema,
    register_version_from_schema,
    reset_feature_registry,
    run_extraction_from_stream,
)
from historical import reset_historical_registry
from market_data import reset_market_data_registry
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.feature_engineering_helpers import make_feature_schema, seed_historical_and_stream


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_historical_registry()
    reset_market_data_registry()
    reset_feature_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_historical_registry()
    reset_market_data_registry()
    reset_feature_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_feature_engineering_runtime_full_flow() -> None:
    settings = get_settings()
    assert settings.feature_engineering.validation_enabled is True
    assert settings.feature_engineering.extraction_enabled is True
    assert settings.feature_engineering.batch_size == 10

    _, stream = seed_historical_and_stream(record_count=3)
    pipeline = build_pipeline_from_stream(stream, pipeline_id="feature-runtime")
    result = run_extraction_from_stream(stream, pipeline_id="feature-runtime", max_batches=1)

    assert result.vectors_extracted == 3
    assert result.completed is True
    assert result.feature_set is not None
    assert len(result.feature_set.vectors) == 3

    schema_registry = FeatureSchemaRegistry()
    feature_registry = FeatureRegistry()
    schema = make_feature_schema()
    register_feature_from_schema(
        schema_registry,
        feature_registry,
        schema=schema,
        feature_id="feature-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
    )

    version_registry = FeatureVersionRegistry()
    register_version_from_schema(
        schema,
        version_registry,
        feature_id="feature-1",
        snapshot_id="snap-1",
    )

    validator = FeatureValidator(rules=(NonEmptyVectorRule(),))
    validation = validator.validate_set(result.feature_set)
    assert validation.valid is True

    schema_validator = FeatureSchemaValidator()
    schema_result = schema_validator.validate_batch(
        result.feature_set.vectors,
        schema=schema,
    )
    assert schema_result.valid is True

    bus = EventBus()
    metrics = build_application_context().metrics
    lifecycle = FeatureLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit(
        FeatureLifecycleEventType.EXTRACTION_COMPLETED,
        dataset_id="dataset-1",
        correlation_id="corr-feature",
        trace_id="trace-feature",
        message="extraction completed",
        payload={"vectors_extracted": result.vectors_extracted},
    )

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
        operation_type="feature_engineering_pipeline",
        dataset_ids=("dataset-1",),
    )

    assert feature_registry.exists("feature-1") is True
    assert version_registry.latest("feature-1").version == "1.0.0"
    assert len(lifecycle.events) == 1
    assert core_context.audit.attributes.get("action_recorded") == "feature_engineering_pipeline"
    assert pipeline.context.pipeline_id == "feature-runtime"
