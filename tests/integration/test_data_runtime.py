"""Integration tests for data layer runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from data import (
    DatasetLifecycleEventType,
    DatasetLifecycleManager,
    DatasetRegistry,
    InMemoryDatasetLoader,
    InMemoryDatasetRepository,
    LineageTracker,
    ProvenanceTracker,
    get_dataset_registry,
    reset_dataset_registry,
)
from pipeline import build_pipeline_context
from services import reset_application_context
from tests.data_helpers import RecordsDataset, make_dataset


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_dataset_registry()
    reset_settings()
    yield
    reset_application_context()
    reset_dataset_registry()
    reset_settings()


@pytest.mark.integration
def test_data_runtime_register_validate_load() -> None:
    settings = get_settings()
    assert settings.data.validation_enabled is True
    assert settings.data.cache_enabled is True

    registry = DatasetRegistry()
    repository = InMemoryDatasetRepository()
    loader = InMemoryDatasetLoader()
    implementation = RecordsDataset()
    loader.register_implementation(implementation)

    dataset = make_dataset(dataset_id="records")
    registry.register(dataset)
    repository.add(dataset)

    validation = registry.validate(dataset)
    assert validation.valid is True

    result = loader.load(dataset)
    assert result.record_count == 2
    assert registry.list() == ("records",)
    assert repository.list() == ("records",)


@pytest.mark.integration
def test_data_runtime_lifecycle_lineage_provenance() -> None:
    context = build_pipeline_context()
    lifecycle = DatasetLifecycleManager(context)
    lineage = LineageTracker()
    provenance = ProvenanceTracker()

    lifecycle.emit(
        DatasetLifecycleEventType.DATASET_LOAD_COMPLETED,
        dataset_id="records",
        dataset_version="1.0.0",
        correlation_id="runtime-corr",
        message="loaded",
    )
    lineage.record(
        dataset_id="records",
        operation="load",
        correlation_id="runtime-corr",
    )
    provenance.record(
        dataset_id="records",
        version="1.0.0",
        producer="integration-test",
        configuration_hash=context.settings.schema_version,
        correlation_id="runtime-corr",
    )

    assert len(lifecycle.events) == 1
    assert len(lineage.list_for_dataset("records")) == 1
    assert provenance.latest_for_dataset("records") is not None


@pytest.mark.integration
def test_data_runtime_singleton_registry() -> None:
    registry = get_dataset_registry()
    dataset = make_dataset(dataset_id="singleton")
    registry.register(dataset)
    assert get_dataset_registry().exists("singleton") is True
