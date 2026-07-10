"""Human-readable architecture validation reports."""

from __future__ import annotations

from architecture.validators import ArchitectureReport, Violation


def format_violation(violation: Violation) -> str:
    location = violation.file_path
    if violation.line_number is not None:
        location = f"{location}:{violation.line_number}"
    return f"[{violation.rule_id}] {violation.rule_name} — {location} — {violation.detail}"


def format_report(report: ArchitectureReport) -> str:
    lines = [
        "Architecture Validation Report",
        "==============================",
        f"Files scanned: {report.files_scanned}",
        f"Violations: {len(report.violations)}",
        "",
    ]
    if not report.violations:
        lines.append("PASS — no architecture violations detected.")
        return "\n".join(lines)

    lines.append("FAIL — architecture violations detected:")
    lines.append("")
    for violation in report.violations:
        lines.append(f"  - {format_violation(violation)}")
    return "\n".join(lines)


def format_summary(report: ArchitectureReport) -> str:
    if not report.violations:
        return "PASS"
    counts: dict[str, int] = {}
    for violation in report.violations:
        counts[violation.rule_name] = counts.get(violation.rule_name, 0) + 1
    parts = [f"{name}={count}" for name, count in sorted(counts.items())]
    return f"FAIL ({', '.join(parts)})"
