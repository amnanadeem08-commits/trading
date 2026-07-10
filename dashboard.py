"""
Interactive web dashboard for PSX + Crypto signal results.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core.llm_analyzer import AIAuthenticationError, AIConfigurationError, AIExecutionError, assert_ai_ready, provider_status, startup_diagnostics
from main import MARKET_SHEETS, markets_to_run, save_results, scan_market


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
    initial_sidebar_state="expanded",
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


def latest_workbook() -> Path | None:
    files = sorted(Path(".").glob("signals_*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_workbook(path: Path) -> dict[str, pd.DataFrame]:
    data = pd.read_excel(path, sheet_name=None)
    normalized = {}
    for market, sheet in MARKET_SHEETS.items():
        if sheet in data:
            normalized[market] = data[sheet]
    return normalized


def run_refresh(selected_market: str) -> tuple[dict[str, pd.DataFrame], str]:
    assert_ai_ready(verify_remote=True)
    results = {}
    for market in markets_to_run(selected_market):
        with st.status(f"Refreshing {MARKET_SHEETS[market]} data...", expanded=False):
            results[market] = scan_market(market)
    out_path = save_results(results, selected_market)
    return results, out_path


def signal_counts(df: pd.DataFrame) -> pd.Series:
    if df.empty or "signal" not in df.columns:
        return pd.Series(dtype="int64")
    return df["signal"].fillna("n/a").value_counts()


def render_metric_cards(df: pd.DataFrame):
    counts = signal_counts(df)
    total = int(counts.sum()) if not counts.empty else 0
    buy = int(counts.get("BUY", 0))
    sell = int(counts.get("SELL", 0))
    hold = int(counts.get("HOLD", 0))
    high_conf = int((df.get("confidence", pd.Series(dtype=str)).fillna("").str.lower() == "high").sum()) if not df.empty else 0

    cards = [
        ("Assets", total, "scanned successfully"),
        ("BUY", buy, "opportunity signals"),
        ("SELL", sell, "risk-off signals"),
        ("HOLD", hold, f"{high_conf} high confidence"),
    ]
    columns = st.columns(4)
    for column, (label, value, help_text) in zip(columns, cards):
        with column:
            st.metric(label=label, value=value, help=help_text)


def render_charts(df: pd.DataFrame, sheet_name: str):
    left, right = st.columns([1, 1])
    counts = signal_counts(df).rename_axis("signal").reset_index(name="count")
    if counts.empty:
        st.info(f"No {sheet_name} rows to chart yet.")
        return

    color_map = {row["signal"]: SIGNAL_COLORS.get(row["signal"], "#6b7280") for _, row in counts.iterrows()}
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
        conf = df.get("confidence", pd.Series(dtype=str)).fillna("n/a").value_counts().rename_axis("confidence").reset_index(name="count")
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

    for _, row in display_df.head(12).iterrows():
        signal = str(row.get("signal", "n/a"))
        color = SIGNAL_COLORS.get(signal, "#6b7280")
        reasoning = str(row.get("reasoning", "No reasoning available."))
        confidence = str(row.get("confidence", "n/a"))
        invalidation = str(row.get("invalidation", "n/a"))
        st.markdown(
            f'''
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
            ''',
            unsafe_allow_html=True,
        )


def render_market(sheet_name: str, df: pd.DataFrame):
    render_metric_cards(df)
    render_charts(df, sheet_name)
    st.markdown("#### Signal Details")
    render_asset_cards(df)
    with st.expander("Full table"):
        st.dataframe(df, use_container_width=True, hide_index=True)


st.markdown(
    """
    <div class="main-title">
        <h1>Trading Signal Dashboard</h1>
        <p>PSX and crypto signals in one refreshable visual workspace.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Refresh")
    diagnostics = startup_diagnostics()
    st.caption(f"Provider: {diagnostics['provider']}")
    st.caption(f"SDK: {diagnostics['sdk']}")
    st.caption(f"Base URL: {diagnostics['base_url']}")
    st.caption(f"Model: {diagnostics['model']}")
    st.caption(f"API key configured: {diagnostics['api_key_configured']}")
    st.caption(f"Auth method: {diagnostics['authentication_method']}")
    selected_market = st.segmented_control(
        "Market",
        options=["both", "psx", "crypto"],
        default="both",
        format_func=lambda value: {"both": "Both", "psx": "PSX", "crypto": "Crypto"}[value],
    )
    st.caption("Refresh fetches live data, runs indicators, saves a new Excel workbook, and updates charts.")
    refresh = st.button("Refresh Results", type="primary", use_container_width=True)

    st.divider()
    workbook_path = st.session_state.get("workbook_path")
    if workbook_path and Path(workbook_path).exists():
        with open(workbook_path, "rb") as file:
            st.download_button(
                "Download Excel",
                file,
                file_name=Path(workbook_path).name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

if "results" not in st.session_state:
    latest = latest_workbook()
    if latest:
        st.session_state.results = load_workbook(latest)
        st.session_state.workbook_path = str(latest)
        st.session_state.last_updated = datetime.fromtimestamp(latest.stat().st_mtime)
    else:
        st.session_state.results = {}
        st.session_state.workbook_path = None
        st.session_state.last_updated = None

if refresh:
    try:
        results, out_path = run_refresh(selected_market)
        st.session_state.results = results
        st.session_state.workbook_path = out_path
        st.session_state.last_updated = datetime.now()
        st.rerun()
    except (AIAuthenticationError, AIConfigurationError, AIExecutionError) as error:
        st.error(f"AI configuration/authentication failed: {error}")
        st.stop()

last_updated = st.session_state.get("last_updated")
if last_updated:
    st.caption(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')} | Workbook: {st.session_state.get('workbook_path')}")
else:
    st.info("No workbook found yet. Click Refresh Results to generate the first dashboard data.")

results = st.session_state.get("results", {})
available_tabs = [(market, MARKET_SHEETS[market]) for market in ["psx", "crypto"] if market in results]
if not available_tabs:
    st.stop()

tabs = st.tabs([sheet for _, sheet in available_tabs])
for tab, (market, sheet_name) in zip(tabs, available_tabs):
    with tab:
        render_market(sheet_name, results.get(market, pd.DataFrame()))




