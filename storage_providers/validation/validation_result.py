"""Storage provider validation result."""

from __future__ import annotations

from models.common import PlatformModel


class ProviderValidationResult(PlatformModel):
    """Result of a storage provider validation check."""

    valid: bool
    provider_id: str | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def success(
        cls,
        *,
        provider_id: str | None = None,
        warnings: tuple[str, ...] = (),
    ) -> ProviderValidationResult:
        return cls(valid=True, provider_id=provider_id, warnings=warnings)

    @classmethod
    def failure(cls, *errors: str, provider_id: str | None = None) -> ProviderValidationResult:
        return cls(valid=False, provider_id=provider_id, errors=errors)

    def with_warnings(self, *warnings: str) -> ProviderValidationResult:
        merged = tuple(dict.fromkeys((*self.warnings, *warnings)))
        return self.model_copy(update={"warnings": merged})
