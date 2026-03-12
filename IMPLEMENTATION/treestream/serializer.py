from __future__ import annotations

import binascii
import codecs
import os
import tempfile
from pathlib import Path

from .errors import TreeStreamError
from .format import assert_windows, build_header_lines, canonical_relative_path, derive_root_name
from .version import SPEC_VERSION

_CHUNK_SIZE = 64 * 1024
_REPARSE_POINT_ATTR = 0x0400


def _is_reparse_point(entry) -> bool:
    if entry.is_symlink():
        return True
    try:
        stat_result = entry.stat(follow_symlinks=False)
    except PermissionError as exc:
        raise TreeStreamError("E2", "serialization", "permission denied while reading filesystem entry", entry.path) from exc
    except OSError as exc:
        raise TreeStreamError("E5", "serialization", "filesystem access error while reading filesystem entry", entry.path) from exc
    return bool(getattr(stat_result, "st_file_attributes", 0) & _REPARSE_POINT_ATTR)


def _collect_files(root_abs: Path) -> list[tuple[str, Path, int]]:
    stack = [root_abs]
    collected: list[tuple[str, Path, int]] = []

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = sorted(list(it), key=lambda e: e.name)
        except PermissionError as exc:
            raise TreeStreamError("E2", "serialization", "permission denied while traversing directory", str(current)) from exc
        except OSError as exc:
            raise TreeStreamError("E5", "serialization", "filesystem access error while traversing directory", str(current)) from exc

        dirs: list[Path] = []
        for entry in entries:
            if _is_reparse_point(entry):
                raise TreeStreamError("E5", "serialization", "reparse point encountered", entry.path)
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except PermissionError as exc:
                raise TreeStreamError("E2", "serialization", "permission denied while inspecting entry", entry.path) from exc
            except OSError as exc:
                raise TreeStreamError("E5", "serialization", "filesystem access error while inspecting entry", entry.path) from exc

            if is_dir:
                dirs.append(Path(entry.path))
                continue
            if is_file:
                rel = canonical_relative_path(root_abs, Path(entry.path))
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                except PermissionError as exc:
                    raise TreeStreamError("E2", "serialization", "permission denied while stating file", entry.path) from exc
                except OSError as exc:
                    raise TreeStreamError("E5", "serialization", "filesystem access error while stating file", entry.path) from exc
                collected.append((rel, Path(entry.path), size))
                continue

            raise TreeStreamError("E3", "serialization", "unsupported filesystem entry type", entry.path)

        for dir_path in reversed(dirs):
            stack.append(dir_path)

    collected.sort(key=lambda item: item[0])
    return collected


def _write_record(handle, rel_path: str, file_path: Path, declared_size: int) -> None:
    handle.write(b"FILE\n")
    handle.write(f"PATH: {rel_path}\n".encode("utf-8"))
    handle.write(f"CONTENT_BYTES: {declared_size}\n".encode("ascii"))
    handle.write(b"BEGIN_CONTENT\n")

    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    written = 0
    carry = b""
    try:
        with open(file_path, "rb") as src:
            while True:
                chunk = src.read(_CHUNK_SIZE)
                if chunk == b"":
                    break
                written += len(chunk)
                try:
                    decoder.decode(chunk, final=False)
                except UnicodeDecodeError as exc:
                    raise TreeStreamError("E4", "serialization", "file is not valid UTF-8 text", str(file_path)) from exc
                buffered = carry + chunk
                whole = (len(buffered) // 3) * 3
                if whole:
                    handle.write(binascii.b2a_base64(buffered[:whole], newline=False))
                carry = buffered[whole:]
            try:
                decoder.decode(b"", final=True)
            except UnicodeDecodeError as exc:
                raise TreeStreamError("E4", "serialization", "file is not valid UTF-8 text", str(file_path)) from exc
            if carry:
                handle.write(binascii.b2a_base64(carry, newline=False))
    except PermissionError as exc:
        raise TreeStreamError("E2", "serialization", "permission denied while reading file", str(file_path)) from exc
    except OSError as exc:
        raise TreeStreamError("E5", "serialization", "filesystem access error while reading file", str(file_path)) from exc

    if written != declared_size:
        raise TreeStreamError("E5", "serialization", "file size changed during read", str(file_path))

    handle.write(b"\nEND_CONTENT\nEND_FILE\n")


def serialize(root_directory: str | os.PathLike[str], output_file: str | os.PathLike[str]) -> None:
    assert_windows("serialization")

    root = Path(root_directory)
    try:
        root_abs = root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise TreeStreamError("E1", "serialization", "root directory does not exist", str(root)) from exc
    except PermissionError as exc:
        raise TreeStreamError("E1", "serialization", "root directory is not accessible", str(root)) from exc
    except OSError as exc:
        raise TreeStreamError("E1", "serialization", "invalid root directory", str(root)) from exc

    if not root_abs.is_dir():
        raise TreeStreamError("E1", "serialization", "root path is not a directory", str(root))

    root_name = derive_root_name(root_abs, "serialization")
    files = _collect_files(root_abs)

    out_path = Path(output_file)
    out_parent = out_path.parent if out_path.parent != Path("") else Path(".")
    out_parent_abs = out_parent.resolve(strict=False)

    tmp_fd = None
    tmp_path: str | None = None
    try:
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix=".treestream.", suffix=".tmp", dir=str(out_parent_abs))
        except OSError as exc:
            raise TreeStreamError("E5", "serialization", "cannot create temporary output file", str(out_path)) from exc

        with os.fdopen(tmp_fd, "wb") as dst:
            tmp_fd = None
            for line in build_header_lines(SPEC_VERSION, root_name):
                dst.write(line)
            for rel_path, file_path, size in files:
                _write_record(dst, rel_path, file_path, size)

        try:
            os.replace(tmp_path, out_path)
        except OSError as exc:
            raise TreeStreamError("E5", "serialization", "failed to replace output file atomically", str(out_path)) from exc
    except TreeStreamError:
        if tmp_fd is not None:
            os.close(tmp_fd)
        if tmp_path is not None:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise
    except Exception:
        if tmp_fd is not None:
            os.close(tmp_fd)
        if tmp_path is not None:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise
