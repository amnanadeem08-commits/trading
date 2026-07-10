"""Pipeline stage graph validation."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.exceptions import CircularStageDependencyError, PipelineValidationError
from pipeline.stage import PipelineStage


@dataclass(frozen=True)
class PipelineValidationResult:
    """Outcome of pipeline stage graph validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    execution_order: tuple[str, ...] = ()
    rollback_order: tuple[str, ...] = ()


def _build_dependency_graph(stages: dict[str, PipelineStage]) -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for name, stage in stages.items():
        dependencies = tuple(dep for dep in stage.dependencies() if dep in stages)
        graph[name] = dependencies
    return graph


def _detect_cycle(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...] | None:
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> tuple[str, ...] | None:
        if node in stack:
            cycle_start = path.index(node)
            return tuple([*path[cycle_start:], node])
        if node in visited:
            return None
        visited.add(node)
        stack.add(node)
        path.append(node)
        for dependency in graph.get(node, ()):
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        path.pop()
        stack.remove(node)
        return None

    for node in sorted(graph):
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None


def _topological_order(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    incoming: dict[str, int] = {name: len(dependencies) for name, dependencies in graph.items()}
    dependents: dict[str, list[str]] = {name: [] for name in graph}
    for name, dependencies in graph.items():
        for dependency in dependencies:
            dependents[dependency].append(name)

    queue = [name for name, count in sorted(incoming.items()) if count == 0]
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for dependent in sorted(dependents[current]):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(graph):
        msg = "Failed to compute stage execution order"
        raise PipelineValidationError(msg)
    return tuple(order)


def validate_pipeline_stages(stages: dict[str, PipelineStage]) -> PipelineValidationResult:
    """Validate pipeline stages and compute execution ordering."""
    errors: list[str] = []
    names = list(stages.keys())
    if len(names) != len(set(names)):
        errors.append("Duplicate stage names detected")

    for name, stage in stages.items():
        if stage.name() != name:
            errors.append(f"Stage name mismatch: key={name}, name()={stage.name()}")
        for dependency in stage.dependencies():
            if dependency == name:
                errors.append(f"Stage depends on itself: {name}")
            elif dependency not in stages:
                errors.append(f"Missing dependency '{dependency}' required by '{name}'")

    if errors:
        return PipelineValidationResult(valid=False, errors=tuple(errors))

    graph = _build_dependency_graph(stages)
    cycle = _detect_cycle(graph)
    if cycle is not None:
        raise CircularStageDependencyError(cycle)

    execution_order = _topological_order(graph)
    rollback_order = tuple(reversed(execution_order))
    return PipelineValidationResult(
        valid=True,
        execution_order=execution_order,
        rollback_order=rollback_order,
    )
