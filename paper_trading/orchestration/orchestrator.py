"""Paper trading orchestrator — risk gate + deterministic simulated fill."""

from __future__ import annotations

from config.settings import AppSettings, get_settings
from models.common import UTCDateTime
from models.risk import RiskVerdict
from models.signal import ExplainableSignal
from paper_trading.contracts.fill import FillConfig
from paper_trading.contracts.paper_fill import PaperFillResult
from paper_trading.contracts.paper_order import PaperOrderRequest
from paper_trading.contracts.paper_request import (
    PaperOrchestrationRequest,
    PaperOrchestrationResult,
    PaperSessionStatus,
)
from paper_trading.contracts.paper_risk import PaperRiskGateResult
from paper_trading.exceptions import (
    PaperLiveTradingDisabledError,
    PaperMappingError,
    PaperOrchestrationError,
    PaperRiskRejectedError,
)
from paper_trading.fill.executor import SimulatedFillExecutor
from paper_trading.journal import get_default_paper_journal_service
from paper_trading.lifecycle import get_default_paper_lifecycle_service
from paper_trading.mapping.signal_mapper import paper_order_from_signal
from paper_trading.registry.paper_record import PaperSessionRecord
from paper_trading.registry.paper_registry import (
    PaperSessionRegistry,
    get_paper_registry,
)
from paper_trading.risk.gate import evaluate_paper_risk_gate
from risk.engine.risk_result import RiskResult


def _fill_config_from_settings(settings: AppSettings) -> FillConfig:
    pt = settings.paper_trading
    return FillConfig(
        slippage_bps=pt.fill_slippage_bps,
        commission_bps=pt.fill_commission_bps,
        spread_bps=pt.fill_spread_bps,
        fill_fraction=pt.fill_fraction,
        initial_cash=pt.initial_cash,
        default_quantity=pt.default_quantity,
    )


class PaperTradingOrchestrator:
    """Coordinates signal → risk gate → deterministic simulated fill.

    PAPER-003: ``authorize_fill`` / ``prepare_with_risk_gate`` fail closed on reject.
    PAPER-004: ``execute_simulated_fill`` runs fill only after risk authorization.
    """

    def __init__(
        self,
        *,
        registry: PaperSessionRegistry | None = None,
        settings: AppSettings | None = None,
        paper_adapter: object | None = None,
        fill_executor: SimulatedFillExecutor | None = None,
    ) -> None:
        self._registry = registry if registry is not None else get_paper_registry()
        self._settings = settings if settings is not None else get_settings()
        self._paper_adapter = paper_adapter
        self._fill_executor = fill_executor or SimulatedFillExecutor(
            config=_fill_config_from_settings(self._settings)
        )
        self._lifecycle = get_default_paper_lifecycle_service()
        self._journal = get_default_paper_journal_service()

    @property
    def registry(self) -> PaperSessionRegistry:
        return self._registry

    @property
    def paper_adapter(self) -> object | None:
        """Injected paper adapter reference (optional; fill uses SimulatedFillExecutor)."""
        return self._paper_adapter

    @property
    def fill_executor(self) -> SimulatedFillExecutor:
        return self._fill_executor

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
        """Authorize continuation toward a simulated fill; fail closed on reject."""
        gate = self.evaluate_risk_gate(signal, verdict=verdict, risk_result=risk_result)
        if gate.blocks_fill:
            raise PaperRiskRejectedError(
                "Risk gate rejected; simulated fill is forbidden",
                reasons=gate.reasons,
            )
        return gate

    def execute_simulated_fill(
        self,
        signal: ExplainableSignal,
        *,
        session_id: str,
        verdict: RiskVerdict | None = None,
        risk_result: RiskResult | None = None,
        quantity: float | None = None,
        fill_timestamp: UTCDateTime | None = None,
        fill_fraction: float | None = None,
        require_reference_price_for_directional: bool = True,
    ) -> PaperFillResult:
        """Signal → risk gate → deterministic fill → ledgers → portfolio."""
        occurred_at = fill_timestamp or signal.created_at
        gate: PaperRiskGateResult | None = None
        try:
            gate = self.authorize_fill(signal, verdict=verdict, risk_result=risk_result)
            order = self.map_signal(
                signal,
                session_id=session_id,
                quantity=quantity,
                require_reference_price_for_directional=require_reference_price_for_directional,
            )
            execution = self._fill_executor.execute(
                order,
                timestamp=fill_timestamp,
                fill_fraction=fill_fraction,
            )
            status = (
                PaperSessionStatus.PARTIALLY_FILLED
                if fill_fraction is not None and fill_fraction < 1.0
                else PaperSessionStatus.FILLED
            )
            result = PaperFillResult(
                session_id=session_id,
                signal_id=signal.signal_id,
                symbol_id=signal.symbol_id,
                market_id=signal.market_id,
                decision=signal.decision,
                status=status,
                message="Simulated fill recorded (not financial advice; no live broker)",
                fill=execution.fill,
                position_entry=execution.position_entry,
                pnl_entry=execution.pnl_entry,
                portfolio=execution.portfolio,
            )
            orch = PaperOrchestrationResult(
                session_id=session_id,
                signal_id=signal.signal_id,
                symbol_id=signal.symbol_id,
                market_id=signal.market_id,
                decision=signal.decision,
                status=status,
                message=result.message,
            )
            self._registry.register(orch)
            self._lifecycle.emit_fill_accepted(signal=signal, result=result)
            self._journal.record_fill_accepted(signal=signal, result=result, gate=gate)
            return result
        except PaperRiskRejectedError as exc:
            gate = self.evaluate_risk_gate(signal, verdict=verdict, risk_result=risk_result)
            self._lifecycle.emit_fill_rejected(
                signal=signal,
                session_id=session_id,
                reason=str(exc),
                risk_reasons=exc.reasons,
                occurred_at=occurred_at,
            )
            self._journal.record_fill_rejected(
                signal=signal,
                session_id=session_id,
                reason=str(exc),
                risk_reasons=exc.reasons,
                gate=gate,
                occurred_at=occurred_at,
            )
            raise
        except (PaperMappingError, PaperOrchestrationError) as exc:
            self._lifecycle.emit_fill_rejected(
                signal=signal,
                session_id=session_id,
                reason=str(exc),
                risk_reasons=(),
                occurred_at=occurred_at,
            )
            self._journal.record_fill_rejected(
                signal=signal,
                session_id=session_id,
                reason=str(exc),
                risk_reasons=(),
                gate=gate,
                occurred_at=occurred_at,
            )
            raise

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
            message=("Paper session prepared (simulated PnL is not a profit guarantee)"),
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
        """Prepare a session after evaluating the risk gate (no fill)."""
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
            self._journal.record_risk_rejected(
                signal=signal,
                session_id=session_id,
                gate=gate,
                occurred_at=signal.created_at,
            )
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

    def cancel_session_from_signal(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        reason: str = "cancelled",
        cancelled_at: UTCDateTime | None = None,
    ) -> PaperOrchestrationResult:
        """Cancel a prepared/risk-approved paper session (PAPER-005)."""
        self.assert_paper_safe()
        record = self._registry.get(session_id)
        if record.status in {PaperSessionStatus.FILLED, PaperSessionStatus.PARTIALLY_FILLED}:
            raise PaperOrchestrationError("Cannot cancel an already-filled paper session")
        updated = self._registry.update_status(
            session_id,
            status=PaperSessionStatus.CANCELLED,
            message=reason,
            risk_gate_reasons=(),
        )
        self._lifecycle.emit_cancellation(
            signal=signal,
            session_id=session_id,
            reason=reason,
            occurred_at=cancelled_at or signal.created_at,
        )
        self._journal.record_cancellation(
            signal=signal,
            session_id=session_id,
            reason=reason,
            occurred_at=cancelled_at or signal.created_at,
        )
        return updated.result
