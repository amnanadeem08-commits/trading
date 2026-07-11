"""Build AdapterContext from a mapped PaperOrderRequest (no live brokers)."""

from __future__ import annotations

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.paper.paper_adapter import PAPER_ADAPTER_ID
from paper_trading.contracts.paper_order import PaperOrderRequest


def adapter_context_from_paper_order(
    order: PaperOrderRequest,
    *,
    adapter_id: str = PAPER_ADAPTER_ID,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    execution_id: str | None = None,
) -> AdapterContext:
    """Convert a paper order request into an adapter dispatch context.

    Does not attach ExecutionContext — fill/risk wiring lands in later tasks.
    """
    corr = correlation_id or f"corr-{order.session_id}"
    trace = trace_id or f"trace-{order.session_id}"
    exec_id = execution_id or f"paper-exec-{order.session_id}"
    payload = dict(order.adapter_payload)
    payload["session_id"] = order.session_id
    payload["invalidation_condition"] = order.invalidation_condition
    return AdapterContext(
        adapter_id=adapter_id,
        correlation_id=corr,
        trace_id=trace,
        execution_id=exec_id,
        request_id=order.request_id,
        execution_context=None,
        payload=payload,
        metadata=dict(order.metadata),
    )
