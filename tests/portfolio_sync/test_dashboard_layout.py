"""Dashboard layout guardrails for relocated controls."""

from __future__ import annotations

from pathlib import Path


def test_sidebar_controls_are_relocated_without_duplication() -> None:
    source = Path("dashboard.py").read_text(encoding="utf-8")
    assert "with st.sidebar" not in source
    assert "st.sidebar." not in source
    assert source.count('"Refresh Results"') == 1
    assert source.count('"Download Excel"') == 1
    assert "segmented_control" not in source
    assert 'selected = "all"' in source
    assert "render_portfolio_signals(" in source
    assert "render_portfolio_sync_diagnostics(" in source
    assert "Portfolio Sync Enabled" in source
    assert "Binance Connected" in source
    assert "API Authentication" in source
    assert "Holdings After Value Filter" in source
    assert "Holdings After Market Validation" in source
    assert "Successfully Valued" in source
    assert '"System and diagnostics"' in source
