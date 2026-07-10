"""Contract tests for platform service layer."""

from __future__ import annotations

import inspect

import pytest

from services import BaseService
from tests.services_fixtures import AlphaService, BetaService


@pytest.mark.contract
def test_base_service_contract_methods() -> None:
    required = {
        "name",
        "version",
        "start",
        "stop",
        "health",
        "status",
        "metrics",
        "dependencies",
        "ready",
    }
    assert required.issubset(set(dir(BaseService)))
    for method_name in required:
        assert getattr(BaseService, method_name) is not None


@pytest.mark.contract
@pytest.mark.parametrize("service_type", [AlphaService, BetaService])
def test_service_implementations_satisfy_contract(service_type: type[BaseService]) -> None:
    assert not inspect.isabstract(service_type)
    if service_type is BetaService:
        alpha = AlphaService()
        alpha.start()
        service = service_type(alpha)
    else:
        service = service_type()
    assert isinstance(service.name(), str)
    assert isinstance(service.version(), str)
    assert isinstance(service.dependencies(), tuple)
    assert isinstance(service.metrics(), dict)
    assert isinstance(service.ready(), bool)
    service.start()
    assert service.health() is not None
    assert service.status() is not None
    service.stop()
