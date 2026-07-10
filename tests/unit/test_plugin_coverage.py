"""Additional plugin coverage tests."""

from __future__ import annotations

import pytest

from pipeline import reset_pipeline_registry
from plugins import (
    DefaultPluginSandbox,
    FilesystemAccessPolicy,
    NetworkAccessPolicy,
    PermissionModel,
    PluginError,
    PluginNotFoundError,
    PluginRegistrationError,
    PluginStateError,
    ResourceLimits,
    plugin,
    plugin_metadata,
    reset_plugin_registry,
)
from plugins.sandbox import PluginSandbox
from services import reset_application_context
from tests.plugin_helpers import TestPlugin


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()
    yield
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()


@pytest.mark.unit
def test_plugin_exceptions_expose_codes() -> None:
    assert PluginError("x").code == "plugin_error"
    assert PluginNotFoundError("x").code == "plugin_not_found"
    assert PluginRegistrationError("dup").code == "plugin_registration_error"
    assert PluginStateError("x", "loaded", "enable").code == "plugin_state_error"


@plugin(plugin_id="decorated", auto_register=False)
class _DecoratedPlugin(TestPlugin):
    def plugin_id(self) -> str:
        return "decorated"


@pytest.mark.unit
def test_plugin_metadata_decorator() -> None:
    metadata = plugin_metadata(_DecoratedPlugin)
    assert metadata["plugin_id"] == "decorated"
    assert metadata["auto_register"] is False


@pytest.mark.unit
def test_default_sandbox_policies() -> None:
    sandbox = DefaultPluginSandbox(permissions=PermissionModel(permissions=("read",)))
    assert sandbox.permissions.permissions == ("read",)
    assert isinstance(sandbox.resource_limits, ResourceLimits)
    assert isinstance(sandbox.filesystem_policy, FilesystemAccessPolicy)
    assert isinstance(sandbox.network_policy, NetworkAccessPolicy)


@pytest.mark.unit
def test_base_plugin_to_definition() -> None:
    definition = TestPlugin().to_definition()
    assert definition.plugin_id == "test-plugin"
    assert definition.manifest.api_version == "1.0.0"


@pytest.mark.unit
def test_sandbox_is_abstract() -> None:
    assert issubclass(PluginSandbox, object)
    with pytest.raises(TypeError):
        PluginSandbox()  # type: ignore[abstract]
