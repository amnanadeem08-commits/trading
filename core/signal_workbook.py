"""Production vs proof signal workbook isolation.

Production scans write only to ``outputs/production/``.
Proof / test scans write only to ``artifacts/proof/``.

The dashboard may load workbooks only from ``outputs/production/`` and only when
workbook metadata ``generator`` equals ``production_scan``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pandas as pd

GeneratorKind = Literal[
    "production_scan",
    "proof_scan",
    "unit_test",
    "integration_test",
]

VALID_GENERATORS: frozenset[str] = frozenset(
    {"production_scan", "proof_scan", "unit_test", "integration_test"}
)
PRODUCTION_GENERATOR = "production_scan"
META_SHEET = "_Meta"

# Filename prefixes that must never be treated as production, even if misplaced.
_BLOCKED_NAME_PREFIXES = (
    "proof_",
    "demo_",
    "mock_",
    "test_",
    "verification_",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR = REPO_ROOT / "outputs" / "production"
PROOF_DIR = REPO_ROOT / "artifacts" / "proof"
ARCHIVE_PROOF_DIR = REPO_ROOT / "archive" / "proof"


def ensure_artifact_dirs() -> None:
    PRODUCTION_DIR.mkdir(parents=True, exist_ok=True)
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PROOF_DIR.mkdir(parents=True, exist_ok=True)


def output_dir_for_generator(generator: str) -> Path:
    if generator not in VALID_GENERATORS:
        raise ValueError(f"Unsupported generator: {generator!r}")
    if generator == PRODUCTION_GENERATOR:
        return PRODUCTION_DIR
    return PROOF_DIR


def has_blocked_name_prefix(path: Path) -> bool:
    name = path.name.lower()
    return any(name.startswith(prefix) for prefix in _BLOCKED_NAME_PREFIXES)


def write_meta_sheet(
    writer: pd.ExcelWriter,
    *,
    generator: str,
    selected_market: str,
    source: str,
) -> None:
    if generator not in VALID_GENERATORS:
        raise ValueError(f"Unsupported generator: {generator!r}")
    meta = pd.DataFrame(
        [
            {"key": "generator", "value": generator},
            {"key": "selected_market", "value": selected_market},
            {"key": "source", "value": source},
            {
                "key": "created_at_utc",
                "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        ]
    )
    meta.to_excel(writer, sheet_name=META_SHEET, index=False)


def read_workbook_metadata(path: Path) -> dict[str, str]:
    """Return key/value metadata from the ``_Meta`` sheet (empty if missing)."""
    try:
        df = pd.read_excel(path, sheet_name=META_SHEET)
    except Exception:
        return {}
    if df is None or df.empty or "key" not in df.columns or "value" not in df.columns:
        return {}
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        key = str(row["key"]).strip()
        if not key or key.lower() == "nan":
            continue
        out[key] = "" if pd.isna(row["value"]) else str(row["value"]).strip()
    return out


def workbook_generator(path: Path) -> str | None:
    meta = read_workbook_metadata(path)
    generator = meta.get("generator")
    if not generator:
        return None
    return generator if generator in VALID_GENERATORS else None


def is_production_workbook(path: Path) -> bool:
    """True only for production-tagged workbooks under outputs/production/."""
    resolved = path.resolve()
    try:
        resolved.relative_to(PRODUCTION_DIR.resolve())
    except ValueError:
        return False
    if resolved.parent != PRODUCTION_DIR.resolve():
        return False
    if has_blocked_name_prefix(resolved):
        return False
    if not resolved.name.lower().startswith("signals_"):
        return False
    if resolved.suffix.lower() != ".xlsx":
        return False
    return workbook_generator(resolved) == PRODUCTION_GENERATOR


def list_production_workbooks() -> list[Path]:
    ensure_artifact_dirs()
    return sorted(
        (p for p in PRODUCTION_DIR.glob("signals_*.xlsx") if is_production_workbook(p)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def latest_production_workbook() -> Path | None:
    files = list_production_workbooks()
    return files[0] if files else None
