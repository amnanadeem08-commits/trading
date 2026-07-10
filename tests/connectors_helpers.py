"""Helpers for connector framework tests."""

from __future__ import annotations

from typing import Any

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_metadata import (
    AdapterHealthResult,
    AdapterHealthStatus,
    AdapterMetadata,
)
from connectors.adapters.execution_adapter import ExecutionAdapter
from execution.dispatch.dispatch_request import DispatchRequest
from execution.engine.execution_context import ExecutionContext
from tests.execution_helpers import make_execution_context


def make_adapter_metadata(
    *,
    adapter_id: str = "sample-adapter",
    name: str = "Sample Adapter",
    version: str = "1.0.0",
    capabilities: tuple[str, ...] = ("dispatch",),
) -> AdapterMetadata:
    return AdapterMetadata(
        adapter_id=adapter_id,
        name=name,
        version=version,
        capabilities=capabilities,
        tags=("test",),
    )


class SampleExecutionAdapter(ExecutionAdapter):
    """Concrete execution adapter used in unit tests."""

    def adapter_id(self) -> str:
        return "sample-adapter"

    def name(self) -> str:
        return "Sample Adapter"

    def version(self) -> str:
        return "1.0.0"

    def metadata(self) -> AdapterMetadata:
        return make_adapter_metadata()

    def initialize(self, context: AdapterContext) -> None:
        return None

    def validate(self, context: AdapterContext) -> bool:
        return True

    def dispatch(self, context: AdapterContext) -> dict[str, Any]:
        return {
            "prepared": True,
            "adapter_id": self.adapter_id(),
            "execution_id": context.execution_id,
        }

    def shutdown(self, context: AdapterContext) -> None:
        return None

    def health(self) -> AdapterHealthResult:
        return AdapterHealthResult(
            adapter_id=self.adapter_id(),
            status=AdapterHealthStatus.HEALTHY,
            message="ok",
        )


class FailingExecutionAdapter(ExecutionAdapter):
    """Adapter that fails during dispatch."""

    def adapter_id(self) -> str:
        return "failing-adapter"

    def name(self) -> str:
        return "Failing Adapter"

    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: AdapterContext) -> None:
        return None

    def validate(self, context: AdapterContext) -> bool:
        return True

    def dispatch(self, context: AdapterContext) -> dict[str, Any]:
        raise RuntimeError("adapter dispatch failed")

    def shutdown(self, context: AdapterContext) -> None:
        return None

    def health(self) -> AdapterHealthResult:
        return AdapterHealthResult(
            adapter_id=self.adapter_id(),
            status=AdapterHealthStatus.UNHEALTHY,
        )


class RejectingExecutionAdapter(ExecutionAdapter):
    """Adapter that fails validation."""

    def adapter_id(self) -> str:
        return "rejecting-adapter"

    def name(self) -> str:
        return "Rejecting Adapter"

    def version(self) -> str:
        return "1.0.0"

    def initialize(self, context: AdapterContext) -> None:
        return None

    def validate(self, context: AdapterContext) -> bool:
        return False

    def dispatch(self, context: AdapterContext) -> dict[str, Any]:
        return {}

    def shutdown(self, context: AdapterContext) -> None:
        return None

    def health(self) -> AdapterHealthResult:
        return AdapterHealthResult(adapter_id=self.adapter_id())


def make_dispatch_request(
    *,
    request_id: str = "req-1",
    execution_id: str = "exec-1",
    engine_id: str = "sample-engine",
) -> DispatchRequest:
    context = make_execution_context(execution_id=execution_id)
    return DispatchRequest(
        request_id=request_id,
        execution_id=execution_id,
        engine_id=engine_id,
        context=context,
        payload={"record_id": "1"},
    )


def make_adapter_context(
    *,
    adapter_id: str = "sample-adapter",
    execution_id: str = "exec-1",
) -> AdapterContext:
    return AdapterContext(
        adapter_id=adapter_id,
        correlation_id="corr-1",
        trace_id="trace-1",
        execution_id=execution_id,
        request_id="req-1",
        execution_context=ExecutionContext(
            execution_id=execution_id,
            correlation_id="corr-1",
            trace_id="trace-1",
        ),
        payload={"record_id": "1"},
    )
