"""Fluent pipeline builder."""

from __future__ import annotations

from config.settings import PipelineSettings, get_settings
from pipeline.pipeline import Pipeline
from pipeline.stage import AfterStageHook, BeforeStageHook, PipelineStage, RetryPolicy, StageHook


class PipelineBuilder:
    """Fluent builder for pipeline definitions."""

    def __init__(
        self,
        name: str,
        *,
        version: str = "1.0.0",
        settings: PipelineSettings | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._settings = settings or get_settings().pipeline
        self._stages: dict[str, PipelineStage] = {}
        self._pre_hooks: list[StageHook] = []
        self._post_hooks: list[StageHook] = []
        self._before_stage_hooks: list[BeforeStageHook] = []
        self._after_stage_hooks: list[AfterStageHook] = []
        self._retry_policy: RetryPolicy | None = None

    def add_stage(self, stage: PipelineStage) -> PipelineBuilder:
        """Add a stage to the pipeline."""
        stage_name = stage.name()
        if stage_name in self._stages:
            msg = f"Duplicate stage: {stage_name}"
            raise ValueError(msg)
        self._stages[stage_name] = stage
        return self

    def remove_stage(self, stage_name: str) -> PipelineBuilder:
        """Remove a stage from the pipeline."""
        self._stages.pop(stage_name, None)
        return self

    def add_pre_hook(self, hook: StageHook) -> PipelineBuilder:
        self._pre_hooks.append(hook)
        return self

    def add_post_hook(self, hook: StageHook) -> PipelineBuilder:
        self._post_hooks.append(hook)
        return self

    def add_before_stage_hook(self, hook: BeforeStageHook) -> PipelineBuilder:
        self._before_stage_hooks.append(hook)
        return self

    def add_after_stage_hook(self, hook: AfterStageHook) -> PipelineBuilder:
        self._after_stage_hooks.append(hook)
        return self

    def with_retry_policy(self, policy: RetryPolicy) -> PipelineBuilder:
        """Attach a retry policy interface without implementing retry logic."""
        self._retry_policy = policy
        return self

    def build(self) -> Pipeline:
        """Build the pipeline definition."""
        return Pipeline(
            name=self._name,
            version=self._version,
            stages=dict(self._stages),
            settings=self._settings,
            pre_hooks=tuple(self._pre_hooks),
            post_hooks=tuple(self._post_hooks),
            before_stage_hooks=tuple(self._before_stage_hooks),
            after_stage_hooks=tuple(self._after_stage_hooks),
            retry_policy=self._retry_policy,
        )
