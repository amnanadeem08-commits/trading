"""Tests for production vs proof workbook isolation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core import signal_workbook as sw
from core.signal_workbook import (
    PRODUCTION_GENERATOR,
    ensure_artifact_dirs,
    is_production_workbook,
    latest_production_workbook,
    read_workbook_metadata,
)
from dashboard import _is_loadable_workbook, latest_workbook
from main import save_results


def _sample_frames() -> dict[str, pd.DataFrame]:
    row = {
        "symbol": "BTC/USDT",
        "signal": "BUY",
        "confidence": "medium",
        "reasoning": "Live technical edge.",
        "fomo_fear_note": "n/a",
        "invalidation": "n/a",
    }
    return {
        "crypto": pd.DataFrame([row]),
        "psx": pd.DataFrame([{**row, "symbol": "MARI.KA"}]),
        "pmex": pd.DataFrame([{**row, "symbol": "GOLD"}]),
    }


def test_production_save_goes_to_outputs_production(tmp_path, monkeypatch) -> None:
    prod = tmp_path / "production"
    proof = tmp_path / "proof"
    prod.mkdir()
    proof.mkdir()
    monkeypatch.setattr(sw, "PRODUCTION_DIR", prod)
    monkeypatch.setattr(sw, "PROOF_DIR", proof)
    monkeypatch.setattr(sw, "ARCHIVE_PROOF_DIR", tmp_path / "archive_proof")

    path = Path(
        save_results(
            _sample_frames(),
            "all",
            generator=PRODUCTION_GENERATOR,
            source="unit_test",
            output_dir=prod,
        )
    )
    assert path.parent.resolve() == prod.resolve()
    meta = read_workbook_metadata(path)
    assert meta["generator"] == "production_scan"
    # is_production_workbook uses module PRODUCTION_DIR — patched above.
    assert is_production_workbook(path)


def test_proof_save_never_selected_by_latest_workbook(tmp_path, monkeypatch) -> None:
    prod = tmp_path / "production"
    proof = tmp_path / "proof"
    prod.mkdir()
    proof.mkdir()
    monkeypatch.setattr(sw, "PRODUCTION_DIR", prod)
    monkeypatch.setattr(sw, "PROOF_DIR", proof)
    monkeypatch.setattr(sw, "ARCHIVE_PROOF_DIR", tmp_path / "archive_proof")
    # dashboard helpers import PRODUCTION_DIR at call time via is_production_workbook
    import dashboard as dash

    monkeypatch.setattr(dash, "PRODUCTION_DIR", prod)
    monkeypatch.setattr(dash, "_WORKBOOK_DIR", prod)

    proof_path = Path(
        save_results(
            _sample_frames(),
            "all",
            generator="proof_scan",
            source="unit_test",
            output_dir=proof,
        )
    )
    assert proof_path.parent.resolve() == proof.resolve()
    assert read_workbook_metadata(proof_path)["generator"] == "proof_scan"
    assert not is_production_workbook(proof_path)
    latest = latest_workbook()
    assert latest is None or latest.resolve() != proof_path.resolve()
    prod_latest = latest_production_workbook()
    assert prod_latest is None or prod_latest.resolve() != proof_path.resolve()


def test_blocked_prefix_rejected_even_in_production_dir(tmp_path, monkeypatch) -> None:
    prod = tmp_path / "production"
    prod.mkdir()
    monkeypatch.setattr(sw, "PRODUCTION_DIR", prod)
    bad = prod / "proof_signals_all_20990101_0000.xlsx"
    frames = _sample_frames()
    with pd.ExcelWriter(bad, engine="openpyxl") as writer:
        pd.DataFrame(
            [{"key": "generator", "value": "production_scan"}]
        ).to_excel(writer, sheet_name="_Meta", index=False)
        frames["crypto"].to_excel(writer, sheet_name="Crypto", index=False)
    assert not is_production_workbook(bad)
    assert not _is_loadable_workbook(bad)


def test_missing_meta_rejected(tmp_path, monkeypatch) -> None:
    prod = tmp_path / "production"
    prod.mkdir()
    monkeypatch.setattr(sw, "PRODUCTION_DIR", prod)
    bare = prod / "signals_all_20990101_0001.xlsx"
    frames = _sample_frames()
    with pd.ExcelWriter(bare, engine="openpyxl") as writer:
        frames["crypto"].to_excel(writer, sheet_name="Crypto", index=False)
    assert not is_production_workbook(bare)
