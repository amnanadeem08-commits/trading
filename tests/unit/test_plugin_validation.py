"""Unit tests for plugin validation."""

from __future__ import annotations

import pytest

from plugins import PermissionConflictError, validate_manifest_schema, validate_plugin_set
from plugins.dependency import PluginDependency
from tests.plugin_helpers import make_capability, make_plugin


@pytest.mark.unit
def test_validate_duplicate_plugins() -> None:
    plugins = (
        make_plugin(plugin_id="same"),
        make_plugin(plugin_id="same"),
    )
    result = validate_plugin_set(plugins, platform_version="0.1.0", platform_api_version="1.0.0")
    assert result.valid is False
    assert any("Duplicate plugin" in error for error in result.errors)


@pytest.mark.unit
def test_validate_duplicate_capabilities() -> None:
    capability = make_capability(capability_id="dup")
    plugins = (
        make_plugin(plugin_id="a", capabilities=(capability,)),
        make_plugin(plugin_id="b", capabilities=(capability,)),
    )
    result = validate_plugin_set(plugins, platform_version="0.1.0", platform_api_version="1.0.0")
    assert result.valid is False
    assert any("Duplicate capability" in error for error in result.errors)


@pytest.mark.unit
def test_validate_missing_dependency() -> None:
    plugin = make_plugin(
        dependencies=(PluginDependency(plugin_id="missing", version_minimum="1.0.0"),),
    )
    result = validate_plugin_set((plugin,), platform_version="0.1.0", platform_api_version="1.0.0")
    assert result.valid is False
    assert any("Missing dependency" in error for error in result.errors)


@pytest.mark.unit
def test_validate_self_dependency() -> None:
    plugin = make_plugin(
        dependencies=(PluginDependency(plugin_id="test-plugin", version_minimum="1.0.0"),),
    )
    result = validate_plugin_set((plugin,), platform_version="0.1.0", platform_api_version="1.0.0")
    assert result.valid is False
    assert any("depends on itself" in error for error in result.errors)


@pytest.mark.unit
def test_validate_permission_conflicts() -> None:
    plugins = (
        make_plugin(plugin_id="a", permissions=("admin",)),
        make_plugin(plugin_id="b", permissions=("admin",)),
    )
    with pytest.raises(PermissionConflictError):
        validate_plugin_set(plugins, platform_version="0.1.0", platform_api_version="1.0.0")


@pytest.mark.unit
def test_validate_manifest_schema_duplicate_capabilities() -> None:
    capability = make_capability(capability_id="dup")
    plugin = make_plugin(capabilities=(capability, capability))
    result = validate_manifest_schema(plugin.manifest)
    assert result.valid is False
