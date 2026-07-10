"""Artifact registry."""

from __future__ import annotations

from threading import RLock

from artifact_management.exceptions import ArtifactNotFoundError
from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference
from artifact_management.registry.artifact_record import ArtifactRecord, ArtifactState
from models.common import utc_now


class ArtifactRegistry:
    """Thread-safe registry for artifact metadata."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, ArtifactRecord] = {}

    def register(
        self,
        *,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
        reference: ArtifactReference,
    ) -> ArtifactRecord:
        now = utc_now()
        record = ArtifactRecord(
            artifact_id=metadata.artifact_id,
            metadata=metadata,
            manifest=manifest,
            reference=reference,
            state=ArtifactState.REGISTERED,
            registered_at=now,
            updated_at=now,
        )
        with self._lock:
            self._records[metadata.artifact_id] = record
        return record

    def lookup(self, artifact_id: str) -> ArtifactRecord:
        with self._lock:
            record = self._records.get(artifact_id)
        if record is None:
            raise ArtifactNotFoundError(artifact_id)
        return record

    def list(self) -> tuple[ArtifactRecord, ...]:
        with self._lock:
            return tuple(self._records[aid] for aid in sorted(self._records))

    def update_state(self, artifact_id: str, state: ArtifactState) -> ArtifactRecord:
        with self._lock:
            record = self._records.get(artifact_id)
            if record is None:
                raise ArtifactNotFoundError(artifact_id)
            updated = record.model_copy(update={"state": state, "updated_at": utc_now()})
            self._records[artifact_id] = updated
            return updated

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
