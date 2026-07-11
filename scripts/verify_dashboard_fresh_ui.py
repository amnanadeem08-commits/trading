"""Fresh UI verification: empty session → Refresh Results → multi-asset workbook."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest

from core.signal_universe import configured_crypto_symbols, configured_psx_symbols
from core.signal_workbook import ARCHIVE_PROOF_DIR, PRODUCTION_DIR, ensure_artifact_dirs

WORKBOOK_DIR = PRODUCTION_DIR
ARCHIVE_DIR = ROOT / "archive"


def workbook_has_auth_hold_fallback(path: Path) -> bool:
    import pandas as pd

    markers = (
        "Analysis failed, defaulting to HOLD for safety",
        "Could not resolve authentication method",
    )
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception:
        return False
    for name, df in sheets.items():
        if name == "_Meta" or df is None or df.empty or "reasoning" not in df.columns:
            continue
        reasoning = df["reasoning"].astype(str)
        if reasoning.str.contains("|".join(markers), regex=True, na=False).any():
            return True
    return False


def main_verify() -> int:
    # Do not truncate the configured universe — that caused the single-asset bug.
    expected_crypto = configured_crypto_symbols()
    expected_psx = configured_psx_symbols()
    ensure_artifact_dirs()
    ARCHIVE_DIR.mkdir(exist_ok=True)
    ARCHIVE_PROOF_DIR.mkdir(parents=True, exist_ok=True)

    for path in list(WORKBOOK_DIR.glob("signals_*.xlsx")):
        path.rename(ARCHIVE_PROOF_DIR / f"pre_multi_{path.name}")

    before = {p.name for p in WORKBOOK_DIR.glob("signals_*.xlsx")}
    assert not before, f"production dir must be empty before UI run, found {before}"

    at = AppTest.from_file(str(ROOT / "dashboard.py"), default_timeout=3600)
    at.run()

    results0 = at.session_state["results"] if "results" in at.session_state else None
    path0 = at.session_state["workbook_path"] if "workbook_path" in at.session_state else None
    assert results0 in (None, {}), f"stale results in session: {results0!r}"
    assert path0 in (None, ""), f"stale workbook_path in session: {path0!r}"

    controls = list(at.sidebar.segmented_control)
    assert controls, "Market segmented_control missing"
    controls[0].set_value("both")

    buttons = [b for b in at.sidebar.button if "Refresh" in (b.label or "")]
    assert buttons, "Refresh Results button missing"
    t0 = time.time()
    buttons[0].click().run(timeout=3600)
    elapsed = time.time() - t0

    if at.exception:
        print("UI_EXCEPTION:", at.exception)
        return 1
    if at.error:
        print("UI_ERROR:", [getattr(e, "value", e) for e in at.error])
        return 1

    results = at.session_state["results"] if "results" in at.session_state else {}
    workbook_path = (
        at.session_state["workbook_path"] if "workbook_path" in at.session_state else None
    )
    assert workbook_path, "session_state.workbook_path missing after refresh"
    wb = Path(workbook_path)
    assert wb.exists(), f"workbook missing: {wb}"
    assert wb.parent.resolve() == PRODUCTION_DIR.resolve(), wb
    assert not workbook_has_auth_hold_fallback(wb)

    crypto = results.get("crypto")
    psx = results.get("psx")
    assert crypto is not None and not crypto.empty, "crypto results empty"
    assert psx is not None and not psx.empty, "psx results empty"
    assert len(crypto) == len(expected_crypto), (
        f"crypto rows {len(crypto)} != configured {len(expected_crypto)}"
    )
    assert len(psx) == len(expected_psx), (
        f"psx rows {len(psx)} != configured {len(expected_psx)}"
    )

    crypto_syms = set(crypto["symbol"].astype(str))
    psx_syms = set(psx["symbol"].astype(str))
    assert crypto_syms == set(expected_crypto)
    assert psx_syms == set(expected_psx)
    assert not crypto["reasoning"].astype(str).str.startswith("Analysis failed").any()
    assert not psx["reasoning"].astype(str).str.startswith("Analysis failed").any()
    assert not crypto["reasoning"].astype(str).str.startswith("Proof scan for").any()
    assert not psx["reasoning"].astype(str).str.startswith("Proof scan for").any()

    report = {
        "current_workbook_filename": wb.name,
        "workbook_path": str(wb),
        "workbook_timestamp": time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(wb.stat().st_mtime)
        ),
        "crypto_count": int(len(crypto)),
        "psx_count": int(len(psx)),
        "crypto_symbols": sorted(crypto_syms),
        "psx_symbols": sorted(psx_syms),
        "is_hold_fallback": False,
        "cached_workbook_reused": False,
        "ui_elapsed_sec": round(elapsed, 1),
        "signal_counts_crypto": crypto["signal"].value_counts().to_dict(),
        "signal_counts_psx": psx["signal"].value_counts().to_dict(),
    }
    print("VERIFICATION_REPORT")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_verify())
