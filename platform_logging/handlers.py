"""Structured log handler interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from threading import RLock


class LogHandler(ABC):
    """Interface for emitting formatted log records."""

    @abstractmethod
    def emit(self, formatted_record: str) -> None:
        """Emit a formatted log record."""


class ConsoleLogHandler(LogHandler):
    """Console log handler."""

    def __init__(self, *, stream: object | None = None) -> None:
        self._stream = stream

    def emit(self, formatted_record: str) -> None:
        if self._stream is not None and hasattr(self._stream, "write"):
            self._stream.write(formatted_record + "\n")
            if hasattr(self._stream, "flush"):
                self._stream.flush()
            return
        print(formatted_record)


class FileLogHandler(LogHandler):
    """Append-only file log handler."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._lock = RLock()
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def file_path(self) -> Path:
        return self._file_path

    def emit(self, formatted_record: str) -> None:
        with self._lock, self._file_path.open("a", encoding="utf-8") as handle:
            handle.write(formatted_record + "\n")
