"""Validate TIOS integrity: links, phases, templates, workflow, CI sync, status sync."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "development"
WORKFLOWS = ROOT / ".github" / "workflows"

PHASE_DIRS = [
    "phase_0",
    "phase_foundation",
    "phase_2_ml",
    "phase_tios",
    "phase_signal",
    "phase_paper",
]

SPRINT_REQUIRED = [
    "## Goal",
    "## Scope",
    "## Dependencies",
    "## Architecture Changes",
    "## Files Created",
    "## Files Modified",
    "## Tests",
    "## Validation",
    "## Acceptance Criteria",
    "## Future Impact",
    "## Completion Report",
]

TASK_REQUIRED = [
    "## Sprint",
    "## Goal",
    "## Scope",
    "## Out of Scope",
    "## Dependencies",
    "## Architecture Impact",
    "## Implementation Notes",
    "## Files Expected",
    "## Tests Required",
    "## Validation Gates",
    "## Acceptance Criteria",
    "## Status",
    "## Completion Notes",
]

COMPLETION_REQUIRED = [
    "## Delivered",
    "## Validation",
    "## Acceptance",
    "## Next",
]

WORKFLOW_READS = [
    DEV / "00_MASTER" / "MASTER_ROADMAP.md",
    DEV / "00_MASTER" / "PROJECT_STATUS.md",
    DEV / "00_MASTER" / "NEXT_TASK.md",
    DEV / "10_STATUS" / "NEXT_TASK.md",
    DEV / "01_GLOBAL_RULES" / "RULEBOOK.md",
    DEV / "01_GLOBAL_RULES" / "ARCHITECTURE_RULES.md",
    DEV / "07_CURSOR" / "WORKFLOW.md",
    DEV / "05_VALIDATION" / "GATES.md",
    ROOT / "AGENTS.md",
    ROOT / ".cursor" / "rules" / "tios-workflow.mdc",
]

CI_REQUIRED_FILES = {
    "lint.yml": ["ruff", "black"],
    "typing.yml": ["mypy"],
    "architecture.yml": [
        "validate_architecture.py",
        "importlinter",
        "tests/architecture",
    ],
    "tests.yml": ["pytest"],
    "coverage.yml": ["cov-fail-under=88", "pytest"],
    "dependencies.yml": ["validate_dependencies.py"],
    "release.yml": ["release.py"],
}

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^## .+$", re.MULTILINE)


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _resolve_link(source: Path, target: str) -> Path | None:
    raw = target.strip()
    if not raw or raw.startswith(("http://", "https://", "mailto:")):
        return None
    if raw.startswith("#"):
        return source
    path_part = raw.split("#", 1)[0]
    if not path_part:
        return source
    candidate = (source.parent / path_part).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return candidate
    return candidate


def check_links(findings: Findings) -> None:
    roots = [DEV, ROOT / "AGENTS.md", ROOT / "README.md"]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(root.rglob("*.md"))
    rule = ROOT / ".cursor" / "rules" / "tios-workflow.mdc"
    if rule.exists():
        files.append(rule)

    for path in files:
        text = path.read_text(encoding="utf-8")
        for _label, target in LINK_RE.findall(text):
            resolved = _resolve_link(path, target)
            if resolved is None:
                continue
            if not resolved.exists():
                findings.err(
                    f"Broken link in {path.relative_to(ROOT)}: ({target}) -> missing"
                )


def check_phases(findings: Findings) -> None:
    phases = DEV / "02_PHASES"
    for name in PHASE_DIRS:
        readme = phases / name / "README.md"
        if not readme.exists():
            findings.err(f"Missing phase README: {readme.relative_to(ROOT)}")


def check_templates(findings: Findings) -> None:
    for name in (
        "SPRINT_TEMPLATE.md",
        "TASK_TEMPLATE.md",
        "COMPLETION_REPORT_TEMPLATE.md",
    ):
        path = DEV / "02_PHASES" / name
        if not path.exists():
            findings.err(f"Missing template: {path.relative_to(ROOT)}")

    for sprint_md in (DEV / "02_PHASES").rglob("SPRINT.md"):
        text = sprint_md.read_text(encoding="utf-8")
        for section in SPRINT_REQUIRED:
            if section not in text:
                findings.err(
                    f"{sprint_md.relative_to(ROOT)} missing section {section}"
                )

    for task_md in (DEV / "02_PHASES").rglob("TASK-*.md"):
        text = task_md.read_text(encoding="utf-8")
        for section in TASK_REQUIRED:
            if section not in text:
                findings.err(f"{task_md.relative_to(ROOT)} missing section {section}")

    for report in (DEV / "02_PHASES").rglob("COMPLETION_REPORT.md"):
        text = report.read_text(encoding="utf-8")
        for section in COMPLETION_REQUIRED:
            if section not in text:
                findings.err(f"{report.relative_to(ROOT)} missing section {section}")


def check_workflow(findings: Findings) -> None:
    for path in WORKFLOW_READS:
        if not path.exists():
            findings.err(f"Workflow path missing: {path.relative_to(ROOT)}")

    e2e = DEV / "07_CURSOR" / "E2E_WORKFLOW_TEST.md"
    if not e2e.exists():
        findings.err("Missing Cursor E2E test: development/07_CURSOR/E2E_WORKFLOW_TEST.md")
    else:
        text = e2e.read_text(encoding="utf-8")
        if "## Result" not in text:
            findings.err("E2E_WORKFLOW_TEST.md missing ## Result section")


def _extract_field(table_text: str, field: str) -> str | None:
    match = re.search(
        rf"\|\s*{re.escape(field)}\s*\|\s*(.+?)\s*\|",
        table_text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return re.sub(r"\*+", "", match.group(1)).strip()


def check_status_sync(findings: Findings) -> None:
    status = (DEV / "00_MASTER" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    next_master = (DEV / "00_MASTER" / "NEXT_TASK.md").read_text(encoding="utf-8")
    next_status_path = DEV / "10_STATUS" / "NEXT_TASK.md"
    if not next_status_path.exists():
        findings.err("Missing development/10_STATUS/NEXT_TASK.md")
        next_status = ""
    else:
        next_status = next_status_path.read_text(encoding="utf-8")
    changelog = (DEV / "00_MASTER" / "CHANGELOG.md").read_text(encoding="utf-8")
    current = (DEV / "10_STATUS" / "CURRENT.md").read_text(encoding="utf-8")

    if "TIOS Bootstrap" not in changelog and "Sprint-000" not in changelog:
        findings.err("CHANGELOG.md missing TIOS Bootstrap / Sprint-000 history")
    if "Active coding task" not in next_master:
        findings.err("00_MASTER/NEXT_TASK.md missing Active coding task field")
    if next_status and "Active coding task" not in next_status:
        findings.err("10_STATUS/NEXT_TASK.md missing Active coding task field")

    active_master = _extract_field(next_master, "Active coding task")
    active_status = _extract_field(next_status, "Active coding task") if next_status else None
    if (
        active_master is not None
        and active_status is not None
        and active_master.lower() != active_status.lower()
    ):
        findings.err(
            "00_MASTER/NEXT_TASK.md and 10_STATUS/NEXT_TASK.md Active coding task mismatch"
        )

    if active_master is None:
        findings.err("Could not parse Active coding task from 00_MASTER/NEXT_TASK.md")
    elif active_master.lower() == "none":
        findings.warn("Active coding task is none")

    if "Signal Engine" not in status or "Signal Engine" not in next_master:
        findings.err("PROJECT_STATUS and NEXT_TASK must both mention Signal Engine")

    sprint_line = _extract_field(status, "Current sprint") or ""
    if "complete" in sprint_line.lower() and active_master and active_master.lower() != "none":
        # Planning-complete sprints may hand off to the next implementation task.
        if "planning" in sprint_line.lower():
            pass
        elif "bootstrap" in sprint_line.lower():
            findings.err(
                "Current sprint is complete bootstrap but NEXT_TASK still has an active task"
            )

    if active_master and active_master.lower() != "none":
        if active_master not in current and active_master.replace("SIG-", "") not in current:
            if active_master not in current:
                findings.warn(
                    f"10_STATUS/CURRENT.md does not mention active task {active_master}"
                )


def check_ci_match(findings: Findings) -> None:
    gates = (DEV / "05_VALIDATION" / "GATES.md").read_text(encoding="utf-8")
    for filename, needles in CI_REQUIRED_FILES.items():
        path = WORKFLOWS / filename
        if not path.exists():
            findings.err(f"Missing CI workflow: .github/workflows/{filename}")
            continue
        if filename not in gates and filename.replace(".yml", "") not in gates:
            findings.err(f"GATES.md does not reference CI workflow {filename}")
        body = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in body:
                findings.err(
                    f".github/workflows/{filename} missing expected content: {needle}"
                )

    if "88" not in gates:
        findings.err("GATES.md must document coverage fail-under 88")
    if "validate_architecture.py" not in gates:
        findings.err("GATES.md must document validate_architecture.py")
    if "validate_dependencies.py" not in gates:
        findings.err("GATES.md must document validate_dependencies.py")
    if "validate_tios.py" not in gates:
        findings.err("GATES.md must document validate_tios.py")


def check_master_files(findings: Findings) -> None:
    required = [
        "MASTER_ROADMAP.md",
        "PROJECT_STATUS.md",
        "PROJECT_VISION.md",
        "PHASE_INDEX.md",
        "TASK_INDEX.md",
        "CHANGELOG.md",
        "TECHNICAL_DEBT.md",
        "RELEASE_PLAN.md",
        "NEXT_TASK.md",
    ]
    for name in required:
        path = DEV / "00_MASTER" / name
        if not path.exists():
            findings.err(f"Missing master doc: {path.relative_to(ROOT)}")


def check_outdated_claims(findings: Findings) -> None:
    roadmap = (DEV / "00_MASTER" / "MASTER_ROADMAP.md").read_text(encoding="utf-8")
    # Broker must remain disabled language somewhere in master set
    status = (DEV / "00_MASTER" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    if "disabled" not in status.lower():
        findings.err("PROJECT_STATUS.md must state broker automation disabled")
    if "V1.0" not in roadmap or "Signal Engine" not in roadmap:
        findings.err("MASTER_ROADMAP.md missing V1.0 Signal Engine placeholder")

    readiness = DEV / "02_PHASES" / "phase_signal" / "SIGNAL_ENGINE_V1_READINESS.md"
    v1_accepted = readiness.exists() and "accepted" in readiness.read_text(encoding="utf-8").lower()

    # Premature "Complete" without readiness checklist remains forbidden.
    if re.search(r"\|\s*V1\.0\s*\|\s*Signal Engine\s*\|\s*Complete\b", roadmap, re.I):
        if not v1_accepted:
            findings.err("MASTER_ROADMAP incorrectly marks Signal Engine V1.0 complete")
    if re.search(r"Signal Engine V1\.0 implementation\s*\|\s*100%", status, re.I):
        if not v1_accepted:
            findings.err("PROJECT_STATUS incorrectly marks Signal Engine implementation 100%")


def run_all() -> int:
    findings = Findings()
    check_master_files(findings)
    check_phases(findings)
    check_templates(findings)
    check_links(findings)
    check_workflow(findings)
    check_status_sync(findings)
    check_ci_match(findings)
    check_outdated_claims(findings)

    for warning in findings.warnings:
        print(f"WARN: {warning}")
    for error in findings.errors:
        print(f"ERROR: {error}")

    if findings.errors:
        print(f"\nTIOS validation FAILED: {len(findings.errors)} error(s)")
        return 1
    print(
        f"TIOS validation PASSED ({len(findings.warnings)} warning(s), "
        f"0 errors)"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    raise SystemExit(run_all())


if __name__ == "__main__":
    main()
