"""Inference validation result."""

from __future__ import annotations

from models.common import PlatformModel


class InferenceValidationResult(PlatformModel):
    """Outcome of inference pipeline validation."""

    valid: bool
    request_id: str | None = None
    model_id: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def success(
        cls,
        *,
        request_id: str | None = None,
        model_id: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> InferenceValidationResult:
        return cls(valid=True, request_id=request_id, model_id=model_id, warnings=warnings)

    @classmethod
    def failure(
        cls,
        *errors: str,
        request_id: str | None = None,
        model_id: str | None = None,
    ) -> InferenceValidationResult:
        return cls(valid=False, request_id=request_id, model_id=model_id, errors=errors)
