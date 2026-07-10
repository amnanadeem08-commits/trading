"""Unit tests for inference versioning."""

from __future__ import annotations

import pytest

from inference_pipeline import InferencePipelineError, InferenceVersionRegistry


@pytest.mark.unit
def test_inference_version_registry() -> None:
    registry = InferenceVersionRegistry()
    version = registry.register(version_id="v1", pipeline_schema="1.0.0")
    assert registry.get("v1").version_id == version.version_id
    assert registry.latest() is not None
    assert len(registry.list_versions()) == 1


@pytest.mark.unit
def test_inference_version_registry_missing_raises() -> None:
    registry = InferenceVersionRegistry()
    with pytest.raises(InferencePipelineError):
        registry.get("missing")
