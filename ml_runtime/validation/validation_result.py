"""Runtime validation result."""

from __future__ import annotations

from models.common import PlatformModel


class RuntimeValidationResult(PlatformModel):
    """Validation result for ML runtime operations."""

    valid: bool
    errors: tuple[str, ...] = ()
    request_id: str | None = None
    model_id: str | None = None
    executor_id: str | None = None

    @classmethod
    def success(
        cls,
        *,
        request_id: str | None = None,
        model_id: str | None = None,
        executor_id: str | None = None,
    ) -> RuntimeValidationResult:
        return cls(
            valid=True,
            request_id=request_id,
            model_id=model_id,
            executor_id=executor_id,
        )

    @classmethod
    def failure(cls, *errors: str, request_id: str | None = None) -> RuntimeValidationResult:
        return cls(valid=False, errors=errors, request_id=request_id)
