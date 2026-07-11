"""Paper trading orchestrator (skeleton — risk gate before fill; no fill yet)."""

from __future__ import annotations

from config.settings import AppSettings, get_settings
from models.risk import RiskVerdict
from models.signal import ExplainableSignal
from paper_trading.contracts.paper_order import PaperOrderRequest
from paper_trading.contracts.paper_request import (
    PaperOrchestrationRequest,
    PaperOrchestrationResult,
    PaperSessionStatus,
)
from paper_trading.contracts.paper_risk import PaperRiskGateResult
from paper_trading.exceptions import (
    PaperLiveTradingDisabledError,
    PaperOrchestrationError,
    PaperRiskRejectedError,
)
from paper_trading.mapping.signal_mapper import paper_order_from_signal
from paper_trading.registry.paper_record import PaperSessionRecord
from paper_trading.registry.paper_registry import (
    PaperSessionRegistry,
    get_paper_registry,
)
from paper_trading.risk.gate import evaluate_paper_risk_gate
from risk.engine.risk_result import RiskResult


class PaperTradingOrchestrator:
    """Coordinates signal → risk gate → paper path without live brokers.

    PAPER-002: prepare may optionally map to a PaperOrderRequest (no fill yet).
    PAPER-003: ``authorize_fill`` / ``prepare_with_risk_gate`` fail closed on reject.
    Optional ``paper_adapter`` may be injected for later wiring; not used for fills yet.
    """

    def __init__(
        self,
        *,
        registry: PaperSessionRegistry | None = None,
        settings: AppSettings | None = None,
        paper_adapter: object | None = None,
    ) -> None:
        self._registry = registry if registry is not None else get_paper_registry()
        self._settings = settings if settings is not None else get_settings()
        self._paper_adapter = paper_adapter

    @property
    def registry(self) -> PaperSessionRegistry:
        return self._registry

    @property
    def paper_adapter(self) -> object | None:
        """Injected paper adapter reference (unused until fill tasks)."""
        return self._paper_adapter

    def assert_paper_safe(self) -> None:
        """Refuse to run when live trading is enabled."""
        if self._settings.feature_flags.live_trading_enabled:
            raise PaperLiveTradingDisabledError()

    def map_signal(
        self,
        signal: ExplainableSignal,
        *,
        session_id: str,
        request_id: str | None = None,
        quantity: float | None = None,
        require_reference_price_for_directional: bool = True,
    ) -> PaperOrderRequest:
        """Map signal → paper order request (raises PaperMappingError on reject)."""
        self.assert_paper_safe()
        return paper_order_from_signal(
            signal,
            session_id=session_id,
            request_id=request_id,
            quantity=quantity,
            require_reference_price_for_directional=require_reference_price_for_directional,
        )

    def evaluate_risk_gate(
        self,
        signal: ExplainableSignal,
        *,
        verdict: RiskVerdict | None = None,
        risk_result: RiskResult | None = None,
    ) -> PaperRiskGateResult:
        """Evaluate the pre-fill risk gate (does not fill)."""
        self.assert_paper_safe()
        if self._settings.paper_trading.risk_gate_required_before_fill and (
            verdict is None and risk_result is None
        ):
            return evaluate_paper_risk_gate(signal, verdict=None, risk_result=None)
        return evaluate_paper_risk_gate(signal, verdict=verdict, risk_result=risk_result)

    def authorize_fill(
        self,
        signal: ExplainableSignal,
        *,
        verdict: RiskVerdict | None = None,
        risk_result: RiskResult | None = None,
    ) -> PaperRiskGateResult:
        """Authorize continuation toward a simulated fill; fail closed on reject.

        Does not execute a fill (PAPER-004). Raises ``PaperRiskRejectedError`` when
        the gate blocks fill, with rejection reasons recorded on the exception.
        """
        gate = self.evaluate_risk_gate(signal, verdict=verdict, risk_result=risk_result)
        if gate.blocks_fill:
            raise PaperRiskRejectedError(
                "Risk gate rejected; simulated fill is forbidden",
                reasons=gate.reasons,
            )
        return gate

    def prepare(self, request: PaperOrchestrationRequest) -> PaperOrchestrationResult:
        """Validate safety flags and register a prepared paper session."""
        self.assert_paper_safe()
        signal = request.signal
        if not request.session_id.strip():
            raise PaperOrchestrationError("session_id must not be empty")
        if signal.signal_id.strip() == "":
            raise PaperOrchestrationError("signal.signal_id must not be empty")
        result = PaperOrchestrationResult(
            session_id=request.session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            decision=signal.decision,
            status=PaperSessionStatus.PREPARED,
            message=(
                "Paper session prepared (no fill yet; simulated PnL is not a profit guarantee)"
            ),
        )
        self._registry.register(result)
        return result

    def prepare_with_risk_gate(
        self,
        signal: ExplainableSignal,
        *,
        session_id: str,
        notes: str = "",
        verdict: RiskVerdict | None = None,
        risk_result: RiskResult | None = None,
        map_order: bool = False,
        require_reference_price_for_directional: bool = True,
    ) -> PaperOrchestrationResult:
        """Prepare a session after evaluating the risk gate (no fill).

        Rejected gates register ``RISK_REJECTED`` with reasons and do not raise,
        so callers can audit the reject path. Use ``authorize_fill`` when a hard
        exception is required before fill.
        """
        if map_order:
            self.map_signal(
                signal,
                session_id=session_id,
                require_reference_price_for_directional=require_reference_price_for_directional,
            )
        gate = self.evaluate_risk_gate(signal, verdict=verdict, risk_result=risk_result)
        if gate.blocks_fill:
            result = PaperOrchestrationResult(
                session_id=session_id,
                signal_id=signal.signal_id,
                symbol_id=signal.symbol_id,
                market_id=signal.market_id,
                decision=signal.decision,
                status=PaperSessionStatus.RISK_REJECTED,
                message=gate.message,
                risk_gate_reasons=gate.reasons,
            )
            self._registry.register(result)
            return result

        self.assert_paper_safe()
        if not session_id.strip():
            raise PaperOrchestrationError("session_id must not be empty")
        approved = PaperOrchestrationResult(
            session_id=session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            decision=signal.decision,
            status=PaperSessionStatus.RISK_APPROVED,
            message=gate.message,
            risk_gate_reasons=(),
        )
        self._registry.register(approved)
        return approved

    def prepare_from_signal(
        self,
        signal: ExplainableSignal,
        *,
        session_id: str,
        notes: str = "",
        map_order: bool = False,
        require_reference_price_for_directional: bool = True,
    ) -> PaperOrchestrationResult:
        """Prepare a session; optionally validate signal→paper mapping first."""
        if map_order:
            self.map_signal(
                signal,
                session_id=session_id,
                require_reference_price_for_directional=require_reference_price_for_directional,
            )
        return self.prepare(
            PaperOrchestrationRequest(
                session_id=session_id,
                signal=signal,
                notes=notes,
            )
        )

    def get_session(self, session_id: str) -> PaperSessionRecord:
        """Return a registered paper session."""
        return self._registry.get(session_id)
