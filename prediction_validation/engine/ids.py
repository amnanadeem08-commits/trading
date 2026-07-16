"""Deterministic identifier helpers."""

from __future__ import annotations

import hashlib


def deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def validation_id_for_outcome(
    *,
    prediction_id: str,
    status: str,
    actual_price: float | None,
    validated_at_iso: str,
) -> str:
    price_part = "none" if actual_price is None else f"{actual_price:.8f}"
    return deterministic_id(
        "pvout",
        prediction_id,
        status,
        price_part,
        validated_at_iso,
    )
