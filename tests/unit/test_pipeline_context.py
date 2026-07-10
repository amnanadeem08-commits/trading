"""Unit tests for pipeline context."""

from __future__ import annotations

import pytest

from pipeline import PipelineContext, build_pipeline_context
from services import reset_application_context


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_pipeline_context_exposes_required_dependencies() -> None:
    context = build_pipeline_context()
    assert isinstance(context, PipelineContext)
    assert context.settings is not None
    assert context.application is not None
    assert context.event_bus is not None
    assert context.metrics is not None
    assert context.health is not None
    assert context.audit is not None
    assert context.version_registry is not None


@pytest.mark.unit
def test_pipeline_context_surface_fields() -> None:
    fields = set(PipelineContext.__dataclass_fields__)
    assert fields == {"settings", "application"}
