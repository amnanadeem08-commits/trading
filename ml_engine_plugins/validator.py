"""Plugin validator."""

from __future__ import annotations

from ml_engine_plugins.exceptions import PluginValidationError
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_manifest import PluginManifest
from ml_engine_plugins.validation_result import PluginValidationResult


class PluginValidator:
    """Validates ML engine plugin manifests and metadata."""

    def validate_manifest(self, manifest: PluginManifest) -> PluginValidationResult:
        errors: list[str] = []
        if not manifest.plugin_id.strip():
            errors.append("plugin_id must not be empty")
        if not manifest.name.strip():
            errors.append("name must not be empty")
        if not manifest.version.strip():
            errors.append("version must not be empty")
        if errors:
            return PluginValidationResult.failure(*errors, plugin_id=manifest.plugin_id or None)
        return PluginValidationResult.success(plugin_id=manifest.plugin_id)

    def validate_plugin(self, plugin: MLPlugin) -> PluginValidationResult:
        manifest_result = self.validate_manifest(plugin.manifest())
        if not manifest_result.valid:
            return manifest_result
        metadata = plugin.metadata()
        if metadata.plugin_id != plugin.plugin_id():
            return PluginValidationResult.failure(
                "metadata.plugin_id must match plugin.plugin_id()",
                plugin_id=plugin.plugin_id(),
            )
        if not plugin.capabilities():
            return PluginValidationResult.failure(
                "plugin must declare at least one capability",
                plugin_id=plugin.plugin_id(),
            )
        return PluginValidationResult.success(plugin_id=plugin.plugin_id())

    def ensure_valid(self, result: PluginValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise PluginValidationError(message)
