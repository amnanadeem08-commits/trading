#!/usr/bin/env python3
"""Development command runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMMANDS: dict[str, list[str]] = {
    "lint": [
        "-m",
        "ruff",
        "check",
        "models",
        "config",
        "connectors",
        "events",
        "versioning",
        "audit",
        "feature_flags",
        "research",
        "architecture",
        "health",
        "metrics",
        "platform_logging",
        "security",
        "notifications",
        "monitoring",
        "scripts",
        "tests",
    ],
    "format": [
        "-m",
        "black",
        "models",
        "config",
        "connectors",
        "events",
        "versioning",
        "audit",
        "feature_flags",
        "research",
        "architecture",
        "health",
        "metrics",
        "platform_logging",
        "security",
        "notifications",
        "monitoring",
        "scripts",
        "tests",
    ],
    "typecheck": [
        "-m",
        "mypy",
        "models",
        "config",
        "connectors",
        "events",
        "versioning",
        "audit",
        "feature_flags",
        "research",
        "architecture",
        "health",
        "metrics",
        "platform_logging",
        "security",
        "notifications",
        "monitoring",
    ],
    "test": [
        "-m",
        "pytest",
        "tests/unit",
        "tests/contract",
        "tests/architecture",
        "tests/integration",
        "-v",
    ],
    "coverage": [
        "-m",
        "pytest",
        "tests/unit",
        "tests/contract",
        "tests/architecture",
        "tests/integration",
        "-q",
        "--cov-fail-under=88",
        "--cov=models",
        "--cov=config",
        "--cov=connectors",
        "--cov=events",
        "--cov=versioning",
        "--cov=audit",
        "--cov=feature_flags",
        "--cov=research",
        "--cov=architecture",
        "--cov=health",
        "--cov=metrics",
        "--cov=platform_logging",
        "--cov=security",
        "--cov=notifications",
        "--cov=monitoring",
    ],
    "architecture": ["scripts/validate_architecture.py"],
    "phase0": ["scripts/validate_phase0.py"],
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python scripts/dev.py <command>")
        print(f"Commands: {', '.join(sorted(COMMANDS))}")
        return 1

    project_root = Path(__file__).resolve().parents[1]
    command_key = sys.argv[1]
    args = COMMANDS[command_key]
    if args[0].endswith(".py"):
        command = [sys.executable, *args]
    else:
        command = [sys.executable, *args]
    completed = subprocess.run(command, cwd=project_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
