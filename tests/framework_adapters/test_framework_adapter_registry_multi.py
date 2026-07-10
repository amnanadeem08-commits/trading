"""Unit tests for expanded adapter registry."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterNotFoundError,
    AdapterRegistry,
    EngineType,
    MetadataFrameworkAdapter,
    create_stub_adapter,
)


@pytest.mark.unit
def test_registry_supports_multiple_adapters_per_engine_type() -> None:
    registry = AdapterRegistry()
    low_priority = MetadataFrameworkAdapter(
        adapter_id="stub-low",
        name="Stub Low",
        version="1.0.0",
        engine_type=EngineType.STUB,
        priority=10,
    )
    high_priority = MetadataFrameworkAdapter(
        adapter_id="stub-high",
        name="Stub High",
        version="1.0.0",
        engine_type=EngineType.STUB,
        priority=100,
    )
    registry.register(low_priority, priority=10)
    registry.register(high_priority, priority=100)

    records = registry.list_by_engine_type(EngineType.STUB)
    assert [record.adapter_id for record in records] == ["stub-high", "stub-low"]


@pytest.mark.unit
def test_registry_default_adapter_and_unregister() -> None:
    registry = AdapterRegistry()
    adapter = create_stub_adapter()
    registry.register(adapter)
    registry.set_default_adapter(adapter.adapter_id())
    assert registry.get_default_adapter_id() == adapter.adapter_id()

    registry.unregister(adapter.adapter_id())
    assert registry.list_by_engine_type(EngineType.STUB) == ()
    assert registry.get_default_adapter_id() is None

    with pytest.raises(AdapterNotFoundError):
        registry.lookup(adapter.adapter_id())
