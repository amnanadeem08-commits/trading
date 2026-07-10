"""Architecture validation engine."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from architecture.dependency_rules import (
    CONNECTOR_BRIDGE_IMPORTS,
    CONNECTOR_FORBIDDEN_IMPORTS,
    CONNECTOR_IMPORT_FORBIDDEN_SOURCES,
    FORBIDDEN_IMPORT_PAIRS,
    GOVERNANCE_FORBIDDEN_IMPORTS,
    GOVERNANCE_PACKAGES,
    LEGACY_CONNECTOR_FILES,
    LEGACY_PATH_PREFIXES,
    MARKET_BRANCHING_IDENTIFIERS,
    MARKET_BRANCHING_STRINGS,
    MARKET_BRANCHING_SUBSTRINGS,
    ORCHESTRATION_PACKAGES,
    PIPELINE_PACKAGES,
    PRESENTATION_PACKAGES,
    RESEARCH_ALLOWED_IMPORTS,
    RESEARCH_FORBIDDEN_SOURCES,
    RESEARCH_PACKAGE,
    RULE_IDS,
    SERVICE_PACKAGES,
    PipelineLayer,
)


@dataclass(frozen=True)
class Violation:
    rule_id: str
    rule_name: str
    file_path: str
    detail: str
    line_number: int | None = None


@dataclass(frozen=True)
class ArchitectureReport:
    files_scanned: int
    violations: tuple[Violation, ...]


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative_path: str
    package: str | None
    source: str
    tree: ast.Module


class ArchitectureValidator:
    """Validates frozen architecture rules across the repository."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def validate_all(self) -> ArchitectureReport:
        source_files = self._load_source_files()
        violations: list[Violation] = []
        violations.extend(self._validate_dependency_direction(source_files))
        violations.extend(self._validate_forbidden_imports(source_files))
        violations.extend(self._validate_research_isolation(source_files))
        violations.extend(self._validate_service_boundaries(source_files))
        violations.extend(self._validate_orchestration_boundaries(source_files))
        violations.extend(self._validate_connector_boundaries(source_files))
        violations.extend(self._validate_layer_rules(source_files))
        violations.extend(self._validate_presentation_boundaries(source_files))
        return ArchitectureReport(
            files_scanned=len(source_files),
            violations=tuple(violations),
        )

    def _load_source_files(self) -> list[SourceFile]:
        files: list[SourceFile] = []
        for path in sorted(self._project_root.rglob("*.py")):
            relative = path.relative_to(self._project_root).as_posix()
            if self._is_excluded_path(relative):
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
            files.append(
                SourceFile(
                    path=path,
                    relative_path=relative,
                    package=self._package_for_path(relative),
                    source=source,
                    tree=tree,
                )
            )
        return files

    def _is_excluded_path(self, relative_path: str) -> bool:
        if relative_path.startswith("tests/"):
            return True
        if relative_path.startswith(".venv/") or "/.venv/" in relative_path:
            return True
        if relative_path.startswith(".mypy_cache/") or "/.mypy_cache/" in relative_path:
            return True
        if relative_path.startswith(".pytest_cache/") or "/.pytest_cache/" in relative_path:
            return True
        if relative_path.startswith(".ruff_cache/") or "/.ruff_cache/" in relative_path:
            return True
        for prefix in LEGACY_PATH_PREFIXES:
            if relative_path == prefix or relative_path.startswith(prefix):
                return True
        return False

    def _package_for_path(self, relative_path: str) -> str | None:
        if "/" not in relative_path:
            stem = relative_path.removesuffix(".py")
            if stem in PRESENTATION_PACKAGES:
                return stem
            return None
        return relative_path.split("/", maxsplit=1)[0]

    def _imported_roots(self, tree: ast.Module) -> set[str]:
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        return imports

    def _validate_dependency_direction(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package is None or package not in PIPELINE_PACKAGES:
                continue
            source_layer = PIPELINE_PACKAGES[package]
            imported = self._imported_roots(source_file.tree)
            for imported_root in imported:
                if imported_root not in PIPELINE_PACKAGES:
                    continue
                target_layer = PIPELINE_PACKAGES[imported_root]
                if package == "connectors" and imported_root in CONNECTOR_BRIDGE_IMPORTS:
                    continue
                if target_layer > source_layer:
                    violations.append(
                        Violation(
                            rule_id=RULE_IDS["dependency_direction"],
                            rule_name="dependency_direction",
                            file_path=source_file.relative_path,
                            detail=(
                                f"{package} (layer {source_layer.name}) must not import "
                                f"{imported_root} (layer {target_layer.name})"
                            ),
                        )
                    )
        return violations

    def _validate_forbidden_imports(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package is None:
                continue
            forbidden_targets = FORBIDDEN_IMPORT_PAIRS.get(package)
            if forbidden_targets is None:
                continue
            imported = self._imported_roots(source_file.tree)
            blocked = sorted(imported.intersection(forbidden_targets))
            for target in blocked:
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["forbidden_import"],
                        rule_name="forbidden_import",
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import {target}",
                    )
                )
        return violations

    def _validate_research_isolation(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package is None:
                continue
            if package == RESEARCH_PACKAGE:
                imported = self._imported_roots(source_file.tree)
                blocked = sorted(imported - RESEARCH_ALLOWED_IMPORTS)
                for target in blocked:
                    violations.append(
                        Violation(
                            rule_id=RULE_IDS["research_isolation"],
                            rule_name="research_isolation",
                            file_path=source_file.relative_path,
                            detail=f"research must not import {target}",
                        )
                    )
                continue
            if package not in RESEARCH_FORBIDDEN_SOURCES:
                continue
            if RESEARCH_PACKAGE in self._imported_roots(source_file.tree):
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["research_isolation"],
                        rule_name="research_isolation",
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import research",
                    )
                )
        return violations

    def _validate_service_boundaries(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package not in SERVICE_PACKAGES:
                continue
            if "connectors" in self._imported_roots(source_file.tree):
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["service_boundary"],
                        rule_name="service_boundary",
                        file_path=source_file.relative_path,
                        detail="services must not import connectors directly",
                    )
                )
            violations.extend(self._market_branching_violations(source_file, "service_boundary"))
        return violations

    def _validate_orchestration_boundaries(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package not in ORCHESTRATION_PACKAGES:
                continue
            rule_name = f"{package}_boundary"
            rule_id = RULE_IDS.get(rule_name, RULE_IDS["pipeline_boundary"])
            forbidden = FORBIDDEN_IMPORT_PAIRS.get(package, frozenset())
            imported = self._imported_roots(source_file.tree)
            blocked = sorted(imported.intersection(forbidden))
            for target in blocked:
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import {target}",
                    )
                )
            violations.extend(self._market_branching_violations(source_file, rule_name))
        return violations

    def _validate_connector_boundaries(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package is None:
                continue
            if (
                package in CONNECTOR_IMPORT_FORBIDDEN_SOURCES
                and "connectors" in self._imported_roots(source_file.tree)
            ):
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["connector_boundary"],
                        rule_name="connector_boundary",
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import connectors",
                    )
                )
            if package == "connectors":
                if source_file.relative_path in LEGACY_CONNECTOR_FILES:
                    continue
                imported = self._imported_roots(source_file.tree)
                blocked = sorted(imported.intersection(CONNECTOR_FORBIDDEN_IMPORTS))
                for target in blocked:
                    violations.append(
                        Violation(
                            rule_id=RULE_IDS["connector_boundary"],
                            rule_name="connector_boundary",
                            file_path=source_file.relative_path,
                            detail=f"connectors must not import {target}",
                        )
                    )
                if source_file.relative_path.endswith("connectors/market_registry.py"):
                    violations.extend(self._registry_market_branching_violations(source_file))
        return violations

    def _validate_layer_rules(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package not in GOVERNANCE_PACKAGES:
                continue
            imported = self._imported_roots(source_file.tree)
            blocked = sorted(imported.intersection(GOVERNANCE_FORBIDDEN_IMPORTS))
            for target in blocked:
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["layer_rule"],
                        rule_name="layer_rule",
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import {target}",
                    )
                )
        return violations

    def _validate_presentation_boundaries(self, source_files: list[SourceFile]) -> list[Violation]:
        violations: list[Violation] = []
        for source_file in source_files:
            package = source_file.package
            if package not in PRESENTATION_PACKAGES:
                continue
            forbidden = FORBIDDEN_IMPORT_PAIRS.get(package, frozenset())
            imported = self._imported_roots(source_file.tree)
            blocked = sorted(imported.intersection(forbidden))
            for target in blocked:
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["presentation_boundary"],
                        rule_name="presentation_boundary",
                        file_path=source_file.relative_path,
                        detail=f"{package} must not import {target}",
                    )
                )
        return violations

    def _market_branching_violations(
        self,
        source_file: SourceFile,
        rule_name: str,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.If):
                continue
            if self._if_test_has_market_branching(node.test):
                violations.append(
                    Violation(
                        rule_id=RULE_IDS["service_boundary"],
                        rule_name=rule_name,
                        file_path=source_file.relative_path,
                        detail="market-specific branching is forbidden",
                        line_number=node.lineno,
                    )
                )
        return violations

    def _registry_market_branching_violations(self, source_file: SourceFile) -> list[Violation]:
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.If):
                continue
            for child in ast.walk(node.test):
                if isinstance(child, ast.Compare):
                    for comparator in child.comparators:
                        if self._constant_has_market_branching(comparator):
                            violations.append(
                                Violation(
                                    rule_id=RULE_IDS["connector_boundary"],
                                    rule_name="connector_boundary",
                                    file_path=source_file.relative_path,
                                    detail="registry must not contain market-specific branching",
                                    line_number=node.lineno,
                                )
                            )
                if self._constant_has_market_branching(child):
                    violations.append(
                        Violation(
                            rule_id=RULE_IDS["connector_boundary"],
                            rule_name="connector_boundary",
                            file_path=source_file.relative_path,
                            detail="registry must not contain market-specific branching",
                            line_number=node.lineno,
                        )
                    )
        return violations

    def _if_test_has_market_branching(self, node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in MARKET_BRANCHING_IDENTIFIERS:
                return True
            if self._constant_has_market_branching(child):
                return True
        return False

    def _constant_has_market_branching(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            return False
        value = node.value.lower()
        if value in MARKET_BRANCHING_STRINGS:
            return True
        return any(substring in value for substring in MARKET_BRANCHING_SUBSTRINGS)


def layer_index(package: str) -> PipelineLayer | None:
    return PIPELINE_PACKAGES.get(package)
