"""Pipeline and stage registry."""

from __future__ import annotations

from threading import RLock

from pipeline.exceptions import PipelineNotFoundError, PipelineRegistrationError, StageNotFoundError
from pipeline.pipeline import Pipeline
from pipeline.stage import PipelineStage
from pipeline.validation import PipelineValidationResult, validate_pipeline_stages

_default_registry: PipelineRegistry | None = None
_registry_lock = RLock()


class PipelineRegistry:
    """Thread-safe registry for pipeline definitions and stage types."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._pipelines: dict[str, Pipeline] = {}
        self._stages: dict[str, type[PipelineStage]] = {}

    def register_pipeline(self, pipeline: Pipeline) -> None:
        """Register a built pipeline definition."""
        name = pipeline.name
        if not name.strip():
            msg = "Pipeline name must not be empty"
            raise PipelineRegistrationError(msg)
        with self._lock:
            if name in self._pipelines:
                msg = f"Pipeline already registered: {name}"
                raise PipelineRegistrationError(msg)
            self._pipelines[name] = pipeline

    def unregister_pipeline(self, name: str) -> None:
        with self._lock:
            if name not in self._pipelines:
                raise PipelineNotFoundError(name)
            del self._pipelines[name]

    def register_stage(self, stage_type: type[PipelineStage]) -> None:
        """Register a stage type."""
        instance = stage_type()
        name = instance.name()
        with self._lock:
            self._stages[name] = stage_type

    def unregister_stage(self, name: str) -> None:
        with self._lock:
            if name not in self._stages:
                raise StageNotFoundError(name)
            del self._stages[name]

    def resolve(self, name: str) -> Pipeline:
        """Resolve a registered pipeline by name."""
        with self._lock:
            pipeline = self._pipelines.get(name)
        if pipeline is None:
            raise PipelineNotFoundError(name)
        return pipeline

    def exists(self, name: str) -> bool:
        with self._lock:
            return name in self._pipelines

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._pipelines.keys()))

    def list_stages(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._stages.keys()))

    def validate(self, pipeline: Pipeline) -> PipelineValidationResult:
        """Validate a pipeline's stage graph."""
        return validate_pipeline_stages(pipeline.stages)


def get_pipeline_registry() -> PipelineRegistry:
    """Return the process-wide default pipeline registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = PipelineRegistry()
        return _default_registry


def reset_pipeline_registry() -> None:
    """Reset the default pipeline registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
