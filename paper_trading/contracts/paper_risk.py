"""Paper risk-gate contracts (pre-fill authorization)."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel
from models.risk import RiskVerdict
from risk.engine.risk_result import RiskResult


class PaperRiskGateResult(PlatformModel):
    """Outcome of the pre-fill risk gate.

    Disclaimer: an approved gate is **not** a profit guarantee and does not
    replace portfolio-level risk management.
    """

    passed: bool
    reasons: tuple[str, ...] = ()
    verdict: RiskVerdict | None = None
    risk_result: RiskResult | None = None
    message: str = Field(min_length=1)

    @property
    def blocks_fill(self) -> bool:
        """True when simulated fill must not proceed."""
        return not self.passed
