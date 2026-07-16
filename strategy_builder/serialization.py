"""Strict strategy JSON serialization."""

from __future__ import annotations

from pydantic import ValidationError

from strategy_builder.contracts import StrategyDefinition
from strategy_builder.exceptions import StrategyValidationError
from strategy_builder.identity import canonical_strategy_json, validate_strategy_identity


def serialize_strategy(strategy: StrategyDefinition) -> str:
    """Serialize a validated definition to canonical JSON."""
    return canonical_strategy_json(strategy)


def deserialize_strategy(payload: str) -> StrategyDefinition:
    """Deserialize, schema-validate, and verify deterministic identity."""
    try:
        strategy = StrategyDefinition.model_validate_json(payload)
    except ValidationError as error:
        raise StrategyValidationError(f"Invalid strategy JSON: {error}") from error
    validate_strategy_identity(strategy)
    return strategy
