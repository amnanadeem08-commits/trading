"""Integration tests for feature store runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from feature_engineering import reset_feature_registry, run_extraction_from_stream
from feature_store import (
    FeatureStore,
    FeatureStoreLifecycleManager,
    build_reproducible_dataset,
    ingest_feature_set,
    reset_feature_store_registry,
)
from historical import reset_historical_registry
from market_data import reset_market_data_registry
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.feature_engineering_helpers import seed_historical_and_stream


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_historical_registry()
    reset_market_data_registry()
    reset_feature_registry()
    reset_feature_store_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_historical_registry()
    reset_market_data_registry()
    reset_feature_registry()
    reset_feature_store_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_feature_store_runtime_full_flow() -> None:
    settings = get_settings()
    assert settings.feature_store.validation_enabled is True
    assert settings.feature_store.cache_enabled is True
    assert settings.feature_store.snapshot_enabled is True

    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    validation = store.validate_dataset("dataset-1")
    assert validation.valid is True

    snapshot = store.create_snapshot("dataset-1")
    offline = store.load_offline("dataset-1")
    assert len(offline) == 3
    assert dataset.checksum == snapshot.checksum

    reproducible = build_reproducible_dataset(store, extraction.feature_set)
    assert "reproducible" in reproducible.tags

    bus = EventBus()
    metrics = build_application_context().metrics
    lifecycle = FeatureStoreLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit_dataset_created(
        dataset_id="dataset-1",
        version="1.0.0",
        correlation_id="corr-store",
        trace_id="trace-store",
    )
    lifecycle.emit_snapshot_created(
        snapshot_id=snapshot.snapshot_id,
        dataset_id="dataset-1",
        correlation_id="corr-store",
        trace_id="trace-store",
    )
    lifecycle.emit_dataset_validated(
        dataset_id="dataset-1",
        valid=True,
        correlation_id="corr-store",
        trace_id="trace-store",
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
        operation_type="feature_store_pipeline",
        dataset_ids=("dataset-1",),
    )

    assert store.catalog.lookup("dataset-1").capabilities == ("offline", "online", "snapshot")
    assert len(lifecycle.events) == 3
    assert core_context.audit.attributes.get("action_recorded") == "feature_store_pipeline"
