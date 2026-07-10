"""Integration tests for model registry runtime."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from model_registry import ModelStage, build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
from training_pipeline import build_training_runtime


@pytest.mark.integration
def test_training_pipeline_to_model_registry_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)

    register_model_from_training(
        registry_runtime,
        model_id="integration-model",
        model_name="Integration Model",
        experiment_id="integration-exp",
        dataset_id=dataset.dataset_id,
    )

    model = registry_runtime.registry.lookup("integration-model")
    version = registry_runtime.registry.latest("integration-model")
    assert model.latest_version_id == version.version_id
    assert version.dataset_id == dataset.dataset_id
    assert len(registry_runtime.lineage.nodes()) >= 6


@pytest.mark.integration
def test_model_registry_promotion_and_catalog() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)

    register_model_from_training(
        registry_runtime,
        model_id="promotion-model",
        model_name="Promotion Model",
        experiment_id="promotion-exp",
        dataset_id="dataset-1",
    )

    version = registry_runtime.registry.latest("promotion-model")
    promoted = registry_runtime.registry.promote(
        version_id=version.version_id,
        to_stage=ModelStage.STAGING,
    )
    catalog_entry = registry_runtime.registry.catalog.get("promotion-model")
    assert catalog_entry is not None
    assert promoted.stage == ModelStage.STAGING
    assert len(catalog_entry.versions) == 1
