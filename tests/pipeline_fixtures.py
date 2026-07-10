"""Test pipeline stage implementations."""

from __future__ import annotations

from pipeline.context import PipelineContext
from pipeline.decorators import stage
from pipeline.request import PipelineRequest
from pipeline.result import StageResult, StageStatus
from pipeline.stage import PipelineStage


@stage(name="ingest", auto_register=False)
class IngestStage(PipelineStage):
    """Primary test stage with no dependencies."""

    def __init__(self) -> None:
        self._executed = False
        self._rolled_back = False
        self._cleaned = False
        self._fail_execute = False
        self._fail_validate = False

    def name(self) -> str:
        return "ingest"

    def version(self) -> str:
        return "1.0.0"

    def dependencies(self) -> tuple[str, ...]:
        return ()

    def validate(self, context: PipelineContext, request: PipelineRequest) -> None:
        if self._fail_validate:
            msg = "ingest validation failed"
            raise ValueError(msg)

    def execute(self, context: PipelineContext, request: PipelineRequest) -> StageResult:
        if self._fail_execute:
            msg = "ingest execution failed"
            raise RuntimeError(msg)
        self._executed = True
        context.metrics.counter("pipeline.stage.ingest.runs").inc(1)
        return StageResult(
            stage_name=self.name(),
            stage_version=self.version(),
            status=StageStatus.COMPLETED,
            message="ingested",
        )

    def rollback(self, context: PipelineContext, request: PipelineRequest) -> None:
        self._rolled_back = True

    def cleanup(self, context: PipelineContext, request: PipelineRequest) -> None:
        self._cleaned = True


@stage(name="transform", auto_register=False)
class TransformStage(PipelineStage):
    """Dependent test stage."""

    def __init__(self) -> None:
        self._executed = False

    def name(self) -> str:
        return "transform"

    def version(self) -> str:
        return "1.0.0"

    def dependencies(self) -> tuple[str, ...]:
        return ("ingest",)

    def validate(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None

    def execute(self, context: PipelineContext, request: PipelineRequest) -> StageResult:
        self._executed = True
        return StageResult(
            stage_name=self.name(),
            stage_version=self.version(),
            status=StageStatus.COMPLETED,
            message="transformed",
        )

    def rollback(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None

    def cleanup(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None


@stage(name="publish", auto_register=True)
class PublishStage(PipelineStage):
    """Auto-registerable test stage."""

    def name(self) -> str:
        return "publish"

    def version(self) -> str:
        return "0.1.0"

    def dependencies(self) -> tuple[str, ...]:
        return ("transform",)

    def validate(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None

    def execute(self, context: PipelineContext, request: PipelineRequest) -> StageResult:
        return StageResult(
            stage_name=self.name(),
            stage_version=self.version(),
            status=StageStatus.COMPLETED,
            message="published",
        )

    def rollback(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None

    def cleanup(self, context: PipelineContext, request: PipelineRequest) -> None:
        return None
