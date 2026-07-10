"""Adapter validation result."""

from __future__ import annotations

from models.common import PlatformModel


class FrameworkAdapterValidationResult(PlatformModel):
    """Validation result for framework adapter operations."""

    valid: bool
    errors: tuple[str, ...] = ()
    adapter_id: str | None = None

    @classmethod
    def success(cls, *, adapter_id: str | None = None) -> FrameworkAdapterValidationResult:
        return cls(valid=True, adapter_id=adapter_id)

    @classmethod
    def failure(
        cls,
        *errors: str,
        adapter_id: str | None = None,
    ) -> FrameworkAdapterValidationResult:
        return cls(valid=False, errors=errors, adapter_id=adapter_id)
