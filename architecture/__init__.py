"""Architecture enforcement package."""

from architecture.dependency_rules import (
    FORBIDDEN_IMPORT_PAIRS,
    FOUNDATION_PACKAGES,
    IMPORT_LINTER_LAYERS,
    LEGACY_PATH_PREFIXES,
    PIPELINE_PACKAGES,
    PRODUCTION_PACKAGES,
    RULE_IDS,
)
from architecture.reporting import format_report, format_summary, format_violation
from architecture.validators import (
    ArchitectureReport,
    ArchitectureValidator,
    Violation,
    layer_index,
)

__all__ = [
    "FORBIDDEN_IMPORT_PAIRS",
    "FOUNDATION_PACKAGES",
    "IMPORT_LINTER_LAYERS",
    "LEGACY_PATH_PREFIXES",
    "PIPELINE_PACKAGES",
    "PRODUCTION_PACKAGES",
    "RULE_IDS",
    "ArchitectureReport",
    "ArchitectureValidator",
    "Violation",
    "format_report",
    "format_summary",
    "format_violation",
    "layer_index",
]
