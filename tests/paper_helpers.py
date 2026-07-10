"""Helpers for paper adapter tests."""

from __future__ import annotations

from connectors.adapters.adapter_metadata import AdapterMetadata
from connectors.adapters.paper.paper_adapter import PAPER_ADAPTER_ID, PaperExecutionAdapter
from connectors.adapters.paper.paper_settings import PaperSettings
from tests.connectors_helpers import make_adapter_context


def make_paper_settings(**overrides: object) -> PaperSettings:
    """Build paper settings with optional overrides."""
    defaults = PaperSettings().model_dump()
    defaults.update(overrides)
    return PaperSettings(**defaults)


def make_paper_adapter(**overrides: object) -> PaperExecutionAdapter:
    """Build a paper execution adapter for tests."""
    settings = overrides.pop("settings", None)
    engine = overrides.pop("engine", None)
    validator = overrides.pop("validator", None)
    return PaperExecutionAdapter(
        settings=settings or make_paper_settings(),
        engine=engine,
        validator=validator,
    )


def make_paper_adapter_metadata() -> AdapterMetadata:
    """Build adapter metadata for paper adapter registration."""
    return AdapterMetadata(
        adapter_id=PAPER_ADAPTER_ID,
        name="Paper Execution Adapter",
        version="1.0.0",
        capabilities=("dispatch", "simulate"),
        tags=("paper", "simulation"),
        attributes={"mode": "offline"},
    )


def make_paper_adapter_context(
    *,
    adapter_id: str = PAPER_ADAPTER_ID,
    execution_id: str = "exec-1",
):
    """Build adapter context configured for the paper adapter."""
    return make_adapter_context(adapter_id=adapter_id, execution_id=execution_id)
