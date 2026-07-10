"""Provider registry."""

from __future__ import annotations

from threading import RLock

from models.common import utc_now
from storage_providers.contracts.storage_provider import StorageProvider
from storage_providers.exceptions import ProviderNotFoundError, ProviderResolutionError
from storage_providers.registry.provider_record import ProviderRecord, ProviderState


class ProviderRegistry:
    """Thread-safe registry for storage providers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._providers: dict[str, StorageProvider] = {}
        self._records: dict[str, ProviderRecord] = {}
        self._scheme_index: dict[str, str] = {}

    def register(self, provider: StorageProvider) -> ProviderRecord:
        provider_id = provider.provider_id()
        metadata = provider.metadata()
        manifest = provider.manifest()
        now = utc_now()
        record = ProviderRecord(
            provider_id=provider_id,
            metadata=metadata,
            manifest=manifest,
            state=ProviderState.REGISTERED,
            registered_at=now,
            updated_at=now,
        )
        with self._lock:
            self._providers[provider_id] = provider
            self._records[provider_id] = record
            for scheme in manifest.supported_uri_schemes:
                normalized = scheme.strip().lower()
                self._scheme_index[normalized] = provider_id
        return record

    def lookup(self, provider_id: str) -> ProviderRecord:
        with self._lock:
            record = self._records.get(provider_id)
        if record is None:
            raise ProviderNotFoundError(provider_id)
        return record

    def get_provider(self, provider_id: str) -> StorageProvider:
        with self._lock:
            provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(provider_id)
        return provider

    def resolve(self, uri: str) -> StorageProvider:
        if "://" not in uri:
            msg = f"URI must include a scheme: {uri}"
            raise ProviderResolutionError(msg)
        scheme = uri.split("://", 1)[0].strip().lower()
        with self._lock:
            provider_id = self._scheme_index.get(scheme)
        if provider_id is None:
            msg = f"No storage provider registered for scheme: {scheme}"
            raise ProviderResolutionError(msg)
        return self.get_provider(provider_id)

    def list(self) -> tuple[ProviderRecord, ...]:
        with self._lock:
            return tuple(self._records[pid] for pid in sorted(self._records))

    def update_state(self, provider_id: str, state: ProviderState) -> ProviderRecord:
        with self._lock:
            record = self._records.get(provider_id)
            if record is None:
                raise ProviderNotFoundError(provider_id)
            updated = record.model_copy(update={"state": state, "updated_at": utc_now()})
            self._records[provider_id] = updated
            return updated

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
            self._records.clear()
            self._scheme_index.clear()
