"""Risk binding package exports."""

from __future__ import annotations

from signal_engine.exceptions import SignalRiskAttachmentError
from signal_engine.risk.attach import (
    attach_confidence,
    attach_invalidation,
    attach_risk_assessment,
    attach_risk_bindings,
    attach_risk_bindings_from_provider,
    ensure_risk_bindings_present,
)
from signal_engine.risk.risk_mapper import (
    assert_directional_confidence,
    build_invalidation_rule,
    build_risk_assessment,
    confidence_value_from_score,
    invalidation_from_atr,
    invalidation_from_structure,
)
from signal_engine.risk.risk_port import RiskBindingProvider
from signal_engine.risk.stub_provider import StubRiskBindingProvider

__all__ = [
    "RiskBindingProvider",
    "SignalRiskAttachmentError",
    "StubRiskBindingProvider",
    "assert_directional_confidence",
    "attach_confidence",
    "attach_invalidation",
    "attach_risk_assessment",
    "attach_risk_bindings",
    "attach_risk_bindings_from_provider",
    "build_invalidation_rule",
    "build_risk_assessment",
    "confidence_value_from_score",
    "ensure_risk_bindings_present",
    "invalidation_from_atr",
    "invalidation_from_structure",
]
