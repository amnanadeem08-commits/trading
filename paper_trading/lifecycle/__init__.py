"""Paper trading lifecycle: domain events + deterministic audit records."""

from __future__ import annotations

from paper_trading.lifecycle.paper_lifecycle import (
    PaperTradingLifecycleService,
    get_default_paper_lifecycle_service,
    set_default_paper_lifecycle_service,
)

__all__ = [
    "PaperTradingLifecycleService",
    "get_default_paper_lifecycle_service",
    "set_default_paper_lifecycle_service",
]
