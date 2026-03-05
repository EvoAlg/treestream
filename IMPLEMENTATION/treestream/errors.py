from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TreeStreamError(Exception):
    code: str
    operation: str
    message: str
    path: str | None = None

    def __str__(self) -> str:
        if self.path is None:
            return f"{self.code} {self.operation}: {self.message}"
        return f"{self.code} {self.operation} [{self.path}]: {self.message}"
