#!/usr/bin/env python3
"""Bootstrap the development environment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    python = sys.executable

    if sys.version_info < (3, 14):
        print(f"FAIL: Python 3.14+ required, found {sys.version}")
        return 1

    commands = [
        [python, "-m", "pip", "install", "--upgrade", "pip"],
        [python, "-m", "pip", "install", "-e", f"{project_root}[dev]"],
    ]
    for command in commands:
        print(f"Running: {' '.join(command)}")
        completed = subprocess.run(command, cwd=project_root, check=False)
        if completed.returncode != 0:
            print(f"FAIL: command exited {completed.returncode}")
            return completed.returncode

    validators = [
        [python, "scripts/validate_environment.py"],
        [python, "scripts/validate_dependencies.py"],
        [python, "scripts/validate_configuration.py"],
    ]
    for command in validators:
        print(f"Running: {' '.join(command)}")
        completed = subprocess.run(command, cwd=project_root, check=False)
        if completed.returncode != 0:
            return completed.returncode

    print("Bootstrap complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
