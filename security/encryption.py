"""Encryption provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EncryptionProvider(ABC):
    """Interface for encrypting and decrypting data."""

    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes."""

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes."""
