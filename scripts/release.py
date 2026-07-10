#!/usr/bin/env python3
"""Release readiness validation runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    python = sys.executable
    steps = [
        [python, "scripts/validate_release.py"],
        [python, "scripts/validate_phase0.py"],
    ]
    for command in steps:
        print(f"Running: {' '.join(command)}")
        completed = subprocess.run(command, cwd=project_root, check=False)
        if completed.returncode != 0:
            print("Release validation failed.")
            return completed.returncode
    print("Release validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
