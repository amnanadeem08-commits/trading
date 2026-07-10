"""Unit tests for plugin health."""

from __future__ import annotations

import pytest

from ml_engine_plugins import PluginHealthChecker, PluginHealthStatus, PluginLoader, PluginRegistry
from tests.ml_engine_plugins_helpers import StubMLPlugin


@pytest.mark.unit
def test_plugin_health_checker() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry=registry)
    loader.load(StubMLPlugin())
    checker = PluginHealthChecker(registry=registry)
    result = checker.check("stub-engine")
    assert result.status == PluginHealthStatus.HEALTHY
