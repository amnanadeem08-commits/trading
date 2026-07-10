"""Unit tests for ML model versioning."""

from __future__ import annotations

import pytest

from ml import ModelVersion
from versioning.model_registry import reset_model_registry


@pytest.fixture(autouse=True)
def _reset_version_registry() -> None:
    reset_model_registry()
    yield
    reset_model_registry()


@pytest.mark.unit
def test_model_version_register_and_list() -> None:
    version = ModelVersion(
        model_id="sample-model",
        version_id="1.0.0",
        description="initial",
    )
    version.register()
    versions = ModelVersion.list_versions()
    assert len(versions) == 1
    assert versions[0].version_id == "1.0.0"


@pytest.mark.unit
def test_model_version_current() -> None:
    ModelVersion(model_id="sample-model", version_id="1.0.0").register()
    current = ModelVersion.current("sample-model")
    assert current is not None
    assert current.version_id == "1.0.0"
