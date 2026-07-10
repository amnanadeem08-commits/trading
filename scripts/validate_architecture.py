#!/usr/bin/env python3
"""Validate frozen architecture rules and emit a human-readable report."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from architecture.reporting import format_report, format_summary
    from architecture.validators import ArchitectureValidator

    report = ArchitectureValidator(project_root).validate_all()
    print(format_report(report))
    print("")
    print(f"Summary: {format_summary(report)}")
    return 1 if report.violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
