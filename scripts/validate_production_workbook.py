"""Print production workbook validation proof for dashboard isolation fix."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.signal_workbook import (  # noqa: E402
    PRODUCTION_DIR,
    PRODUCTION_GENERATOR,
    latest_production_workbook,
    read_workbook_metadata,
)
from main import MARKET_SHEETS  # noqa: E402


def load_market_sheets(path: Path) -> dict[str, pd.DataFrame]:
    data = pd.read_excel(path, sheet_name=None)
    return {
        market: data[sheet]
        for market, sheet in MARKET_SHEETS.items()
        if sheet in data
    }


def main() -> int:
    wb = latest_production_workbook()
    print("Production workbook path:", wb)
    if wb is None:
        print("FAIL: no production workbook")
        return 1
    assert wb.parent.resolve() == PRODUCTION_DIR.resolve()
    meta = read_workbook_metadata(wb)
    print("Workbook metadata:", meta)
    print("Generator =", meta.get("generator"))
    assert meta.get("generator") == PRODUCTION_GENERATOR

    loaded = load_market_sheets(wb)
    for market in ("crypto", "psx", "pmex"):
        df = loaded[market]
        print(f"{market.upper()} rows =", len(df))
        proofish = df["reasoning"].astype(str).str.startswith("Proof scan for").any()
        print("  proof_reasoning_present =", proofish)
        assert not proofish
        print("  signal_counts =", df["signal"].value_counts().to_dict())

    # Dashboard eligibility uses the same production-only helper.
    from dashboard import latest_workbook  # noqa: WPS433

    dash_wb = latest_workbook()
    print("Dashboard source workbook:", dash_wb)
    assert dash_wb is not None and dash_wb.resolve() == wb.resolve()
    print('CONFIRM: reasoning is no longer "Proof scan for ..."')
    print("VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
