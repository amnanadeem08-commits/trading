"""Registry validation result."""

from __future__ import annotations

from models.common import PlatformModel


class RegistryValidationResult(PlatformModel):
    """Outcome of model registry validation."""

    valid: bool
    model_id: str | None = None
    version_id: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def success(
        cls,
        *,
        model_id: str | None = None,
        version_id: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> RegistryValidationResult:
        return cls(valid=True, model_id=model_id, version_id=version_id, warnings=warnings)

    @classmethod
    def failure(cls, *errors: str, model_id: str | None = None) -> RegistryValidationResult:
        return cls(valid=False, model_id=model_id, errors=errors)
