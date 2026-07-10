"""Training validation result."""

from __future__ import annotations

from models.common import PlatformModel


class TrainingValidationResult(PlatformModel):
    """Outcome of training pipeline validation."""

    valid: bool
    job_id: str | None = None
    experiment_id: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def success(
        cls,
        *,
        job_id: str | None = None,
        experiment_id: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> TrainingValidationResult:
        return cls(valid=True, job_id=job_id, experiment_id=experiment_id, warnings=warnings)

    @classmethod
    def failure(cls, *errors: str, job_id: str | None = None) -> TrainingValidationResult:
        return cls(valid=False, job_id=job_id, errors=errors)
