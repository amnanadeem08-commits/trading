"""Contract tests for plugin framework."""

from __future__ import annotations

import pytest

from plugins import ApiVersionConstraint, PlatformVersionConstraint, PluginManifest
from plugins.sandbox import PermissionModel
from tests.plugin_helpers import make_capability, make_plugin


@pytest.mark.contract
def test_plugin_contract_fields() -> None:
    plugin = make_plugin()
    assert plugin.plugin_id == "test-plugin"
    assert plugin.name
    assert plugin.version
    assert plugin.author
    assert isinstance(plugin.description, str)
    assert isinstance(plugin.manifest, PluginManifest)


@pytest.mark.contract
def test_manifest_contract_fields() -> None:
    manifest = PluginManifest(
        api_version="1.0.0",
        api_version_bounds=ApiVersionConstraint(minimum_api_version="1.0.0"),
        platform_version=PlatformVersionConstraint(minimum="0.1.0", maximum="1.0.0"),
        dependencies=(),
        permissions=PermissionModel(permissions=("read",)),
        capabilities=(make_capability(),),
    )
    assert manifest.api_version == "1.0.0"
    assert manifest.platform_version.minimum == "0.1.0"
    assert manifest.permissions.permissions == ("read",)
    assert len(manifest.capabilities) == 1


@pytest.mark.contract
def test_capability_contract_fields() -> None:
    capability = make_capability()
    assert capability.capability_id == "cap-1"
    assert capability.type == "ingest"
    assert capability.version == "1.0.0"
    assert capability.metadata["scope"] == "test"
