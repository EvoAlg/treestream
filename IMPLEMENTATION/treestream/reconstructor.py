from __future__ import annotations

import os
from pathlib import Path

from .errors import TreeStreamError
from .format import assert_windows, parse_content_bytes_field, parse_line_strict_lf, validate_serialized_path


def _parse_header(handle) -> None:
    op = "reconstruction"
    line1 = parse_line_strict_lf(handle, op, eof_code="E6")
    if line1.startswith(b"TREESTREAM ") and line1 != b"TREESTREAM 1":
        raise TreeStreamError("E7", op, "unsupported TREESTREAM version")
    if line1 != b"TREESTREAM 1":
        raise TreeStreamError("E6", op, "invalid header structure: missing TREESTREAM line")

    line2 = parse_line_strict_lf(handle, op, eof_code="E6")
    if not line2.startswith(b"SPEC_VERSION: "):
        raise TreeStreamError("E6", op, "invalid header structure: SPEC_VERSION line malformed")
    if line2 != b"SPEC_VERSION: v0.1.9":
        raise TreeStreamError("E7", op, "unsupported SPEC_VERSION")

    line3 = parse_line_strict_lf(handle, op, eof_code="E6")
    if not line3.startswith(b"ENCODING: "):
        raise TreeStreamError("E6", op, "invalid header structure: ENCODING line malformed")
    if line3 != b"ENCODING: UTF-8":
        raise TreeStreamError("E7", op, "unsupported ENCODING")

    line4 = parse_line_strict_lf(handle, op, eof_code="E6")
    if not line4.startswith(b"NEWLINES: "):
        raise TreeStreamError("E6", op, "invalid header structure: NEWLINES line malformed")
    if line4 != b"NEWLINES: LF":
        raise TreeStreamError("E7", op, "unsupported NEWLINES value")

    line5 = parse_line_strict_lf(handle, op, eof_code="E6")
    if not line5.startswith(b"RECORDS: "):
        raise TreeStreamError("E6", op, "invalid header structure: RECORDS line malformed")
    if line5 != b"RECORDS: FILE":
        raise TreeStreamError("E7", op, "unsupported RECORDS value")

    line6 = parse_line_strict_lf(handle, op, eof_code="E6")
    if line6 != b"END_HEADER":
        raise TreeStreamError("E6", op, "invalid header structure: missing END_HEADER")


def _parse_record_header(handle) -> tuple[str, int]:
    op = "reconstruction"

    marker = parse_line_strict_lf(handle, op, eof_code="E6")
    if marker != b"FILE":
        raise TreeStreamError("E6", op, "invalid record structure: expected FILE marker")

    path_line = parse_line_strict_lf(handle, op, eof_code="E6")
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

    length_line = parse_line_strict_lf(handle, op, eof_code="E6")
    if not length_line.startswith(b"CONTENT_BYTES: "):
        raise TreeStreamError("E6", op, "invalid record structure: malformed CONTENT_BYTES line")
    content_bytes = parse_content_bytes_field(length_line[len(b"CONTENT_BYTES: ") :], op)

    begin = parse_line_strict_lf(handle, op, eof_code="E6")
    if begin != b"BEGIN_CONTENT":
        raise TreeStreamError("E6", op, "invalid record structure: missing BEGIN_CONTENT")

    return path_value, content_bytes


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
            _parse_header(handle)

            if not target_abs.exists():
                try:
                    target_abs.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to create target directory", str(target_abs)) from exc

            seen_casefold: set[str] = set()
            previous_path: str | None = None

            while True:
                pos = handle.tell()
                first = handle.read(1)
                if first == b"":
                    break
                handle.seek(pos)

                path_value, content_bytes = _parse_record_header(handle)

                folded = path_value.casefold()
                if folded in seen_casefold:
                    raise TreeStreamError("E9", "reconstruction", "case-insensitive PATH collision", path_value)
                seen_casefold.add(folded)

                if previous_path is not None and path_value < previous_path:
                    raise TreeStreamError("E6", "reconstruction", "records are not sorted by PATH")
                previous_path = path_value

                dst_path = validate_serialized_path(path_value, target_abs, "reconstruction")

                if dst_path.exists() and dst_path.is_file() and not overwrite:
                    raise TreeStreamError("E11", "reconstruction", "overwrite disabled and target file exists", str(dst_path))
                if dst_path.exists() and dst_path.is_dir():
                    raise TreeStreamError("E10", "reconstruction", "target path is an existing directory", str(dst_path))

                try:
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to create parent directories", str(dst_path.parent)) from exc

                remaining = content_bytes
                try:
                    with open(dst_path, "wb") as dst:
                        while remaining > 0:
                            chunk = handle.read(min(65536, remaining))
                            if chunk == b"":
                                raise TreeStreamError("E8", "reconstruction", "unexpected EOF while reading content bytes", path_value)
                            dst.write(chunk)
                            remaining -= len(chunk)
                except TreeStreamError:
                    raise
                except OSError as exc:
                    raise TreeStreamError("E10", "reconstruction", "unable to write target file", str(dst_path)) from exc

                separator = handle.read(1)
                if separator == b"":
                    raise TreeStreamError("E8", "reconstruction", "unexpected EOF after content block", path_value)
                if separator != b"\n":
                    raise TreeStreamError("E8", "reconstruction", "CONTENT_BYTES does not align with structural separator", path_value)

                end_content = parse_line_strict_lf(handle, "reconstruction", eof_code="E8")
                if end_content != b"END_CONTENT":
                    raise TreeStreamError("E6", "reconstruction", "invalid record structure: missing END_CONTENT", path_value)

                end_file = parse_line_strict_lf(handle, "reconstruction", eof_code="E8")
                if end_file != b"END_FILE":
                    raise TreeStreamError("E6", "reconstruction", "invalid record structure: missing END_FILE", path_value)
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
