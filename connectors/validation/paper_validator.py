"""Paper adapter validation framework."""

from __future__ import annotations

from pydantic import Field

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.paper.paper_order_state import PaperState
from connectors.adapters.paper.paper_settings import PaperSettings
from models.common import PlatformModel


class PaperValidationResult(PlatformModel):
    """Outcome of paper adapter validation checks."""

    valid: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()


class PaperValidator:
    """Validates paper adapter readiness and dispatch eligibility."""

    def __init__(self, settings: PaperSettings | None = None) -> None:
        self._settings = settings or PaperSettings()

    @property
    def settings(self) -> PaperSettings:
        return self._settings

    def validate_request(self, context: AdapterContext | None) -> PaperValidationResult:
        """Validate dispatch request context."""
        checks: dict[str, bool] = {}
        errors: list[str] = []

        checks["context_present"] = context is not None
        if context is None:
            errors.append("Adapter context is required")
        elif not context.request_id.strip():
            errors.append("Request id is required")
            checks["request_id_present"] = False
        else:
            checks["request_id_present"] = True

        if context is not None and not context.execution_id.strip():
            errors.append("Execution id is required")
            checks["execution_id_present"] = False
        elif context is not None:
            checks["execution_id_present"] = True

        return PaperValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_adapter_state(self, state: PaperState | None) -> PaperValidationResult:
        """Validate adapter lifecycle state."""
        checks: dict[str, bool] = {}
        errors: list[str] = []

        checks["state_present"] = state is not None
        if state is None:
            errors.append("Adapter state is required")
        elif state in {PaperState.FAILED, PaperState.CANCELLED}:
            errors.append(f"Adapter state '{state.value}' is not dispatch eligible")
            checks["state_eligible"] = False
        else:
            checks["state_eligible"] = True

        return PaperValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_configuration(self) -> PaperValidationResult:
        """Validate simulation configuration."""
        checks: dict[str, bool] = {}
        errors: list[str] = []

        checks["enabled"] = self._settings.enabled
        if not self._settings.enabled:
            errors.append("Paper adapter is disabled")

        checks["latency_bounds"] = self._settings.latency_ms_max >= self._settings.latency_ms_min
        if not checks["latency_bounds"]:
            errors.append("Invalid latency configuration")

        checks["failure_rate_valid"] = 0.0 <= self._settings.failure_rate <= 1.0
        if not checks["failure_rate_valid"]:
            errors.append("Invalid failure rate configuration")

        return PaperValidationResult(valid=not errors, checks=checks, errors=tuple(errors))

    def validate_dispatch(
        self,
        context: AdapterContext | None,
        *,
        state: PaperState | None,
    ) -> PaperValidationResult:
        """Validate request, adapter state, and configuration."""
        request_result = self.validate_request(context)
        state_result = self.validate_adapter_state(state)
        config_result = self.validate_configuration()

        checks = {
            **request_result.checks,
            **state_result.checks,
            **config_result.checks,
        }
        errors = (
            list(request_result.errors) + list(state_result.errors) + list(config_result.errors)
        )
        return PaperValidationResult(valid=not errors, checks=checks, errors=tuple(errors))
