"""Execution validation framework."""

from __future__ import annotations

from execution.engine.execution_context import ExecutionContext
from execution.validation.execution_validation_result import ExecutionValidationResult
from execution.versioning.execution_version import ExecutionVersion
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState


class ExecutionValidator:
    """Validates approved risk outcomes and execution context."""

    def __init__(self, version: ExecutionVersion | None = None) -> None:
        self._version = version

    def validate(
        self,
        *,
        execution_id: str,
        risk_result: RiskResult | None,
        context: ExecutionContext | None = None,
        require_core_context: bool = True,
    ) -> ExecutionValidationResult:
        """Validate risk outcome, context, policy, and version compatibility."""
        checks: dict[str, bool] = {}
        errors: list[str] = []
        warnings: list[str] = []

        checks["risk_result_present"] = risk_result is not None
        if risk_result is None:
            errors.append("Risk result is required")

        approved = False
        if risk_result is not None:
            approved = risk_result.state == RiskState.APPROVED
            checks["risk_approved"] = approved
            if not approved:
                errors.append(f"Risk result must be approved, got '{risk_result.state}'")

        checks["context_present"] = context is not None
        if context is None:
            errors.append("Execution context is required")
        elif context.execution_id != execution_id:
            errors.append("Execution context id mismatch")
            checks["context_id_match"] = False
        else:
            checks["context_id_match"] = True

        if context is not None and require_core_context:
            has_core = context.core_context is not None
            checks["core_context_present"] = has_core
            if not has_core:
                errors.append("Core context is required")

        policy_compliant = approved and (context is not None)
        checks["policy_compliant"] = policy_compliant

        version_compatible = True
        if self._version is not None:
            version_compatible = self._version.is_compatible()
        checks["version_compatible"] = version_compatible
        if not version_compatible:
            errors.append("Execution version is not compatible with platform")

        valid = not errors
        return ExecutionValidationResult(
            valid=valid,
            execution_id=execution_id,
            checks=checks,
            errors=tuple(errors),
            warnings=tuple(warnings),
            version_compatible=version_compatible,
            policy_compliant=policy_compliant,
        )
