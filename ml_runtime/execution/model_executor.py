"""Abstract model executor interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.runtime.runtime_context import RuntimeContext


class ModelExecutor(ABC):
    """Framework-agnostic executor interface for future ML engines."""

    @abstractmethod
    def executor_id(self) -> str:
        """Return the executor identifier."""

    @abstractmethod
    def load(self, *, artifact_reference: str, metadata: dict[str, object]) -> None:
        """Load model artifacts without framework binding."""

    @abstractmethod
    def execute(self, context: RuntimeContext) -> ExecutionResult:
        """Execute a single runtime request. Returns metadata only."""

    @abstractmethod
    def execute_batch(
        self,
        contexts: tuple[RuntimeContext, ...],
    ) -> tuple[ExecutionResult, ...]:
        """Execute a batch of runtime requests."""

    @abstractmethod
    def unload(self) -> None:
        """Release loaded artifacts."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return executor health metadata."""
