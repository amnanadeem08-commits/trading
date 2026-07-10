"""Pipeline stage contract and hook types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pipeline.context import PipelineContext
from pipeline.request import PipelineRequest
from pipeline.result import StageResult

type StageHook = Callable[[PipelineContext, PipelineRequest, PipelineStage], None]
type BeforeStageHook = Callable[[PipelineContext, PipelineRequest, PipelineStage], None]
type AfterStageHook = Callable[[PipelineContext, PipelineRequest, PipelineStage, StageResult], None]


class RetryPolicy(ABC):
    """Retry policy interface. Implementations are out of scope for foundation."""

    @abstractmethod
    def should_retry(self, *, attempt: int, error: Exception) -> bool:
        """Return whether another attempt should be made."""

    @abstractmethod
    def max_attempts(self) -> int:
        """Return the maximum number of attempts allowed."""


class PipelineStage(ABC):
    """Contract implemented by every pipeline stage."""

    @abstractmethod
    def name(self) -> str:
        """Return the unique stage identifier."""

    @abstractmethod
    def version(self) -> str:
        """Return the stage version string."""

    @abstractmethod
    def dependencies(self) -> tuple[str, ...]:
        """Return stage names this stage depends on."""

    @abstractmethod
    def validate(self, context: PipelineContext, request: PipelineRequest) -> None:
        """Validate stage preconditions before execution."""

    @abstractmethod
    def execute(
        self,
        context: PipelineContext,
        request: PipelineRequest,
    ) -> StageResult:
        """Execute the stage and return its result."""

    @abstractmethod
    def rollback(self, context: PipelineContext, request: PipelineRequest) -> None:
        """Rollback stage side effects after failure."""

    @abstractmethod
    def cleanup(self, context: PipelineContext, request: PipelineRequest) -> None:
        """Cleanup stage resources after execution or rollback."""

    def metrics_snapshot(self) -> dict[str, Any]:
        """Return optional stage metrics metadata."""
        return {}
