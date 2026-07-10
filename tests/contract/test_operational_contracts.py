"""Contract tests for operational scaffolds."""

from __future__ import annotations

import inspect

import pytest

from health.observability import ObservableService
from metrics.types import Counter, Gauge, Histogram, Timer
from notifications.providers import EmailProvider, SlackProvider, WebhookProvider
from security.api_keys import ApiKeyProvider
from security.audit_hook import SecurityAuditHook
from security.credentials import CredentialProvider
from security.encryption import EncryptionProvider
from security.hash_provider import HashProvider
from security.secrets import SecretProvider
from security.tokens import TokenProvider


@pytest.mark.contract
def test_observable_service_declares_required_methods() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ObservableService, predicate=inspect.isfunction)
    }
    assert {"name", "version", "status", "health", "metrics"}.issubset(methods)


@pytest.mark.contract
def test_metric_interfaces_are_abstract() -> None:
    for metric_type in (Counter, Gauge, Histogram, Timer):
        assert inspect.isabstract(metric_type)


@pytest.mark.contract
def test_security_providers_are_abstract() -> None:
    for provider_type in (
        CredentialProvider,
        SecretProvider,
        EncryptionProvider,
        HashProvider,
        TokenProvider,
        ApiKeyProvider,
        SecurityAuditHook,
    ):
        assert inspect.isabstract(provider_type)


@pytest.mark.contract
def test_notification_providers_are_abstract() -> None:
    for provider_type in (EmailProvider, SlackProvider, WebhookProvider):
        assert inspect.isabstract(provider_type)
