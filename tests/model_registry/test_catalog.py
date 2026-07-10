"""Unit tests for model catalog."""

from __future__ import annotations

import pytest

from model_registry import ModelCatalog, ModelRegistry
from tests.model_registry_helpers import make_registered_model, seed_trained_model


@pytest.mark.unit
def test_catalog_lists_models_and_versions() -> None:
    runtime = seed_trained_model()
    catalog = runtime.registry.catalog
    models = catalog.list_models()
    assert len(models) == 1
    versions = catalog.list_versions("model-1")
    assert len(versions) == 1


@pytest.mark.unit
def test_catalog_metadata_and_all_versions() -> None:
    runtime = seed_trained_model()
    catalog = runtime.registry.catalog
    metadata = catalog.list_metadata()
    assert metadata[0].model_id == "model-1"
    assert len(catalog.list_all_versions()) == 1


@pytest.mark.unit
def test_catalog_standalone_upsert() -> None:
    catalog = ModelCatalog()
    registry = ModelRegistry()
    model = make_registered_model()
    registry.register_model(model)
    catalog.upsert(model, ())
    assert catalog.get("model-1") is not None
