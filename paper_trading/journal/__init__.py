"""Paper trading journal: contracts-backed store and review service."""

from __future__ import annotations

from paper_trading.journal.metrics import compute_performance_metrics
from paper_trading.journal.service import (
    PaperJournalService,
    get_default_paper_journal_service,
    set_default_paper_journal_service,
)
from paper_trading.journal.store import (
    PaperJournalStore,
    get_paper_journal_store,
    reset_paper_journal_store,
)

__all__ = [
    "PaperJournalService",
    "PaperJournalStore",
    "compute_performance_metrics",
    "get_default_paper_journal_service",
    "get_paper_journal_store",
    "reset_paper_journal_store",
    "set_default_paper_journal_service",
]
