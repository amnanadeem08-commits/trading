"""Execution routing protocol for adapter runtime integration."""

from __future__ import annotations

from typing import Protocol

from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.runtime.inference_context import InferenceExecutionContext


class ExecutionOutcome(Protocol):
    """Protocol for execution results without importing ML runtime types."""

    @property
    def status(self) -> str: ...

    @property
    def message(self) -> str: ...

    @property
    def attributes(self) -> dict[str, object]: ...


class ExecutionRouter(Protocol):
    """Routes orchestrated inference through the adapter runtime."""

    def route(
        self,
        inference_response: InferenceResponse,
        *,
        execution_context: InferenceExecutionContext,
        bound_input: dict[str, object],
    ) -> ExecutionOutcome: ...


class ExecutionOutcomeAdapter:
    """Adapter wrapping a generic execution result mapping."""

    def __init__(
        self,
        *,
        status: str,
        message: str = "",
        attributes: dict[str, object] | None = None,
    ) -> None:
        self._status = status
        self._message = message
        self._attributes = attributes or {}

    @property
    def status(self) -> str:
        return self._status

    @property
    def message(self) -> str:
        return self._message

    @property
    def attributes(self) -> dict[str, object]:
        return self._attributes
