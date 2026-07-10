"""Pipeline definition and hook configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from config.settings import PipelineSettings
from pipeline.stage import AfterStageHook, BeforeStageHook, PipelineStage, RetryPolicy, StageHook


@dataclass
class Pipeline:
    """Immutable pipeline definition with stages and hooks."""

    name: str
    version: str
    stages: dict[str, PipelineStage]
    settings: PipelineSettings
    pre_hooks: tuple[StageHook, ...] = field(default_factory=tuple)
    post_hooks: tuple[StageHook, ...] = field(default_factory=tuple)
    before_stage_hooks: tuple[BeforeStageHook, ...] = field(default_factory=tuple)
    after_stage_hooks: tuple[AfterStageHook, ...] = field(default_factory=tuple)
    retry_policy: RetryPolicy | None = None
    _shutdown_requested: bool = field(default=False, repr=False)

    def request_shutdown(self) -> None:
        """Request graceful shutdown before the next stage."""
        self._shutdown_requested = True

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def stage_order(self) -> tuple[str, ...]:
        from pipeline.validation import validate_pipeline_stages

        validation = validate_pipeline_stages(self.stages)
        return validation.execution_order
