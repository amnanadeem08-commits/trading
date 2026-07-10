"""Unit tests for pipeline validation."""

from __future__ import annotations

import pytest

from pipeline import CircularStageDependencyError, validate_pipeline_stages
from tests.pipeline_fixtures import IngestStage, TransformStage


@pytest.mark.unit
def test_validate_missing_dependency() -> None:
    result = validate_pipeline_stages({"transform": TransformStage()})
    assert result.valid is False
    assert any("Missing dependency" in error for error in result.errors)


@pytest.mark.unit
def test_validate_duplicate_names_in_graph() -> None:
    class _Mismatch(IngestStage):
        def name(self) -> str:
            return "other"

    result = validate_pipeline_stages({"ingest": _Mismatch()})
    assert result.valid is False
    assert any("name mismatch" in error for error in result.errors)


@pytest.mark.unit
def test_validate_self_dependency() -> None:
    class _Self(IngestStage):
        def dependencies(self) -> tuple[str, ...]:
            return ("ingest",)

    result = validate_pipeline_stages({"ingest": _Self()})
    assert result.valid is False
    assert any("depends on itself" in error for error in result.errors)


@pytest.mark.unit
def test_validate_cycle_raises() -> None:
    class _A(IngestStage):
        def name(self) -> str:
            return "a"

        def dependencies(self) -> tuple[str, ...]:
            return ("b",)

    class _B(IngestStage):
        def name(self) -> str:
            return "b"

        def dependencies(self) -> tuple[str, ...]:
            return ("a",)

    with pytest.raises(CircularStageDependencyError):
        validate_pipeline_stages({"a": _A(), "b": _B()})
