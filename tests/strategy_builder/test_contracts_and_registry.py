"""Contract, identity, serialization, and registry acceptance tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from strategy_builder import (
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    EntryRules,
    IndicatorOperand,
    IndicatorSpec,
    ProtectionKind,
    ProtectionRule,
    StrategyDraft,
    StrategyRegistrationError,
    StrategyRegistry,
    StrategyValidationError,
    deserialize_strategy,
    serialize_strategy,
    validate_strategy_identity,
)
from tests.strategy_builder.fixtures import crossing_strategy, example_strategies


def test_required_examples_are_valid_and_distinct() -> None:
    strategies = example_strategies()
    assert len(strategies) == 3
    assert len({strategy.strategy_id for strategy in strategies}) == 3
    for strategy in strategies:
        validate_strategy_identity(strategy)
        assert strategy.enabled


def test_unknown_indicator_kind_and_invalid_rule_shape_are_rejected() -> None:
    with pytest.raises(ValidationError):
        IndicatorSpec.model_validate_json(
            json.dumps({"indicator_id": "unknown", "kind": "ai_sentiment"})
        )
    with pytest.raises(ValidationError, match="between requires lower and upper"):
        ComparisonRule(
            rule_id="bad-range",
            operator=ComparisonOperator.BETWEEN,
            left=ConstantOperand(value=1.0),
        )


def test_undeclared_indicator_dependency_is_rejected() -> None:
    baseline = crossing_strategy()
    content = {name: getattr(baseline, name) for name in StrategyDraft.model_fields}
    content["entry_rules"] = EntryRules(
        buy=ComparisonRule(
            rule_id="unknown-dependency",
            operator=ComparisonOperator.GREATER_THAN,
            left=IndicatorOperand(indicator_id="not_declared"),
            right=ConstantOperand(value=1.0),
        )
    )
    with pytest.raises(ValidationError, match="undeclared indicator"):
        StrategyDraft.model_validate(content)


def test_atr_protection_requires_declared_atr_indicator() -> None:
    baseline = crossing_strategy()
    content = {name: getattr(baseline, name) for name in StrategyDraft.model_fields}
    content["stop_loss_rule"] = ProtectionRule(
        kind=ProtectionKind.ATR_MULTIPLE,
        value=2.0,
        indicator_id="close",
    )
    with pytest.raises(ValidationError, match="must reference an ATR"):
        StrategyDraft.model_validate(content)


def test_identity_and_serialization_are_deterministic() -> None:
    first = crossing_strategy()
    second = crossing_strategy()
    assert first.strategy_id == second.strategy_id
    assert first.version_hash == second.version_hash
    encoded = serialize_strategy(first)
    assert encoded == serialize_strategy(second)
    assert deserialize_strategy(encoded) == first


def test_enablement_does_not_change_definition_hash() -> None:
    enabled = crossing_strategy(enabled=True)
    disabled = crossing_strategy(enabled=False)
    assert enabled.version_hash == disabled.version_hash
    assert enabled.strategy_id == disabled.strategy_id
    validate_strategy_identity(disabled)


def test_tampered_identity_is_rejected() -> None:
    strategy = crossing_strategy()
    tampered = strategy.model_copy(update={"version_hash": "0" * 64})
    with pytest.raises(StrategyValidationError, match="version_hash"):
        serialize_strategy(tampered)


def test_registry_prevents_duplicates_and_controls_enablement() -> None:
    registry = StrategyRegistry()
    strategy = crossing_strategy()
    registry.register(strategy)
    with pytest.raises(StrategyRegistrationError, match="already registered"):
        registry.register(strategy)

    disabled = registry.disable(strategy.strategy_id, strategy.version)
    assert not disabled.enabled
    assert registry.list(enabled_only=True) == ()
    enabled = registry.enable(strategy.strategy_id, strategy.version)
    assert enabled.enabled
    assert registry.resolve(strategy.strategy_id, strategy.version) == enabled
