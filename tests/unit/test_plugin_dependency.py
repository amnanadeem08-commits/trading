"""Unit tests for plugin dependency graph."""

from __future__ import annotations

import pytest

from plugins import build_dependency_graph, detect_cycle, topological_order
from plugins.dependency import PluginDependency
from plugins.exceptions import CircularPluginDependencyError
from plugins.validation import validate_plugin_set
from tests.plugin_helpers import make_plugin


@pytest.mark.unit
def test_topological_order() -> None:
    graph = build_dependency_graph(
        ("a", "b", "c"),
        {"a": (), "b": ("a",), "c": ("b",)},
    )
    assert topological_order(graph) == ("a", "b", "c")


@pytest.mark.unit
def test_detect_cycle() -> None:
    graph = build_dependency_graph(
        ("a", "b", "c"),
        {"a": ("c",), "b": ("a",), "c": ("b",)},
    )
    cycle = detect_cycle(graph)
    assert cycle is not None
    assert "a" in cycle


@pytest.mark.unit
def test_validate_plugin_cycle_raises() -> None:
    plugins = (
        make_plugin(
            plugin_id="a", dependencies=(PluginDependency(plugin_id="c", version_minimum="1.0.0"),)
        ),
        make_plugin(
            plugin_id="b", dependencies=(PluginDependency(plugin_id="a", version_minimum="1.0.0"),)
        ),
        make_plugin(
            plugin_id="c", dependencies=(PluginDependency(plugin_id="b", version_minimum="1.0.0"),)
        ),
    )
    with pytest.raises(CircularPluginDependencyError):
        validate_plugin_set(plugins, platform_version="0.1.0", platform_api_version="1.0.0")
