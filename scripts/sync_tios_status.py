"""Sync derived TIOS status snapshots from NEXT_TASK + sprint metadata."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "development"
MASTER = DEV / "00_MASTER"
STATUS_DIR = DEV / "10_STATUS"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _extract_active_task(next_task: str) -> str:
    match = re.search(
        r"\|\s*Active coding task\s*\|\s*(.+?)\s*\|",
        next_task,
        flags=re.IGNORECASE,
    )
    if not match:
        return "unknown"
    return re.sub(r"\*+", "", match.group(1)).strip()


def _extract_sprint_line(status: str) -> str:
    match = re.search(r"\|\s*Current sprint\s*\|\s*(.+?)\s*\|", status)
    return match.group(1).strip() if match else "unknown"


def sync(dry_run: bool = False) -> None:
    today = date.today().isoformat()
    next_task = _read(MASTER / "NEXT_TASK.md")
    project_status = _read(MASTER / "PROJECT_STATUS.md")
    active = _extract_active_task(next_task)
    sprint = _extract_sprint_line(project_status)

    # Refresh last-updated stamps
    project_status = re.sub(
        r"\*\*Last updated:\*\*.*",
        f"**Last updated:** {today}",
        project_status,
        count=1,
    )
    next_task = re.sub(
        r"\*\*Last synced:\*\*.*",
        f"**Last synced:** {today}",
        next_task,
        count=1,
    )

    signal_status = "Planning complete; implementation queued"
    if active.lower() == "none":
        readiness = (
            DEV / "02_PHASES" / "phase_signal" / "SIGNAL_ENGINE_V1_READINESS.md"
        )
        if readiness.exists() and "accepted" in readiness.read_text(encoding="utf-8").lower():
            signal_status = "V1.0 path accepted; awaiting next task open"
        else:
            signal_status = "Awaiting next task open"
    elif active.upper().startswith("PAPER-PLAN"):
        signal_status = "V1.0 accepted; paper trading planning in progress"
    elif active.upper().startswith("PAPER-"):
        signal_status = f"V1.0 accepted; paper trading implementation ({active})"
    elif active.upper().startswith("BACKTEST-"):
        signal_status = f"V1.0 accepted; backtesting implementation ({active})"
    elif active.upper().startswith("VALIDATION-"):
        signal_status = f"V1.0 accepted; prediction validation implementation ({active})"
    elif active.upper().startswith("STRATEGY-"):
        signal_status = f"V1.0 accepted; strategy builder implementation ({active})"
    elif active.upper().startswith("SIG-PLAN"):
        signal_status = "Planning in progress"
    elif active.upper().startswith("SIG-"):
        signal_status = f"Implementation ready/active ({active})"

    current = f"""# Current Status Snapshot

**Date:** {today}
**Auto-synced by:** `scripts/sync_tios_status.py`

| Field | Value |
|-------|-------|
| Sprint | {sprint} |
| Active coding task | {active} |
| Milestone | {sprint} |
| Phase 0 | Certified |
| Foundation | Certified v1.0.0 |
| Phase 2 ML | Complete |
| Signal Engine | {signal_status} |
| Broker automation | Disabled |
| Coverage gate | >= 88% |
| Last certifications | PHASE0 + FOUNDATION docs at repo root |
| Sync sources | `PROJECT_STATUS.md`, `00_MASTER/NEXT_TASK.md`, `CHANGELOG.md` |

See also `../00_MASTER/PROJECT_STATUS.md`, `../00_MASTER/NEXT_TASK.md`, and `NEXT_TASK.md`.
"""

    if dry_run:
        print("DRY RUN — would update:")
        print(f"- {MASTER / 'PROJECT_STATUS.md'} last-updated -> {today}")
        print(f"- {MASTER / 'NEXT_TASK.md'} last-synced -> {today}")
        print(f"- {STATUS_DIR / 'NEXT_TASK.md'} mirrored")
        print(f"- {STATUS_DIR / 'CURRENT.md'} regenerated")
        print(f"Active task: {active}")
        print(f"Sprint: {sprint}")
        return

    _write(MASTER / "PROJECT_STATUS.md", project_status)
    _write(MASTER / "NEXT_TASK.md", next_task)
    _write(STATUS_DIR / "NEXT_TASK.md", next_task)
    _write(STATUS_DIR / "CURRENT.md", current)
    print("TIOS status sync complete.")
    print(f"  date={today}")
    print(f"  sprint={sprint}")
    print(f"  active_task={active}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show sync actions without writing files",
    )
    args = parser.parse_args()
    sync(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
