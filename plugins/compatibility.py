"""Semantic version compatibility checks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from plugins.dependency import PluginDependency
from plugins.exceptions import PluginCompatibilityError
from plugins.manifest import PluginManifest

_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


@dataclass(frozen=True)
class SemanticVersion:
    """Parsed semantic version."""

    major: int
    minor: int
    patch: int


@dataclass(frozen=True)
class CompatibilityResult:
    """Outcome of compatibility validation."""

    compatible: bool
    errors: tuple[str, ...] = ()


def parse_version(version: str) -> SemanticVersion:
    """Parse a semantic version string."""
    match = _VERSION_PATTERN.match(version.strip())
    if match is None:
        msg = f"Invalid semantic version: {version}"
        raise PluginCompatibilityError(msg)
    return SemanticVersion(
        major=int(match.group(1)),
        minor=int(match.group(2)),
        patch=int(match.group(3)),
    )


def compare_versions(left: str, right: str) -> int:
    """Compare two semantic versions. Returns -1, 0, or 1."""
    left_version = parse_version(left)
    right_version = parse_version(right)
    if left_version.major != right_version.major:
        return -1 if left_version.major < right_version.major else 1
    if left_version.minor != right_version.minor:
        return -1 if left_version.minor < right_version.minor else 1
    if left_version.patch != right_version.patch:
        return -1 if left_version.patch < right_version.patch else 1
    return 0


def satisfies(version: str, minimum: str, maximum: str | None = None) -> bool:
    """Return whether version satisfies minimum and optional maximum bounds."""
    if compare_versions(version, minimum) < 0:
        return False
    return maximum is None or compare_versions(version, maximum) <= 0


def check_api_compatibility(
    manifest: PluginManifest,
    platform_api_version: str,
) -> CompatibilityResult:
    """Validate manifest API version constraints."""
    errors: list[str] = []
    bounds = manifest.api_version_bounds
    if not satisfies(
        platform_api_version,
        bounds.minimum_api_version,
        bounds.maximum_api_version,
    ):
        if bounds.maximum_api_version is None:
            errors.append(
                "API version "
                f"{platform_api_version} is below minimum {bounds.minimum_api_version}",
            )
        else:
            errors.append(
                "API version "
                f"{platform_api_version} is outside range "
                f"{bounds.minimum_api_version} to {bounds.maximum_api_version}",
            )
    if not satisfies(manifest.api_version, bounds.minimum_api_version, bounds.maximum_api_version):
        errors.append(
            f"Plugin api_version {manifest.api_version} violates declared API bounds",
        )
    return CompatibilityResult(compatible=not errors, errors=tuple(errors))


def check_platform_compatibility(
    manifest: PluginManifest,
    platform_version: str,
) -> CompatibilityResult:
    """Validate manifest platform version constraints."""
    errors: list[str] = []
    constraint = manifest.platform_version
    if not satisfies(platform_version, constraint.minimum, constraint.maximum):
        if constraint.maximum is None:
            errors.append(
                f"Platform version {platform_version} is below minimum {constraint.minimum}",
            )
        else:
            errors.append(
                "Platform version "
                f"{platform_version} is outside range "
                f"{constraint.minimum} to {constraint.maximum}",
            )
    return CompatibilityResult(compatible=not errors, errors=tuple(errors))


def check_dependency_compatibility(
    dependency: PluginDependency,
    installed_version: str,
) -> CompatibilityResult:
    """Validate an installed plugin version against a dependency requirement."""
    if satisfies(installed_version, dependency.version_minimum, dependency.version_maximum):
        return CompatibilityResult(compatible=True)
    if dependency.version_maximum is None:
        message = (
            f"Dependency {dependency.plugin_id} version {installed_version} "
            f"is below minimum {dependency.version_minimum}"
        )
    else:
        message = (
            f"Dependency {dependency.plugin_id} version {installed_version} "
            f"is outside range {dependency.version_minimum} to {dependency.version_maximum}"
        )
    return CompatibilityResult(compatible=False, errors=(message,))


def check_manifest_compatibility(
    manifest: PluginManifest,
    *,
    platform_version: str,
    platform_api_version: str,
    installed_versions: dict[str, str],
) -> CompatibilityResult:
    """Validate manifest platform and dependency version compatibility."""
    errors: list[str] = []
    api_result = check_api_compatibility(manifest, platform_api_version)
    errors.extend(api_result.errors)
    platform_result = check_platform_compatibility(manifest, platform_version)
    errors.extend(platform_result.errors)
    for dependency in manifest.dependencies:
        installed = installed_versions.get(dependency.plugin_id)
        if installed is None:
            continue
        dependency_result = check_dependency_compatibility(dependency, installed)
        errors.extend(dependency_result.errors)
    return CompatibilityResult(compatible=not errors, errors=tuple(errors))
