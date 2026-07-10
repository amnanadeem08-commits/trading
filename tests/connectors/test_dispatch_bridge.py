"""Unit tests for dispatch bridge."""

from __future__ import annotations

import pytest

from connectors import AdapterRegistry, DispatchBridge, DispatchBridgeError
from connectors.exceptions import AdapterNotFoundError
from tests.connectors_helpers import (
    FailingExecutionAdapter,
    RejectingExecutionAdapter,
    SampleExecutionAdapter,
    make_adapter_metadata,
    make_dispatch_request,
)


def test_bridge_wrap_request() -> None:
    bridge = DispatchBridge()
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="sample-adapter")
    assert wrapped.adapter_id == "sample-adapter"
    assert wrapped.request.request_id == "req-1"


def test_bridge_route_success() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    bridge = DispatchBridge(adapter_registry=registry)
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="sample-adapter")
    result = bridge.route(wrapped, SampleExecutionAdapter())
    assert result.success is True
    assert result.output["prepared"] is True


def test_bridge_route_unregistered_raises() -> None:
    bridge = DispatchBridge()
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="missing")
    with pytest.raises(AdapterNotFoundError):
        bridge.route(wrapped, SampleExecutionAdapter())


def test_bridge_route_validation_failure() -> None:
    registry = AdapterRegistry()
    registry.register(
        make_adapter_metadata(adapter_id="rejecting-adapter", capabilities=("dispatch",))
    )
    bridge = DispatchBridge(adapter_registry=registry)
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="rejecting-adapter")
    with pytest.raises(DispatchBridgeError):
        bridge.route(wrapped, RejectingExecutionAdapter())


def test_bridge_route_adapter_exception_returns_failure() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata(adapter_id="failing-adapter"))
    bridge = DispatchBridge(adapter_registry=registry)
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="failing-adapter")
    result = bridge.route(wrapped, FailingExecutionAdapter())
    assert result.success is False
    assert result.error_message is not None


def test_bridge_history_and_reset() -> None:
    registry = AdapterRegistry()
    registry.register(make_adapter_metadata())
    bridge = DispatchBridge(adapter_registry=registry)
    request = make_dispatch_request()
    wrapped = bridge.wrap_request(request, adapter_id="sample-adapter")
    bridge.route(wrapped, SampleExecutionAdapter())
    assert len(bridge.history()) == 1
    bridge.reset()
    assert bridge.history() == []
