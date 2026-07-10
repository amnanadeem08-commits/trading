"""Artifact checksum contracts."""

from __future__ import annotations

import re
from enum import StrEnum

from models.common import PlatformModel

_SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
_SHA512_PATTERN = re.compile(r"^[a-fA-F0-9]{128}$")
_MD5_PATTERN = re.compile(r"^[a-fA-F0-9]{32}$")


class ChecksumAlgorithm(StrEnum):
    """Supported checksum algorithms. Metadata only."""

    SHA256 = "sha256"
    SHA512 = "sha512"
    MD5 = "md5"


class ArtifactChecksum(PlatformModel):
    """Checksum metadata for artifact integrity verification."""

    algorithm: ChecksumAlgorithm
    value: str

    def validate_format(self) -> bool:
        """Validate checksum value format without hashing files."""
        if self.algorithm == ChecksumAlgorithm.SHA256:
            return _SHA256_PATTERN.match(self.value) is not None
        if self.algorithm == ChecksumAlgorithm.SHA512:
            return _SHA512_PATTERN.match(self.value) is not None
        return _MD5_PATTERN.match(self.value) is not None
