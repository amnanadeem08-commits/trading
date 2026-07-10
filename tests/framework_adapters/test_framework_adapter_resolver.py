"""Unit tests for adapter resolver."""

from __future__ import annotations

import pytest

from framework_adapters import AdapterResolutionError, EngineType
from tests.framework_adapters_helpers import make_resolver_with_stub


@pytest.mark.unit
def test_adapter_resolver_resolve_stub() -> None:
    resolver = make_resolver_with_stub()
    adapter = resolver.resolve(engine_type=EngineType.STUB)
    assert adapter.engine_type() == EngineType.STUB


@pytest.mark.unit
def test_adapter_resolver_resolve_engine_type() -> None:
    resolver = make_resolver_with_stub()
    assert resolver.resolve_engine_type("stub") == EngineType.STUB


@pytest.mark.unit
def test_adapter_resolver_unknown_engine_type() -> None:
    resolver = make_resolver_with_stub()
    with pytest.raises(AdapterResolutionError):
        resolver.resolve_engine_type("unknown-engine")
