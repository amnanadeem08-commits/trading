"""Unit tests for pipeline registry."""

from __future__ import annotations

import pytest

from pipeline import (
    CircularStageDependencyError,
    PipelineBuilder,
    PipelineNotFoundError,
    PipelineRegistry,
    get_pipeline_registry,
    reset_pipeline_registry,
)
from tests.pipeline_fixtures import IngestStage, TransformStage


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_pipeline_registry()
    yield
    reset_pipeline_registry()


@pytest.mark.unit
def test_registry_register_resolve_list_exists() -> None:
    registry = PipelineRegistry()
    pipeline = PipelineBuilder("alpha").add_stage(IngestStage()).build()
    registry.register_pipeline(pipeline)
    assert registry.exists("alpha") is True
    assert registry.resolve("alpha").name == "alpha"
    assert registry.list() == ("alpha",)


@pytest.mark.unit
def test_registry_unregister_missing_raises() -> None:
    registry = PipelineRegistry()
    with pytest.raises(PipelineNotFoundError):
        registry.unregister_pipeline("missing")


@pytest.mark.unit
def test_registry_validate_execution_order() -> None:
    registry = PipelineRegistry()
    pipeline = (
        PipelineBuilder("ordered").add_stage(TransformStage()).add_stage(IngestStage()).build()
    )
    validation = registry.validate(pipeline)
    assert validation.valid is True
    assert validation.execution_order == ("ingest", "transform")


@pytest.mark.unit
def test_registry_validate_cycle_raises() -> None:
    registry = PipelineRegistry()

    class _CycleA(IngestStage):
        def name(self) -> str:
            return "cycle-a"

        def dependencies(self) -> tuple[str, ...]:
            return ("cycle-b",)

    class _CycleB(IngestStage):
        def name(self) -> str:
            return "cycle-b"

        def dependencies(self) -> tuple[str, ...]:
            return ("cycle-a",)

    pipeline = PipelineBuilder("cycle").add_stage(_CycleA()).add_stage(_CycleB()).build()
    with pytest.raises(CircularStageDependencyError):
        registry.validate(pipeline)


@pytest.mark.unit
def test_get_pipeline_registry_singleton() -> None:
    assert get_pipeline_registry() is get_pipeline_registry()
