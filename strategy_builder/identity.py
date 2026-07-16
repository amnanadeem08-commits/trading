"""Canonical deterministic strategy identity."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_builder.contracts import StrategyDefinition, StrategyDraft
from strategy_builder.exceptions import StrategyValidationError


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _content_payload(strategy: StrategyDraft | StrategyDefinition) -> dict[str, Any]:
    payload = strategy.model_dump(mode="json")
    payload.pop("strategy_id", None)
    payload.pop("version_hash", None)
    payload.pop("enabled", None)
    return payload


def resolve_strategy_id(*, name: str, market: str) -> str:
    """Derive stable strategy identity from normalized name and market."""
    identity = _canonical_json(
        {
            "market": market.strip().casefold(),
            "name": name.strip().casefold(),
        }
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"strategy-{digest[:16]}"


def resolve_version_hash(strategy: StrategyDraft | StrategyDefinition) -> str:
    """Hash immutable strategy content, excluding registry enablement state."""
    canonical = _canonical_json(_content_payload(strategy))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_strategy(draft: StrategyDraft) -> StrategyDefinition:
    """Attach deterministic identity to a validated draft."""
    return StrategyDefinition.model_validate(
        {
            **draft.model_dump(mode="python"),
            "strategy_id": resolve_strategy_id(name=draft.name, market=draft.market),
            "version_hash": resolve_version_hash(draft),
        }
    )


def validate_strategy_identity(strategy: StrategyDefinition) -> None:
    """Reject definitions whose declared deterministic identity was altered."""
    expected_id = resolve_strategy_id(name=strategy.name, market=strategy.market)
    if strategy.strategy_id != expected_id:
        raise StrategyValidationError(
            f"strategy_id mismatch: expected {expected_id}, got {strategy.strategy_id}"
        )
    expected_hash = resolve_version_hash(strategy)
    if strategy.version_hash != expected_hash:
        raise StrategyValidationError("version_hash does not match canonical strategy content")


def canonical_strategy_json(strategy: StrategyDefinition) -> str:
    """Return stable canonical JSON after identity validation."""
    validate_strategy_identity(strategy)
    return _canonical_json(strategy.model_dump(mode="json"))
