"""Unit tests for plugin validation."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginValidationError, PluginValidator
from tests.ml_engine_plugins_helpers import StubMLPlugin


@pytest.mark.unit
def test_plugin_validator_accepts_stub() -> None:
    validator = PluginValidator()
    result = validator.validate_plugin(StubMLPlugin())
    assert result.valid is True


@pytest.mark.unit
def test_plugin_validator_rejects_empty_capabilities() -> None:
    validator = PluginValidator()

    class NoCapsPlugin(StubMLPlugin):
        def capabilities(self) -> tuple:
            return ()

    with pytest.raises(PluginValidationError):
        validator.ensure_valid(validator.validate_plugin(NoCapsPlugin()))
