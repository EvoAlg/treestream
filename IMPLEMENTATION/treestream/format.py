from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath

from .errors import TreeStreamError

HEADER_LINES = (
    b"TREESTREAM 1\n",
    b"SPEC_VERSION: v0.1.9\n",
    b"ENCODING: UTF-8\n",
    b"NEWLINES: LF\n",
    b"RECORDS: FILE\n",
    b"END_HEADER\n",
)

INVALID_COMPONENT_CHARS = frozenset('<>"|?*')
RESERVED_DEVICE_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(10)] + [f"LPT{i}" for i in range(10)]
)


def assert_windows(operation: str) -> None:
    if os.name != "nt":
        raise TreeStreamError("E5", operation, "Windows-only implementation")


def canonical_relative_path(root_abs: Path, file_abs: Path) -> str:
    return file_abs.relative_to(root_abs).as_posix()


def parse_line_strict_lf(handle, operation: str, eof_code: str = "E6") -> bytes:
    line = handle.readline()
    if line == b"":
        raise TreeStreamError(eof_code, operation, "unexpected EOF while reading structural line")
    if not line.endswith(b"\n"):
        raise TreeStreamError(eof_code, operation, "structural line missing LF terminator")
    if line.endswith(b"\r\n"):
        raise TreeStreamError("E6", operation, "structural lines must use LF only")
    return line[:-1]


def parse_line_normalized_lf(handle, operation: str, eof_code: str = "E6") -> bytes:
    line = handle.readline()
    if line == b"":
        raise TreeStreamError(eof_code, operation, "unexpected EOF while reading structural line")
    if not line.endswith(b"\n"):
        raise TreeStreamError(eof_code, operation, "structural line missing LF terminator")

    if line.endswith(b"\r\n"):
        value = line[:-2]
    else:
        value = line[:-1]

    if b"\r" in value:
        raise TreeStreamError("E6", operation, "standalone CR is invalid in structural input")

    return value


def parse_content_bytes_field(raw_value: bytes, operation: str) -> int:
    if raw_value == b"0":
        return 0
    if not raw_value or raw_value.startswith(b"0") or not raw_value.isdigit():
        raise TreeStreamError("E6", operation, "invalid CONTENT_BYTES format")
    return int(raw_value.decode("ascii"))


def validate_serialized_path(path_value: str, target_abs: Path, operation: str) -> Path:
    if path_value == "":
        raise TreeStreamError("E9", operation, "PATH cannot be empty")

    raw_components = path_value.split("/")
    for component in raw_components:
        if component == "":
            raise TreeStreamError("E9", operation, "PATH has empty component", path=path_value)
        if component in (".", ".."):
            raise TreeStreamError("E9", operation, "PATH contains traversal segment", path=path_value)

    if "\\" in path_value:
        raise TreeStreamError("E9", operation, "PATH must use forward slashes", path=path_value)
    if ":" in path_value:
        raise TreeStreamError("E9", operation, "PATH must not contain ':'", path=path_value)

    p = PureWindowsPath(path_value)
    parts = p.parts
    if not parts:
        raise TreeStreamError("E9", operation, "PATH cannot be empty", path=path_value)

    for component in raw_components:
        if component.endswith(" ") or component.endswith("."):
            raise TreeStreamError("E9", operation, "PATH component ends with space/dot", path=path_value)
        if any(ch in INVALID_COMPONENT_CHARS for ch in component):
            raise TreeStreamError("E9", operation, "PATH component has invalid character", path=path_value)

        dev_name = component.split(".", 1)[0].upper()
        if dev_name in RESERVED_DEVICE_NAMES:
            raise TreeStreamError("E9", operation, "PATH component is reserved device name", path=path_value)

    candidate = (target_abs / Path(*parts)).resolve(strict=False)
    try:
        candidate.relative_to(target_abs)
    except ValueError as exc:
        raise TreeStreamError("E9", operation, "PATH escapes target directory", path=path_value) from exc

    return candidate
