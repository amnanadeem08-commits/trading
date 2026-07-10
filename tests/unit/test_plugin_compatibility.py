"""Unit tests for plugin compatibility."""

from __future__ import annotations

import pytest

from plugins import (
    ApiVersionConstraint,
    PermissionModel,
    PlatformVersionConstraint,
    PluginCompatibilityError,
    PluginDependency,
    PluginManifest,
    check_api_compatibility,
    check_dependency_compatibility,
    check_manifest_compatibility,
    check_platform_compatibility,
    compare_versions,
    parse_version,
    satisfies,
)
from tests.plugin_helpers import make_plugin


@pytest.mark.unit
def test_parse_and_compare_versions() -> None:
    assert parse_version("1.2.3") == parse_version("1.2.3")
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1


@pytest.mark.unit
def test_satisfies_version_bounds() -> None:
    assert satisfies("1.0.0", "0.9.0", "1.1.0") is True
    assert satisfies("0.8.0", "0.9.0") is False
    assert satisfies("2.0.0", "0.9.0", "1.5.0") is False


@pytest.mark.unit
def test_invalid_version_raises() -> None:
    with pytest.raises(PluginCompatibilityError):
        parse_version("invalid")


@pytest.mark.unit
def test_platform_compatibility() -> None:
    plugin = make_plugin()
    result = check_platform_compatibility(plugin.manifest, "0.1.0")
    assert result.compatible is True


@pytest.mark.unit
def test_dependency_compatibility() -> None:
    dependency = PluginDependency(
        plugin_id="dep",
        version_minimum="1.0.0",
        version_maximum="2.0.0",
    )
    assert check_dependency_compatibility(dependency, "1.5.0").compatible is True
    assert check_dependency_compatibility(dependency, "0.5.0").compatible is False


@pytest.mark.unit
def test_api_compatibility() -> None:
    plugin = make_plugin()
    result = check_api_compatibility(plugin.manifest, "1.0.0")
    assert result.compatible is True


@pytest.mark.unit
def test_manifest_compatibility_with_dependencies() -> None:
    manifest = PluginManifest(
        api_version="1.0.0",
        api_version_bounds=ApiVersionConstraint(minimum_api_version="1.0.0"),
        platform_version=PlatformVersionConstraint(minimum="0.1.0"),
        dependencies=(PluginDependency(plugin_id="base", version_minimum="1.0.0"),),
        permissions=PermissionModel(),
        capabilities=(),
    )
    result = check_manifest_compatibility(
        manifest,
        platform_version="0.1.0",
        platform_api_version="1.0.0",
        installed_versions={"base": "1.0.0"},
    )
    assert result.compatible is True
