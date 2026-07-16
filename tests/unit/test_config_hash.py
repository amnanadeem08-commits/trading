"""Unit tests for configuration hash generation."""

from __future__ import annotations

import pytest

from config.hash import (
    compute_configuration_hash,
    configuration_files_exist,
    list_configuration_files,
    load_merged_configuration,
)


@pytest.mark.unit
def test_configuration_files_exist() -> None:
    assert configuration_files_exist() is True


@pytest.mark.unit
def test_list_configuration_files_complete() -> None:
    files = list_configuration_files()
    assert "indicators.yaml" in files
    assert "logging.yaml" in files
    assert "services.yaml" in files
    assert "workflow.yaml" in files
    assert "plugins.yaml" in files
    assert "data.yaml" in files
    assert "core.yaml" in files
    assert "ml.yaml" in files
    assert "ai.yaml" in files
    assert "decision.yaml" in files
    assert "paper_adapter.yaml" in files
    assert "historical.yaml" in files
    assert "market_data.yaml" in files
    assert "feature_engineering.yaml" in files
    assert "feature_store.yaml" in files
    assert "training_pipeline.yaml" in files
    assert "model_registry.yaml" in files
    assert "inference_pipeline.yaml" in files
    assert "ml_runtime.yaml" in files
    assert "ml_engine.yaml" in files
    assert "framework_adapters.yaml" in files
    assert "artifact_management.yaml" in files
    assert "storage_providers.yaml" in files
    assert "portfolio_sync.yaml" in files
    assert len(files) == 34


@pytest.mark.unit
def test_compute_configuration_hash_is_stable() -> None:
    first = compute_configuration_hash()
    second = compute_configuration_hash()
    assert first == second
    assert len(first) == 64


@pytest.mark.unit
def test_load_merged_configuration_has_sections() -> None:
    merged = load_merged_configuration()
    assert "indicators" in merged
    assert "feature_flags" in merged
    assert "data" in merged
    assert "core" in merged
    assert "ml" in merged
    assert "ai" in merged
    assert "decision" in merged
    assert "paper_adapter" in merged
    assert "historical" in merged
    assert "market_data" in merged
    assert "feature_engineering" in merged
    assert "feature_store" in merged
    assert "training_pipeline" in merged
    assert "model_registry" in merged
    assert "inference_pipeline" in merged
    assert "ml_runtime" in merged
    assert "ml_engine" in merged
    assert "framework_adapters" in merged
    assert "artifact_management" in merged
    assert "storage_providers" in merged
    assert "portfolio_sync" in merged
