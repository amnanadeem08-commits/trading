"""Paper Trading public API — simulated path only; no live brokers."""

from __future__ import annotations

from paper_trading.contracts import (
    PaperOrchestrationRequest,
    PaperOrchestrationResult,
    PaperOrderMappingResult,
    PaperOrderRequest,
    PaperOrderSide,
    PaperRiskGateResult,
    PaperSessionStatus,
)
from paper_trading.exceptions import (
    PaperLiveTradingDisabledError,
    PaperMappingError,
    PaperOrchestrationError,
    PaperRegistrationError,
    PaperRiskRejectedError,
    PaperSessionNotFoundError,
    PaperTradingError,
)
from paper_trading.mapping import (
    adapter_context_from_paper_order,
    map_signal_to_paper_order,
    paper_order_from_signal,
    reference_price_from_signal,
)
from paper_trading.orchestration import PaperTradingOrchestrator
from paper_trading.registry import (
    PaperSessionRecord,
    PaperSessionRegistry,
    get_paper_registry,
    reset_paper_registry,
)
from paper_trading.risk import (
    approval_blocks_fill,
    build_paper_risk_verdict,
    evaluate_paper_risk_gate,
    trading_decision_from_signal,
)

__all__ = [
    "PaperLiveTradingDisabledError",
    "PaperMappingError",
    "PaperOrchestrationError",
    "PaperOrchestrationRequest",
    "PaperOrchestrationResult",
    "PaperOrderMappingResult",
    "PaperOrderRequest",
    "PaperOrderSide",
    "PaperRegistrationError",
    "PaperRiskGateResult",
    "PaperRiskRejectedError",
    "PaperSessionNotFoundError",
    "PaperSessionRecord",
    "PaperSessionRegistry",
    "PaperSessionStatus",
    "PaperTradingError",
    "PaperTradingOrchestrator",
    "adapter_context_from_paper_order",
    "approval_blocks_fill",
    "build_paper_risk_verdict",
    "evaluate_paper_risk_gate",
    "get_paper_registry",
    "map_signal_to_paper_order",
    "paper_order_from_signal",
    "reference_price_from_signal",
    "reset_paper_registry",
    "trading_decision_from_signal",
]
