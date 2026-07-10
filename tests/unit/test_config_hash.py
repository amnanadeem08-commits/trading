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
    assert len(files) == 21


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
