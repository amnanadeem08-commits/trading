"""Validator interface."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from risk.engine.risk_context import RiskContext
from risk.validation.validation_result import ValidationResult, ValidationState
from risk.validation.validation_rule import ValidationRule


class Validator:
    """Executes a validation pipeline over registered rules."""

    def __init__(self, rules: tuple[ValidationRule, ...] | None = None) -> None:
        self._rules = rules or ()

    def register_rule(self, rule: ValidationRule) -> None:
        """Add a rule to the validation pipeline."""
        self._rules = (*self._rules, rule)

    def validate(
        self, context: RiskContext, *, input_data: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Execute all validation rules against the context."""
        validation_id = str(uuid4())
        data = input_data if input_data is not None else dict(context.input_data)
        if context.decision_result is not None:
            data = {**data, **context.decision_result.output}

        passed: list[str] = []
        failed: list[str] = []
        for rule in self._rules:
            if rule.validate(context, input_data=data):
                passed.append(rule.rule_id())
            else:
                failed.append(rule.rule_id())

        state = ValidationState.PASSED if not failed else ValidationState.FAILED
        return ValidationResult(
            validation_id=validation_id,
            state=state,
            passed_rules=tuple(passed),
            failed_rules=tuple(failed),
            metadata={"rule_count": str(len(self._rules))},
        )
