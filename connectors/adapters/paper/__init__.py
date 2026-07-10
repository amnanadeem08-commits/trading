"""Paper execution adapter public API."""

from connectors.adapters.paper.paper_adapter import PAPER_ADAPTER_ID, PaperExecutionAdapter
from connectors.adapters.paper.paper_execution_record import PaperExecutionRecord
from connectors.adapters.paper.paper_order_state import TERMINAL_PAPER_STATES, PaperState
from connectors.adapters.paper.paper_result import PaperExecutionResult
from connectors.adapters.paper.paper_settings import PaperSettings

__all__ = [
    "PAPER_ADAPTER_ID",
    "TERMINAL_PAPER_STATES",
    "PaperExecutionAdapter",
    "PaperExecutionRecord",
    "PaperExecutionResult",
    "PaperSettings",
    "PaperState",
]
