"""Service graph validation utilities."""

from __future__ import annotations

from dataclasses import dataclass

from services.exceptions import CircularDependencyError, ServiceValidationError
from services.service import BaseService


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of service graph validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    startup_order: tuple[str, ...] = ()
    shutdown_order: tuple[str, ...] = ()


def _build_dependency_graph(services: dict[str, BaseService]) -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for name, service in services.items():
        dependencies = tuple(dep for dep in service.dependencies() if dep in services)
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
        msg = "Failed to compute dependency order"
        raise ServiceValidationError(msg)
    return tuple(order)


def validate_services(services: dict[str, BaseService]) -> ValidationResult:
    """Validate registered services and compute lifecycle ordering."""
    errors: list[str] = []
    for name, service in services.items():
        if service.name() != name:
            errors.append(f"Service name mismatch: key={name}, name()={service.name()}")
        for dependency in service.dependencies():
            if dependency == name:
                errors.append(f"Service depends on itself: {name}")
            elif dependency not in services:
                errors.append(f"Missing dependency '{dependency}' required by '{name}'")

    if errors:
        return ValidationResult(valid=False, errors=tuple(errors))

    graph = _build_dependency_graph(services)
    cycle = _detect_cycle(graph)
    if cycle is not None:
        raise CircularDependencyError(cycle)

    startup_order = _topological_order(graph)
    shutdown_order = tuple(reversed(startup_order))
    return ValidationResult(
        valid=True,
        startup_order=startup_order,
        shutdown_order=shutdown_order,
    )
