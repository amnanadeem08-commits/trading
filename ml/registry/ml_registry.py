"""ML platform registry."""

from __future__ import annotations

from enum import StrEnum
from threading import RLock

from ml.exceptions import MLRegistryError, ModelNotFoundError
from ml.models.model import MLModel
from ml.models.model_metadata import ModelMetadata
from ml.models.model_registry import ModelRegistry
from ml.training.training_job import TrainingJob, TrainingJobState

_default_ml_registry: MLRegistry | None = None
_ml_registry_lock = RLock()


class ModelLifecycleState(StrEnum):
    """Lifecycle states tracked by the ML registry."""

    REGISTERED = "registered"
    TRAINING = "training"
    READY = "ready"
    EVALUATING = "evaluating"
    ARCHIVED = "archived"


class MLRegistry:
    """Coordinates ML models, training jobs, and lifecycle state."""

    def __init__(self, *, model_registry: ModelRegistry | None = None) -> None:
        self._model_registry = model_registry or ModelRegistry()
        self._lock = RLock()
        self._states: dict[str, ModelLifecycleState] = {}
        self._jobs: dict[str, TrainingJob] = {}

    @property
    def models(self) -> ModelRegistry:
        return self._model_registry

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a model and initialize lifecycle state."""
        self._model_registry.register_metadata(metadata)
        with self._lock:
            self._states[metadata.model_id] = ModelLifecycleState.REGISTERED

    def register_model_type(self, model_type: type[MLModel]) -> None:
        """Register a model implementation type."""
        self._model_registry.register_type(model_type)
        instance = model_type()
        with self._lock:
            self._states[instance.model_id()] = ModelLifecycleState.REGISTERED

    def get_model(self, model_id: str) -> ModelMetadata:
        """Retrieve model metadata by identifier."""
        return self._model_registry.resolve_metadata(model_id)

    def get_state(self, model_id: str) -> ModelLifecycleState:
        with self._lock:
            state = self._states.get(model_id)
        if state is None:
            raise ModelNotFoundError(model_id)
        return state

    def set_state(self, model_id: str, state: ModelLifecycleState) -> None:
        if not self._model_registry.exists(model_id):
            raise ModelNotFoundError(model_id)
        with self._lock:
            self._states[model_id] = state

    def track_job(self, job: TrainingJob) -> None:
        if not self._model_registry.exists(job.model_id):
            raise ModelNotFoundError(job.model_id)
        with self._lock:
            self._jobs[job.job_id] = job
            if job.state == TrainingJobState.RUNNING:
                self._states[job.model_id] = ModelLifecycleState.TRAINING
            elif job.state == TrainingJobState.COMPLETED:
                self._states[job.model_id] = ModelLifecycleState.READY

    def get_job(self, job_id: str) -> TrainingJob:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            msg = f"Training job not found: {job_id}"
            raise MLRegistryError(msg)
        return job

    def list_models(self) -> tuple[str, ...]:
        return self._model_registry.list()

    def list_jobs(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._jobs.keys()))


def get_ml_registry() -> MLRegistry:
    """Return the process-wide default ML registry."""
    global _default_ml_registry
    with _ml_registry_lock:
        if _default_ml_registry is None:
            _default_ml_registry = MLRegistry()
        return _default_ml_registry


def reset_ml_registry() -> None:
    """Reset the default ML registry. Intended for tests."""
    global _default_ml_registry
    with _ml_registry_lock:
        _default_ml_registry = None
