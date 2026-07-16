"""
Interactive web dashboard for Crypto + PSX + PMEX signal results.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from connectors.binance_spot_portfolio import (
    BinanceSpotPortfolioGateway,
    PortfolioAuthenticationError,
)
from core.llm_analyzer import (
    AIAuthenticationError,
    AIConfigurationError,
    AIExecutionError,
    assert_ai_ready,
    startup_diagnostics,
)
from core.signal_universe import (
    configured_crypto_symbols,
    configured_pmex_instruments,
    configured_psx_symbols,
    configured_universe_counts,
)
from core.signal_workbook import (
    PRODUCTION_DIR,
    PRODUCTION_GENERATOR,
    ensure_artifact_dirs,
    has_blocked_name_prefix,
    is_production_workbook,
    list_production_workbooks,
    read_workbook_metadata,
)
from main import MARKET_SHEETS, markets_to_run, save_results, scan_market
from portfolio_sync import (
    PortfolioAuthenticationStatus,
    PortfolioHolding,
    PortfolioSignalRow,
    PortfolioSyncDiagnostics,
    PortfolioSyncResult,
    PortfolioSyncService,
    PortfolioWarning,
    PortfolioWarningCode,
    portfolio_rows_for_display,
    portfolio_stage_message,
    project_portfolio_signals,
    stable_unique_symbols,
    unavailable_result,
)

SIGNAL_COLORS = {
    "BUY": "#1f9d66",
    "SELL": "#d64545",
    "HOLD": "#d89b1d",
    "n/a": "#6b7280",
}


st.set_page_config(
    page_title="Trading Signal Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    .stApp {
        background: #f6f7fb;
        color: #172033;
    }
    [data-testid="stHeader"] {
        background: rgba(246, 247, 251, 0.88);
    }
    .main-title {
        padding: 22px 0 4px 0;
    }
    .main-title h1 {
        margin: 0;
        font-size: 34px;
        line-height: 1.1;
        letter-spacing: 0;
        color: #111827;
    }
    .main-title p {
        margin: 8px 0 0 0;
        color: #526070;
        font-size: 15px;
    }
    .metric-row {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin: 18px 0 14px 0;
    }
    .signal-card {
        background: #ffffff;
        border: 1px solid #dfe5ee;
        border-left: 5px solid var(--accent);
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 92px;
        box-shadow: 0 8px 22px rgba(21, 31, 48, 0.06);
    }
    .signal-card .label {
        color: #667085;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 8px;
    }
    .signal-card .value {
        color: #111827;
        font-size: 26px;
        font-weight: 700;
        line-height: 1.1;
    }
    .signal-card .sub {
        color: #667085;
        font-size: 13px;
        margin-top: 5px;
    }
    .asset-card {
        background: #ffffff;
        border: 1px solid #dfe5ee;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 6px 16px rgba(21, 31, 48, 0.05);
    }
    .asset-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 8px;
    }
    .asset-symbol {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 72px;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 12px;
        color: white;
        background: var(--accent);
        font-weight: 700;
    }
    .reasoning {
        color: #344054;
        font-size: 13px;
        line-height: 1.45;
    }
    .muted {
        color: #667085;
        font-size: 13px;
    }
    @media (max-width: 900px) {
        .metric-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 560px) {
        .metric-row { grid-template-columns: 1fr; }
        .main-title h1 { font-size: 26px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Production workbooks ONLY under outputs/production/. Never root, archive, or proof.
_WORKBOOK_DIR = PRODUCTION_DIR

_AUTH_HOLD_FALLBACK_MARKERS = (
    "Analysis failed, defaulting to HOLD for safety",
    "Could not resolve authentication method",
)
_PROOF_REASONING_PREFIX = "Proof scan for"


def frame_has_proof_reasoning(df: pd.DataFrame) -> bool:
    if df is None or df.empty or "reasoning" not in df.columns:
        return False
    return bool(df["reasoning"].astype(str).str.startswith(_PROOF_REASONING_PREFIX).any())


def results_have_proof_reasoning(results: dict) -> bool:
    return any(frame_has_proof_reasoning(df) for df in results.values())


def workbook_has_proof_reasoning(path: Path) -> bool:
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception:
        return False
    return any(frame_has_proof_reasoning(df) for name, df in sheets.items() if name != "_Meta")


def frame_has_auth_hold_fallback(df: pd.DataFrame) -> bool:
    if df is None or df.empty or "reasoning" not in df.columns:
        return False
    reasoning = df["reasoning"].astype(str)
    return bool(
        reasoning.str.contains("|".join(_AUTH_HOLD_FALLBACK_MARKERS), regex=True, na=False).any()
    )


def results_have_auth_hold_fallback(results: dict) -> bool:
    return any(frame_has_auth_hold_fallback(df) for df in results.values())


def workbook_has_auth_hold_fallback(path: Path) -> bool:
    """True when workbook rows were produced by the removed auth→HOLD catch path."""
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception:
        return False
    return any(frame_has_auth_hold_fallback(df) for name, df in sheets.items() if name != "_Meta")


def workbook_matches_configured_universe(path: Path) -> bool:
    """False when a sheet has fewer rows than the current configured universe.

    Stale workbooks from older 5-symbol configs must not be treated as current.
    """
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception:
        return False

    expected = {
        "Crypto": len(configured_crypto_symbols()),
        "PSX": len(configured_psx_symbols()),
        "PMEX": len(configured_pmex_instruments()),
    }
    for sheet_name, configured_count in expected.items():
        if sheet_name not in sheets:
            continue
        df = sheets[sheet_name]
        if df is None or df.empty:
            return False
        # Ignore placeholder n/a rows from empty scans
        if "symbol" in df.columns:
            symbols = df["symbol"].astype(str)
            real = symbols[~symbols.str.lower().isin({"n/a", "nan", ""})]
            # Reject stale TOP_N=5 workbooks; allow minor live fetch skips.
            if len(real) < configured_count and len(real) <= 5:
                return False
        elif len(df) < configured_count and len(df) <= 5:
            return False
    return True


def _is_loadable_workbook(path: Path) -> bool:
    """Only production_scan workbooks under outputs/production/ are eligible."""
    if has_blocked_name_prefix(path):
        return False
    if not is_production_workbook(path):
        return False
    if workbook_has_auth_hold_fallback(path):
        return False
    if workbook_has_proof_reasoning(path):
        return False
    return workbook_matches_configured_universe(path)


def list_root_signal_workbooks() -> list[Path]:
    """Eligible production workbooks under outputs/production/ only."""
    ensure_artifact_dirs()
    return sorted(
        (p for p in list_production_workbooks() if _is_loadable_workbook(p)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def latest_workbook() -> Path | None:
    """Newest production workbook under outputs/production/ (never proof/root/archive)."""
    files = list_root_signal_workbooks()
    return files[0] if files else None


def load_workbook(path: Path) -> dict[str, pd.DataFrame]:
    data = pd.read_excel(path, sheet_name=None)
    normalized = {}
    for market, sheet in MARKET_SHEETS.items():
        if sheet in data:
            normalized[market] = data[sheet]
    return normalized


def run_refresh(
    selected_market: str,
    *,
    crypto_symbols: tuple[str, ...] | None = None,
) -> tuple[dict[str, pd.DataFrame], str]:
    assert_ai_ready(verify_remote=True)
    results = {}
    for market in markets_to_run(selected_market):
        with st.status(f"Refreshing {MARKET_SHEETS[market]} data...", expanded=False):
            results[market] = scan_market(
                market,
                symbols=crypto_symbols if market == "crypto" else None,
            )
    out_path = save_results(
        results,
        selected_market,
        generator=PRODUCTION_GENERATOR,
        source="dashboard.py",
    )
    return results, out_path


def should_run_portfolio_sync(
    *,
    refresh_clicked: bool,
    force: bool = False,
    cached_result: PortfolioSyncResult | None,
    cached_at: datetime | None,
    cache_ttl_seconds: float,
    portfolio_sync_enabled: bool,
) -> bool:
    """Return whether a new Binance sync should run on this Streamlit rerun."""
    if not portfolio_sync_enabled:
        return False
    if refresh_clicked or force:
        return True
    if cached_result is None or not cached_result.sync_succeeded:
        return True
    if cached_at is None:
        return True
    return datetime.now() - cached_at > timedelta(seconds=cache_ttl_seconds)


def resolve_portfolio_sync_result(
    new_result: PortfolioSyncResult,
    cached_result: PortfolioSyncResult | None,
) -> tuple[PortfolioSyncResult, bool]:
    """Keep the last successful sync when a later attempt fails."""
    if new_result.sync_succeeded:
        return new_result, False
    if cached_result is not None and cached_result.sync_succeeded:
        merged_warnings = (*new_result.warnings, *cached_result.warnings)
        return (
            cached_result.model_copy(update={"warnings": merged_warnings}),
            True,
        )
    return new_result, False


def sync_binance_portfolio() -> PortfolioSyncResult:
    """Return a non-fatal read-only portfolio snapshot for dashboard refresh."""
    settings = get_settings().portfolio_sync
    if not settings.enabled:
        return PortfolioSyncResult(
            diagnostics=PortfolioSyncDiagnostics(portfolio_sync_enabled=False)
        )
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    if not api_key.strip() or not api_secret.strip():
        return unavailable_result(
            PortfolioWarningCode.MISSING_CREDENTIALS,
            "Binance credentials were not loaded.",
            diagnostics=PortfolioSyncDiagnostics(
                portfolio_sync_enabled=True,
                credentials_loaded=False,
                authentication_status=PortfolioAuthenticationStatus.FAILED,
            ),
        )
    try:
        gateway = BinanceSpotPortfolioGateway.from_credentials(
            api_key=api_key,
            api_secret=api_secret,
            timeout_milliseconds=settings.timeout_milliseconds,
            max_retries=settings.max_retries,
        )
    except PortfolioAuthenticationError as error:
        return unavailable_result(
            PortfolioWarningCode.AUTHENTICATION_FAILED,
            f"Binance authentication failed: {error}",
            diagnostics=PortfolioSyncDiagnostics(
                portfolio_sync_enabled=True,
                credentials_loaded=True,
                authentication_status=PortfolioAuthenticationStatus.FAILED,
            ),
        )
    return PortfolioSyncService(gateway, settings).sync()


def sync_binance_portfolio_with_timeout(timeout_seconds: float) -> PortfolioSyncResult:
    """Run portfolio sync in a worker thread so scanner rendering is not blocked."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(sync_binance_portfolio)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        return unavailable_result(
            PortfolioWarningCode.API_TIMEOUT,
            "Portfolio sync timed out; showing last cached result.",
            diagnostics=PortfolioSyncDiagnostics(
                portfolio_sync_enabled=True,
                credentials_loaded=bool(
                    os.getenv("BINANCE_API_KEY", "").strip()
                    and os.getenv("BINANCE_API_SECRET", "").strip()
                ),
                fetch_balance_executed=True,
                authentication_status=PortfolioAuthenticationStatus.NOT_VERIFIED,
            ),
        )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def configured_portfolio_diagnostics() -> PortfolioSyncDiagnostics:
    """Return non-sensitive pre-refresh configuration diagnostics."""
    settings = get_settings().portfolio_sync
    credentials_loaded = bool(
        os.getenv("BINANCE_API_KEY", "").strip() and os.getenv("BINANCE_API_SECRET", "").strip()
    )
    return PortfolioSyncDiagnostics(
        portfolio_sync_enabled=settings.enabled,
        credentials_loaded=credentials_loaded,
    )


def render_portfolio_sync_diagnostics(
    diagnostics: PortfolioSyncDiagnostics,
    warnings: tuple[PortfolioWarning, ...],
) -> None:
    """Render non-sensitive connection state and portfolio pipeline stage counts."""
    st.markdown("#### Portfolio Sync Diagnostics")
    authentication = {
        PortfolioAuthenticationStatus.SUCCESS: "Success",
        PortfolioAuthenticationStatus.FAILED: "Failed",
        PortfolioAuthenticationStatus.NOT_VERIFIED: "Not verified",
        PortfolioAuthenticationStatus.NOT_ATTEMPTED: "Not attempted",
    }[diagnostics.authentication_status]
    left, right = st.columns(2)
    with left:
        st.write(
            "**Portfolio Sync Enabled:** "
            f"{'Yes' if diagnostics.portfolio_sync_enabled else 'No'}"
        )
        st.write(f"**Binance Connected:** {'Yes' if diagnostics.binance_connected else 'No'}")
        st.write(f"**API Authentication:** {authentication}")
        st.write(f"**Credentials Loaded:** {'Yes' if diagnostics.credentials_loaded else 'No'}")
        st.write(
            "**fetch_balance() Executed:** "
            f"{'Yes' if diagnostics.fetch_balance_executed else 'No'}"
        )
        st.write(
            "**fetch_balance() Success:** "
            f"{'Yes' if diagnostics.fetch_balance_success else 'No'}"
        )
    with right:
        st.write(f"**Holdings Returned:** {diagnostics.non_zero_balance_count}")
        st.write(
            "**Holdings After Market Validation:** "
            f"{diagnostics.valid_market_count}"
        )
        st.write(
            "**Holdings After Value Filter:** "
            f"{diagnostics.above_threshold_count}"
        )
        st.write(f"**Final Portfolio Holdings:** {diagnostics.final_holding_count}")
        if diagnostics.asset_symbols_returned:
            st.write(
                "**Asset Symbols Returned:** "
                f"{', '.join(diagnostics.asset_symbols_returned)}"
            )
        st.write(f"**Mapped Assets:** {diagnostics.mapped_asset_count}")
        st.write(f"**Successfully Valued:** {diagnostics.successfully_valued_count}")
    st.write("**Structured Warnings:**")
    if warnings:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "code": warning.code.value,
                        "asset": warning.asset or "N/A",
                        "message": warning.message,
                    }
                    for warning in warnings
                ]
            ),
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("None")


def render_portfolio_holdings(
    holdings: tuple[PortfolioHolding, ...],
    warnings: tuple[PortfolioWarning, ...],
) -> None:
    """Render compact portfolio holdings summary."""
    if not holdings:
        return
    
    st.markdown("### Portfolio Holdings")
    st.caption(
        "Your Binance balances. Values are estimated using underlying asset prices."
    )
    
    # Check if we have any LD* assets
    has_locked = any(h.holding_type == "Binance Earn" for h in holdings)
    if has_locked:
        st.info(
            "Your Binance balance includes Earn/locked positions (LD* assets). "
            "These are shown using their underlying market pairs for read-only analysis."
        )
    
    # Build compact display rows
    rows = []
    for holding in holdings:
        rows.append({
            "Asset": holding.asset,
            "Holding Type": holding.holding_type,
            "Quantity": f"{holding.quantity:.8f}",
            "Estimated Value (USDT)": f"${holding.current_value_usdt:.2f}",
            "Analysis Pair": holding.scan_symbol if not holding.is_stable_balance else "N/A",
        })
    
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def render_portfolio_signals(
    rows: tuple[PortfolioSignalRow, ...],
    warnings: tuple[PortfolioWarning, ...],
    diagnostics: PortfolioSyncDiagnostics,
    holdings: tuple[PortfolioHolding, ...] = (),
    *,
    status_message: str | None = None,
    from_cache: bool = False,
) -> None:
    """Render portfolio analysis as visual cards matching Signal Details style."""
    st.markdown("### Portfolio Signals")
    st.caption(
        "Read-only market analysis for your holdings. "
        "Suggested actions are advisory; no trades are placed."
    )
    
    # Show warnings that aren't about LD* missing pairs (those are expected)
    relevant_warnings = [
        w for w in warnings
        if not (w.code == PortfolioWarningCode.MISSING_PAIR and w.asset and w.asset.startswith("LD"))
    ]
    for warning in relevant_warnings:
        st.warning(warning.message)
    
    if not rows:
        # Check if we have holdings but no signals (e.g., only stable balances)
        if holdings:
            stable_count = sum(1 for h in holdings if h.is_stable_balance)
            if stable_count == len(holdings):
                st.info(
                    "All portfolio holdings are stablecoins (USDT). "
                    "No market analysis signals are generated for stable balances."
                )
                return
        
        reason = status_message or portfolio_stage_message(
            PortfolioSyncResult(diagnostics=diagnostics, warnings=warnings),
            from_cache=from_cache,
        )
        st.info(f"No portfolio signals available. Reason: {reason}")
        return
    
    # Render portfolio signals as cards
    for row in rows:
        signal = row.signal
        color = SIGNAL_COLORS.get(signal, "#6b7280")
        
        # Format optional fields
        entry = f"${row.entry_zone:.2f}" if isinstance(row.entry_zone, (int, float)) else "N/A"
        stop = f"${row.stop_loss:.2f}" if isinstance(row.stop_loss, (int, float)) else "N/A"
        tp = f"${row.take_profit:.2f}" if isinstance(row.take_profit, (int, float)) else "N/A"
        
        st.markdown(
            f"""
            <div class="asset-card">
                <div class="asset-top">
                    <div>
                        <div class="asset-symbol">{row.asset}</div>
                        <div class="muted">
                            Analysis: {row.analysis_symbol} · 
                            Value: ${row.current_value_usdt:.2f} · 
                            Confidence: {row.confidence}
                        </div>
                    </div>
                    <span class="badge" style="--accent:{color}">{signal}</span>
                </div>
                <div class="reasoning">{row.reasoning}</div>
                <div class="muted" style="margin-top:8px">
                    Suggested: {row.suggested_action}
                </div>
                <div class="muted" style="margin-top:4px">
                    Entry: {entry} · Stop: {stop} · Target: {tp}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def signal_counts(df: pd.DataFrame) -> pd.Series:
    if df.empty or "signal" not in df.columns:
        return pd.Series(dtype="int64")
    return df["signal"].fillna("n/a").value_counts()


def render_metric_cards(df: pd.DataFrame, *, market: str | None = None):
    counts = signal_counts(df)
    scanned = int(counts.sum()) if not counts.empty else 0
    buy = int(counts.get("BUY", 0))
    sell = int(counts.get("SELL", 0))
    hold = int(counts.get("HOLD", 0))
    high_conf = (
        int((df.get("confidence", pd.Series(dtype=str)).fillna("").str.lower() == "high").sum())
        if not df.empty
        else 0
    )

    if market == "crypto":
        monitored = len(configured_crypto_symbols())
    elif market == "psx":
        monitored = len(configured_psx_symbols())
    elif market == "pmex":
        monitored = len(configured_pmex_instruments())
    else:
        monitored = scanned

    cards = [
        (
            "Assets",
            monitored,
            f"{scanned} scanned of {monitored} configured in signal_universe.yaml",
        ),
        ("BUY", buy, "opportunity signals"),
        ("SELL", sell, "risk-off signals"),
        ("HOLD", hold, f"{high_conf} high confidence"),
    ]
    columns = st.columns(4)
    for column, (label, value, help_text) in zip(columns, cards, strict=True):
        with column:
            st.metric(label=label, value=value, help=help_text)


def render_charts(df: pd.DataFrame, sheet_name: str):
    left, right = st.columns([1, 1])
    counts = signal_counts(df).rename_axis("signal").reset_index(name="count")
    if counts.empty:
        st.info(f"No {sheet_name} rows to chart yet.")
        return

    color_map = {
        row["signal"]: SIGNAL_COLORS.get(row["signal"], "#6b7280") for _, row in counts.iterrows()
    }
    with left:
        fig = px.pie(
            counts,
            names="signal",
            values="count",
            hole=0.58,
            color="signal",
            color_discrete_map=color_map,
        )
        fig.update_layout(
            title=f"{sheet_name} Signal Mix",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(l=10, r=10, t=54, b=10),
            legend_title_text="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        conf = (
            df.get("confidence", pd.Series(dtype=str))
            .fillna("n/a")
            .value_counts()
            .rename_axis("confidence")
            .reset_index(name="count")
        )
        fig = px.bar(
            conf,
            x="confidence",
            y="count",
            color="confidence",
            color_discrete_sequence=["#3858e9", "#1f9d66", "#d89b1d", "#d64545"],
        )
        fig.update_layout(
            title=f"{sheet_name} Confidence",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(l=10, r=10, t=54, b=10),
            showlegend=False,
            xaxis_title="",
            yaxis_title="Assets",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_asset_cards(df: pd.DataFrame):
    if df.empty:
        st.info("No assets available for this sheet yet.")
        return

    sort_order = {"BUY": 0, "SELL": 1, "HOLD": 2}
    display_df = df.copy()
    display_df["_order"] = display_df["signal"].map(sort_order).fillna(3)
    display_df = display_df.sort_values(["_order", "symbol"]).drop(columns=["_order"])

    for _, row in display_df.iterrows():
        signal = str(row.get("signal", "n/a"))
        color = SIGNAL_COLORS.get(signal, "#6b7280")
        reasoning = str(row.get("reasoning", "No reasoning available."))
        confidence = str(row.get("confidence", "n/a"))
        invalidation = str(row.get("invalidation", "n/a"))
        st.markdown(
            f"""
            <div class="asset-card">
                <div class="asset-top">
                    <div>
                        <div class="asset-symbol">{row.get('symbol', 'n/a')}</div>
                        <div class="muted">Confidence: {confidence}</div>
                    </div>
                    <span class="badge" style="--accent:{color}">{signal}</span>
                </div>
                <div class="reasoning">{reasoning}</div>
                <div class="muted" style="margin-top:8px">Invalidation: {invalidation}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_market(sheet_name: str, df: pd.DataFrame, *, market: str):
    render_metric_cards(df, market=market)
    render_charts(df, sheet_name)
    st.markdown("#### Signal Details")
    render_asset_cards(df)
    with st.expander("Full table"):
        st.dataframe(df, use_container_width=True, hide_index=True)


cleared_invalid_results = False
if "results" in st.session_state and (
    results_have_auth_hold_fallback(st.session_state.results)
    or results_have_proof_reasoning(st.session_state.results)
):
    st.session_state.results = {}
    st.session_state.workbook_path = None
    st.session_state.last_updated = None
    cleared_invalid_results = True

if "results" not in st.session_state:
    latest = latest_workbook()
    if latest:
        meta = read_workbook_metadata(latest)
        if meta.get("generator") != PRODUCTION_GENERATOR:
            st.session_state.results = {}
            st.session_state.workbook_path = None
            st.session_state.last_updated = None
        else:
            st.session_state.results = load_workbook(latest)
            st.session_state.workbook_path = str(latest)
            st.session_state.last_updated = datetime.fromtimestamp(latest.stat().st_mtime)
    else:
        st.session_state.results = {}
        st.session_state.workbook_path = None
        st.session_state.last_updated = None

if "portfolio_holdings" not in st.session_state:
    st.session_state.portfolio_holdings = ()
if "portfolio_rows" not in st.session_state:
    st.session_state.portfolio_rows = ()
if "portfolio_warnings" not in st.session_state:
    st.session_state.portfolio_warnings = ()
if "portfolio_diagnostics" not in st.session_state:
    st.session_state.portfolio_diagnostics = configured_portfolio_diagnostics()
if "portfolio_sync_result" not in st.session_state:
    st.session_state.portfolio_sync_result = None
if "portfolio_sync_cached_at" not in st.session_state:
    st.session_state.portfolio_sync_cached_at = None
if "portfolio_sync_from_cache" not in st.session_state:
    st.session_state.portfolio_sync_from_cache = False
if "portfolio_sync_pending" not in st.session_state:
    portfolio_settings = get_settings().portfolio_sync
    has_crypto_results = "crypto" in st.session_state.get("results", {})
    st.session_state.portfolio_sync_pending = (
        portfolio_settings.enabled and has_crypto_results
    )

st.markdown(
    """
    <div class="main-title">
        <h1>Trading Signal Dashboard</h1>
        <p>Crypto, PSX, and PMEX signals in one refreshable visual workspace.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

refresh_column, download_column = st.columns([1, 1])
with refresh_column:
    st.write("")
    refresh = st.button("Refresh Results", type="primary", use_container_width=True)
with download_column:
    st.write("")
    workbook_path = st.session_state.get("workbook_path")
    if workbook_path and Path(workbook_path).exists():
        with Path(workbook_path).open("rb") as file:
            st.download_button(
                "Download Excel",
                file,
                file_name=Path(workbook_path).name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

if cleared_invalid_results:
    st.warning(
        "Cleared in-memory results that were not from a production scan "
        "(proof/auth-fallback rows). Click **Refresh Results** to run a live production scan."
    )

if refresh:
    try:
        selected = "all"
        cached_result = st.session_state.get("portfolio_sync_result")
        cached_symbols = (
            cached_result.portfolio_symbols
            if isinstance(cached_result, PortfolioSyncResult)
            else ()
        )
        crypto_symbols = stable_unique_symbols(
            configured_crypto_symbols(),
            cached_symbols,
        )
        results, out_path = run_refresh(
            selected,
            crypto_symbols=crypto_symbols,
        )
        st.session_state.results = results
        st.session_state.workbook_path = out_path
        st.session_state.last_updated = datetime.now()
        portfolio_settings = get_settings().portfolio_sync
        st.session_state.portfolio_sync_pending = (
            portfolio_settings.enabled and "crypto" in markets_to_run(selected)
        )
        st.rerun()
    except (AIAuthenticationError, AIConfigurationError, AIExecutionError) as error:
        st.error(f"AI configuration/authentication failed: {error}")
        st.stop()

if st.session_state.get("portfolio_sync_pending"):
    portfolio_settings = get_settings().portfolio_sync
    cached_result = (
        st.session_state.get("portfolio_sync_result")
        if isinstance(st.session_state.get("portfolio_sync_result"), PortfolioSyncResult)
        else None
    )
    if should_run_portfolio_sync(
        refresh_clicked=False,
        force=True,
        cached_result=cached_result,
        cached_at=st.session_state.get("portfolio_sync_cached_at"),
        cache_ttl_seconds=portfolio_settings.cache_ttl_seconds,
        portfolio_sync_enabled=portfolio_settings.enabled,
    ):
        new_result = sync_binance_portfolio_with_timeout(
            portfolio_settings.sync_timeout_seconds
        )
        portfolio_result, portfolio_from_cache = resolve_portfolio_sync_result(
            new_result,
            cached_result,
        )
        if new_result.sync_succeeded:
            st.session_state.portfolio_sync_result = new_result
            st.session_state.portfolio_sync_cached_at = datetime.now()
    else:
        portfolio_result = cached_result or PortfolioSyncResult()
        portfolio_from_cache = cached_result is not None
    crypto_rows = (
        st.session_state.get("results", {}).get("crypto", pd.DataFrame()).to_dict(orient="records")
    )
    portfolio_rows = project_portfolio_signals(
        portfolio_result.holdings,
        crypto_rows,
    )
    st.session_state.portfolio_holdings = portfolio_result.holdings
    st.session_state.portfolio_rows = portfolio_rows
    st.session_state.portfolio_warnings = portfolio_result.warnings
    st.session_state.portfolio_diagnostics = portfolio_result.diagnostics
    st.session_state.portfolio_sync_from_cache = portfolio_from_cache
    st.session_state.portfolio_sync_pending = False
    st.rerun()

last_updated = st.session_state.get("last_updated")
workbook_path_display = st.session_state.get("workbook_path")
if last_updated and workbook_path_display:
    meta = (
        read_workbook_metadata(Path(workbook_path_display))
        if Path(str(workbook_path_display)).exists()
        else {}
    )
    generator = meta.get("generator", "unknown")
    st.caption(
        f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Workbook: {workbook_path_display} | generator={generator}"
    )
else:
    st.info("No production scan available")

results = st.session_state.get("results", {})
available_tabs = [
    (market, MARKET_SHEETS[market]) for market in ["psx", "crypto", "pmex"] if market in results
]
if not available_tabs:
    st.stop()
else:
    tabs = st.tabs([sheet for _, sheet in available_tabs])
    for tab, (market, sheet_name) in zip(tabs, available_tabs, strict=True):
        with tab:
            # Crypto tab order: Portfolio Holdings → Portfolio Signals → Scanner Results → Diagnostics
            if market == "crypto" and get_settings().portfolio_sync.enabled:
                portfolio_holdings = tuple(st.session_state.get("portfolio_holdings", ()))
                
                # 1. Portfolio Holdings (user's actual Binance positions)
                render_portfolio_holdings(
                    portfolio_holdings,
                    tuple(st.session_state.get("portfolio_warnings", ())),
                )
                
                # 2. Portfolio Signals (analysis for user's positions)
                render_portfolio_signals(
                    tuple(st.session_state.get("portfolio_rows", ())),
                    tuple(st.session_state.get("portfolio_warnings", ())),
                    st.session_state.get(
                        "portfolio_diagnostics",
                        configured_portfolio_diagnostics(),
                    ),
                    holdings=portfolio_holdings,
                    from_cache=bool(st.session_state.get("portfolio_sync_from_cache")),
                )
            
            # 3-5. Scanner metrics, charts, and signal details
            render_market(sheet_name, results.get(market, pd.DataFrame()), market=market)
            
            # 6. Collapsed diagnostics at bottom
            with st.expander("System and diagnostics", expanded=False):
                diagnostics = startup_diagnostics()
                universe = configured_universe_counts()
                st.caption(
                    f"Provider: {diagnostics['provider']} · SDK: {diagnostics['sdk']} · "
                    f"Model: {diagnostics['model']} · API key configured: "
                    f"{diagnostics['api_key_configured']} · Auth: {diagnostics['authentication_method']}"
                )
                st.caption(
                    f"Monitored universe: {universe['crypto']} crypto · "
                    f"{universe['psx']} PSX · {universe['pmex']} PMEX · "
                    f"{universe['total']} total (config/signal_universe.yaml)"
                )
                
                # Portfolio sync diagnostics only in crypto tab
                if market == "crypto" and get_settings().portfolio_sync.enabled:
                    render_portfolio_sync_diagnostics(
                        st.session_state.portfolio_diagnostics,
                        tuple(st.session_state.portfolio_warnings),
                    )
