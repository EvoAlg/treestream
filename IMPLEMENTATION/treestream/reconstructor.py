from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass
from pathlib import Path

from .errors import TreeStreamError
from .format import (
    assert_windows,
    encoded_content_length,
    parse_content_bytes_field,
    parse_line_normalized_lf,
    validate_serialized_path,
)
from .version import SPEC_VERSION


def _parse_header(handle) -> str:
    op = "reconstruction"
    line1 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if line1.startswith(b"TREESTREAM ") and line1 != b"TREESTREAM 1":
        raise TreeStreamError("E7", op, "unsupported TREESTREAM version")
    if line1 != b"TREESTREAM 1":
        raise TreeStreamError("E6", op, "invalid header structure: missing TREESTREAM line")

    line2 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not line2.startswith(b"SPEC_VERSION: "):
        raise TreeStreamError("E6", op, "invalid header structure: SPEC_VERSION line malformed")
    if line2 != f"SPEC_VERSION: {SPEC_VERSION}".encode("ascii"):
        raise TreeStreamError("E7", op, "unsupported SPEC_VERSION")

    line3 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not line3.startswith(b"ENCODING: "):
        raise TreeStreamError("E6", op, "invalid header structure: ENCODING line malformed")
    if line3 != b"ENCODING: UTF-8":
        raise TreeStreamError("E7", op, "unsupported ENCODING")

    line4 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not line4.startswith(b"NEWLINES: "):
        raise TreeStreamError("E6", op, "invalid header structure: NEWLINES line malformed")
    if line4 != b"NEWLINES: LF":
        raise TreeStreamError("E7", op, "unsupported NEWLINES value")

    line5 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not line5.startswith(b"RECORDS: "):
        raise TreeStreamError("E6", op, "invalid header structure: RECORDS line malformed")
    if line5 != b"RECORDS: FILE":
        raise TreeStreamError("E7", op, "unsupported RECORDS value")

    line6 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if line6 == b"END_HEADER":
        raise TreeStreamError("E7", op, "missing ROOT_NAME header")
    if not line6.startswith(b"ROOT_NAME: "):
        raise TreeStreamError("E7", op, "missing or malformed ROOT_NAME header")
    raw_root_name = line6[len(b"ROOT_NAME: ") :]
    if raw_root_name == b"":
        raise TreeStreamError("E7", op, "ROOT_NAME is empty")
    try:
        root_name = raw_root_name.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise TreeStreamError("E7", op, "ROOT_NAME is not valid UTF-8") from exc
    if "/" in root_name or "\\" in root_name or "\n" in root_name or "\r" in root_name:
        raise TreeStreamError("E7", op, "ROOT_NAME contains invalid separator characters")

    line7 = parse_line_normalized_lf(handle, op, eof_code="E6")
    if line7 != b"END_HEADER":
        raise TreeStreamError("E6", op, "invalid header structure: missing END_HEADER")

    return root_name


def _parse_record_header(handle) -> tuple[str, int]:
    op = "reconstruction"

    marker = parse_line_normalized_lf(handle, op, eof_code="E6")
    if marker != b"FILE":
        raise TreeStreamError("E6", op, "invalid record structure: expected FILE marker")

    path_line = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not path_line.startswith(b"PATH: "):
        raise TreeStreamError("E6", op, "invalid record structure: malformed PATH line")
    if path_line == b"PATH: ":
        raise TreeStreamError("E6", op, "invalid record structure: empty PATH value")
    raw_path_value = path_line[len(b"PATH: ") :]
    if raw_path_value == b"":
        raise TreeStreamError("E6", op, "invalid record structure: empty PATH value")

    path_value = raw_path_value.decode("utf-8", errors="strict")
    if path_value != path_value.strip():
        raise TreeStreamError("E6", op, "invalid record structure: PATH value has surrounding whitespace")

    length_line = parse_line_normalized_lf(handle, op, eof_code="E6")
    if not length_line.startswith(b"CONTENT_BYTES: "):
        raise TreeStreamError("E6", op, "invalid record structure: malformed CONTENT_BYTES line")
    content_bytes = parse_content_bytes_field(length_line[len(b"CONTENT_BYTES: ") :], op)

    begin = parse_line_normalized_lf(handle, op, eof_code="E6")
    if begin != b"BEGIN_CONTENT":
        raise TreeStreamError("E6", op, "invalid record structure: missing BEGIN_CONTENT")

    return path_value, content_bytes


@dataclass(frozen=True)
class _ParsedRecord:
    path_value: str
    content_bytes: int
    encoded_bytes: int
    content_offset: int
    dst_path: Path | None = None


def _parse_all_records(handle) -> list[_ParsedRecord]:
    records: list[_ParsedRecord] = []
    in_trailing_blank_region = False
    while True:
        pos = handle.tell()
        first = handle.read(1)
        if first == b"":
            break

        if in_trailing_blank_region:
            if first == b"\n":
                continue
            if first == b"\r":
                next_byte = handle.read(1)
                if next_byte == b"\n":
                    continue
                raise TreeStreamError("E6", "reconstruction", "standalone CR is invalid in structural input")
            raise TreeStreamError("E6", "reconstruction", "non-blank trailing bytes after final END_FILE")

        if first == b"\n":
            if records:
                in_trailing_blank_region = True
                continue
            raise TreeStreamError("E6", "reconstruction", "invalid record structure: expected FILE marker")
        if first == b"\r":
            next_byte = handle.read(1)
            if next_byte != b"\n":
                raise TreeStreamError("E6", "reconstruction", "standalone CR is invalid in structural input")
            if records:
                in_trailing_blank_region = True
                continue
            raise TreeStreamError("E6", "reconstruction", "invalid record structure: expected FILE marker")

        handle.seek(pos)

        path_value, content_bytes = _parse_record_header(handle)
        encoded_bytes = encoded_content_length(content_bytes)
        content_offset = handle.tell()
        handle.seek(encoded_bytes, os.SEEK_CUR)

        separator = handle.read(1)
        if separator == b"":
            raise TreeStreamError("E8", "reconstruction", "unexpected EOF after content block", path_value)
        if separator == b"\n":
            pass
        elif separator == b"\r":
            next_byte = handle.read(1)
            if next_byte != b"\n":
                raise TreeStreamError("E6", "reconstruction", "standalone CR is invalid in structural input", path_value)
        else:
            raise TreeStreamError("E8", "reconstruction", "CONTENT_BYTES does not align with structural separator", path_value)

        end_content = parse_line_normalized_lf(handle, "reconstruction", eof_code="E8")
        if end_content != b"END_CONTENT":
            raise TreeStreamError("E6", "reconstruction", "invalid record structure: missing END_CONTENT", path_value)

        end_file = parse_line_normalized_lf(handle, "reconstruction", eof_code="E8")
        if end_file != b"END_FILE":
            raise TreeStreamError("E6", "reconstruction", "invalid record structure: missing END_FILE", path_value)

        records.append(
            _ParsedRecord(
                path_value=path_value,
                content_bytes=content_bytes,
                encoded_bytes=encoded_bytes,
                content_offset=content_offset,
            )
        )

    return records


def _validate_paths_before_ordering(records: list[_ParsedRecord], target_abs: Path) -> list[_ParsedRecord]:
    validated: list[_ParsedRecord] = []
    seen_casefold: set[str] = set()
    for record in records:
        dst_path = validate_serialized_path(record.path_value, target_abs, "reconstruction")
        folded = record.path_value.casefold()
        if folded in seen_casefold:
            raise TreeStreamError("E9", "reconstruction", "case-insensitive PATH collision", record.path_value)
        seen_casefold.add(folded)
        validated.append(
            _ParsedRecord(
                path_value=record.path_value,
                content_bytes=record.content_bytes,
                encoded_bytes=record.encoded_bytes,
                content_offset=record.content_offset,
                dst_path=dst_path,
            )
        )
    return validated


def reconstruct(
    serialized_file: str | os.PathLike[str],
    target_directory: str | os.PathLike[str],
    *,
    overwrite: bool = False,
) -> None:
    assert_windows("reconstruction")

    src = Path(serialized_file)
    target = Path(target_directory)
    target_abs = target.resolve(strict=False)

    try:
        with open(src, "rb") as handle:
            root_name = _parse_header(handle)
            parsed_records = _parse_all_records(handle)
            root_target_abs = (target_abs / root_name).resolve(strict=False)
            try:
                root_target_abs.relative_to(target_abs)
            except ValueError as exc:
                raise TreeStreamError("E7", "reconstruction", "ROOT_NAME escapes target directory", root_name) from exc
            records = _validate_paths_before_ordering(parsed_records, root_target_abs)

            if not target_abs.exists():
                try:
                    target_abs.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to create target directory", str(target_abs)) from exc
            if root_target_abs.exists() and not root_target_abs.is_dir():
                raise TreeStreamError("E10", "reconstruction", "root reconstruction path is not a directory", str(root_target_abs))
            if not root_target_abs.exists():
                try:
                    root_target_abs.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to create root reconstruction directory", str(root_target_abs)) from exc

            for record in records:
                dst_path = record.dst_path
                if dst_path is None:
                    raise TreeStreamError("E10", "reconstruction", "internal error: missing validated destination path")

                if dst_path.exists() and dst_path.is_file() and not overwrite:
                    raise TreeStreamError("E11", "reconstruction", "overwrite disabled and target file exists", str(dst_path))
                if dst_path.exists() and dst_path.is_dir():
                    raise TreeStreamError("E10", "reconstruction", "target path is an existing directory", str(dst_path))

                try:
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to create parent directories", str(dst_path.parent)) from exc

                handle.seek(record.content_offset)
                remaining = record.encoded_bytes
                decoded_written = 0
                try:
                    with open(dst_path, "wb") as dst:
                        while remaining > 0:
                            quantum_count = min(16384, remaining // 4)
                            chunk = handle.read(quantum_count * 4)
                            if chunk == b"":
                                raise TreeStreamError("E8", "reconstruction", "unexpected EOF while reading content bytes", record.path_value)
                            try:
                                decoded = base64.b64decode(chunk, validate=True)
                            except binascii.Error as exc:
                                raise TreeStreamError("E12", "reconstruction", "content block is not valid standard Base64", record.path_value) from exc
                            dst.write(decoded)
                            decoded_written += len(decoded)
                            remaining -= len(chunk)
                    if decoded_written != record.content_bytes:
                        raise TreeStreamError("E12", "reconstruction", "decoded content length does not match CONTENT_BYTES", record.path_value)
                except TreeStreamError:
                    raise
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to write target file", str(dst_path)) from exc
    except TreeStreamError:
        raise
    except FileNotFoundError as exc:
        raise TreeStreamError("E6", "reconstruction", "serialized file does not exist", str(src)) from exc
    except PermissionError as exc:
        raise TreeStreamError("E10", "reconstruction", "permission denied while reading/writing files", str(src)) from exc
    except UnicodeDecodeError as exc:
        raise TreeStreamError("E6", "reconstruction", "PATH line is not valid UTF-8", str(src)) from exc
    except OSError as exc:
        raise TreeStreamError("E10", "reconstruction", "filesystem error during reconstruction", str(src)) from exc
