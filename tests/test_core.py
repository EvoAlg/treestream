"""tests/test_core.py — Scenarios S01–S24 for TreeStream SPEC v0.1.16.

Run with:
    $env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_core
"""
from __future__ import annotations

import base64
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from treestream import TreeStreamError, reconstruct, serialize

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURES = _REPO_ROOT / "fixtures"
_ROUNDTRIP = _FIXTURES / "roundtrip"
_DETERMINISM = _FIXTURES / "determinism"
_ERRORS = _FIXTURES / "errors"
_SPEC_VERSION = "v0.1.16"


def _make_treestream(root_name: str, records: list[tuple[str, bytes]]) -> bytes:
    """Build a minimal valid v0.1.16 treestream payload in memory."""
    out: list[bytes] = [
        b"TREESTREAM 1\n",
        f"SPEC_VERSION: {_SPEC_VERSION}\n".encode(),
        b"ENCODING: UTF-8\n",
        b"NEWLINES: LF\n",
        b"RECORDS: FILE\n",
        f"ROOT_NAME: {root_name}\n".encode(),
        b"END_HEADER\n",
    ]
    for path_val, content in records:
        encoded = base64.b64encode(content)
        out.append(b"FILE\n")
        out.append(f"PATH: {path_val}\n".encode())
        out.append(f"CONTENT_BYTES: {len(content)}\n".encode())
        out.append(b"BEGIN_CONTENT\n")
        out.append(encoded)
        out.append(b"\nEND_CONTENT\nEND_FILE\n")
    return b"".join(out)


def _collect_tree(root: Path) -> dict[str, bytes]:
    """Return {relative_posix_path: bytes} for every file under root."""
    result: dict[str, bytes] = {}
    for dirpath, _dirs, filenames in os.walk(root):
        for fname in filenames:
            abs_path = Path(dirpath) / fname
            rel = abs_path.relative_to(root).as_posix()
            result[rel] = abs_path.read_bytes()
    return result


class TestTreeStreamCore(unittest.TestCase):

    def setUp(self) -> None:
        self.workdir = Path(__file__).resolve().parent / "_test_work_core"
        if self.workdir.exists():
            shutil.rmtree(self.workdir)
        self.workdir.mkdir()

    def tearDown(self) -> None:
        if self.workdir.exists():
            shutil.rmtree(self.workdir)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _output(self, name: str) -> Path:
        """Return a Path for a temp output file inside the workdir."""
        return self.workdir / name

    def _target(self, name: str) -> Path:
        """Return a Path for a temp target directory inside the workdir."""
        p = self.workdir / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _write_payload(self, payload: bytes, name: str) -> Path:
        """Write bytes to a file inside the workdir and return its path."""
        p = self.workdir / name
        p.write_bytes(payload)
        return p

    # ------------------------------------------------------------------
    # S01 — Basic round-trip integrity
    # ------------------------------------------------------------------

    def test_s01_basic_round_trip_integrity(self) -> None:
        out = self._output("s01.treestream")
        target = self._target("s01_target")
        serialize(_ROUNDTRIP, out)
        reconstruct(out, target)
        recon_root = target / "roundtrip"
        self.assertTrue(recon_root.is_dir(), "Reconstructed root subdir must exist")
        self.assertTrue(
            (recon_root / "top1.txt").exists(),
            "top1.txt must exist after round-trip",
        )
        self.assertEqual(
            (_ROUNDTRIP / "top1.txt").read_bytes(),
            (recon_root / "top1.txt").read_bytes(),
        )

    # ------------------------------------------------------------------
    # S02 — Nested directory structure
    # ------------------------------------------------------------------

    def test_s02_nested_directory_structure(self) -> None:
        out = self._output("s02.treestream")
        target = self._target("s02_target")
        serialize(_ROUNDTRIP, out)
        reconstruct(out, target)
        recon_root = target / "roundtrip"
        deep = recon_root / "deep" / "level1" / "level2" / "level3" / "deep.txt"
        self.assertTrue(deep.exists(), "Deeply nested file must survive round-trip")
        self.assertEqual(
            (_ROUNDTRIP / "deep" / "level1" / "level2" / "level3" / "deep.txt").read_bytes(),
            deep.read_bytes(),
        )
        self.assertEqual(_collect_tree(_ROUNDTRIP), _collect_tree(recon_root))

    # ------------------------------------------------------------------
    # S03 — Empty file handling
    # ------------------------------------------------------------------

    def test_s03_empty_file_handling(self) -> None:
        out = self._output("s03.treestream")
        target = self._target("s03_target")
        serialize(_ROUNDTRIP, out)
        raw = out.read_bytes()
        # Locate the record for empty.txt and confirm CONTENT_BYTES: 0
        idx = raw.index(b"PATH: empty.txt\n")
        snippet = raw[idx : idx + 60]
        self.assertIn(b"CONTENT_BYTES: 0\n", snippet)
        # Reconstruct and verify zero-byte file
        reconstruct(out, target)
        recon_empty = target / "roundtrip" / "empty.txt"
        self.assertTrue(recon_empty.exists())
        self.assertEqual(recon_empty.stat().st_size, 0)

    # ------------------------------------------------------------------
    # S04 — CRLF preservation
    # ------------------------------------------------------------------

    def test_s04_crlf_preservation(self) -> None:
        original = (_ROUNDTRIP / "crlf.txt").read_bytes()
        self.assertIn(b"\r\n", original, "crlf.txt fixture must contain CRLF bytes")
        out = self._output("s04.treestream")
        target = self._target("s04_target")
        serialize(_ROUNDTRIP, out)
        raw = out.read_bytes()
        # Extract and decode the base64 block for crlf.txt
        idx = raw.index(b"PATH: crlf.txt\n")
        b64_start = raw.index(b"BEGIN_CONTENT\n", idx) + len(b"BEGIN_CONTENT\n")
        b64_end = raw.index(b"\n", b64_start)
        decoded = base64.b64decode(raw[b64_start:b64_end])
        self.assertEqual(decoded, original)
        # Round-trip must restore CRLF bytes intact
        reconstruct(out, target)
        self.assertEqual((target / "roundtrip" / "crlf.txt").read_bytes(), original)

    # ------------------------------------------------------------------
    # S05 — Deterministic ordering
    # ------------------------------------------------------------------

    def test_s05_deterministic_ordering(self) -> None:
        out1 = self._output("s05_run1.treestream")
        out2 = self._output("s05_run2.treestream")
        serialize(_DETERMINISM, out1)
        serialize(_DETERMINISM, out2)
        bytes1 = out1.read_bytes()
        bytes2 = out2.read_bytes()
        self.assertEqual(bytes1, bytes2, "Two serializations must be byte-for-byte identical")
        paths = [
            line[6:].decode("utf-8")
            for line in bytes1.split(b"\n")
            if line.startswith(b"PATH: ")
        ]
        self.assertEqual(paths, sorted(paths), "PATH records must be in ordinal Unicode order")

    # ------------------------------------------------------------------
    # S06 — Empty root directory
    # ------------------------------------------------------------------

    def test_s06_empty_root_directory(self) -> None:
        empty_root = self.workdir / "empty_root_s06"
        empty_root.mkdir()
        out = self._output("s06.treestream")
        serialize(empty_root, out)
        raw = out.read_bytes()
        self.assertIn(b"TREESTREAM 1\n", raw)
        # Verify no FILE records appear after END_HEADER.
        # assertNotIn(b"FILE\n", raw) would be wrong: the header always contains
        # "RECORDS: FILE\n", which is a false match.
        end_header_pos = raw.index(b"END_HEADER\n") + len(b"END_HEADER\n")
        body = raw[end_header_pos:]
        self.assertNotIn(b"FILE\n", body)
        # Reconstruct — must create an empty subdirectory named after the root
        target = self._target("s06_target")
        reconstruct(out, target)
        recon_root = target / "empty_root_s06"
        self.assertTrue(recon_root.is_dir())
        self.assertEqual(list(recon_root.iterdir()), [])

    # ------------------------------------------------------------------
    # S07 — Non-existent target directory is created
    # ------------------------------------------------------------------

    def test_s07_nonexistent_target_directory_created(self) -> None:
        out = self._output("s07.treestream")
        serialize(_ROUNDTRIP, out)
        target = self.workdir / "s07_new_parent" / "s07_new_target"
        self.assertFalse(target.exists())
        reconstruct(out, target)
        self.assertTrue(target.is_dir())
        self.assertTrue((target / "roundtrip").is_dir())
        self.assertTrue((target / "roundtrip" / "top1.txt").exists())

    # ------------------------------------------------------------------
    # S08 — File content contains bytes invalid under UTF-8 strict → E4
    # ------------------------------------------------------------------

    def test_s08_invalid_utf8_triggers_e4(self) -> None:
        src = _ERRORS / "serialize_invalid_utf8"
        out = self._output("s08.treestream")
        with self.assertRaises(TreeStreamError) as ctx:
            serialize(src, out)
        self.assertEqual(ctx.exception.code, "E4")

    # ------------------------------------------------------------------
    # S09 — Symlink or junction encountered → E5
    # ------------------------------------------------------------------

    def test_s09_symlink_triggers_e5(self) -> None:
        src_dir = self.workdir / "s09_src"
        src_dir.mkdir()
        real_file = src_dir / "real.txt"
        real_file.write_bytes(b"real content")
        link = src_dir / "link.txt"
        try:
            os.symlink(str(real_file), str(link))
        except OSError as exc:
            self.skipTest(f"Symlink creation not permitted on this system: {exc}")
        out = self._output("s09.treestream")
        with self.assertRaises(TreeStreamError) as ctx:
            serialize(src_dir, out)
        self.assertEqual(ctx.exception.code, "E5")

    # ------------------------------------------------------------------
    # S10 — Atomic output on failure, no pre-existing output file
    # ------------------------------------------------------------------

    def test_s10_atomic_no_preexisting_output(self) -> None:
        src = _ERRORS / "serialize_invalid_utf8"
        out = self._output("s10.treestream")
        self.assertFalse(out.exists())
        with self.assertRaises(TreeStreamError) as ctx:
            serialize(src, out)
        self.assertEqual(ctx.exception.code, "E4")
        self.assertFalse(out.exists(), "Output file must not exist after failed serialization")

    # ------------------------------------------------------------------
    # S11 — Atomic output on failure with pre-existing output file
    # ------------------------------------------------------------------

    def test_s11_atomic_preexisting_output_preserved(self) -> None:
        src = _ERRORS / "serialize_invalid_utf8"
        out = self._output("s11.treestream")
        sentinel = b"pre-existing output -- must survive serialization failure"
        out.write_bytes(sentinel)
        with self.assertRaises(TreeStreamError) as ctx:
            serialize(src, out)
        self.assertEqual(ctx.exception.code, "E4")
        self.assertEqual(out.read_bytes(), sentinel)

    # ------------------------------------------------------------------
    # S12 — Incorrect SPEC_VERSION in header → E7
    # ------------------------------------------------------------------

    def test_s12_incorrect_spec_version_triggers_e7(self) -> None:
        fixture = _ERRORS / "recon_E7_header_mismatch.treestream"
        target = self._target("s12_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(fixture, target)
        self.assertEqual(ctx.exception.code, "E7")

    # ------------------------------------------------------------------
    # S13 — CONTENT_BYTES mismatch → E8
    # ------------------------------------------------------------------

    def test_s13_content_bytes_mismatch_triggers_e8(self) -> None:
        # CONTENT_BYTES declares 10 but actual encoded content decodes to 5 bytes.
        content = b"Hello"
        encoded = base64.b64encode(content)  # 8 base64 chars, decodes to 5 bytes
        payload = (
            b"TREESTREAM 1\n"
            b"SPEC_VERSION: v0.1.16\n"
            b"ENCODING: UTF-8\n"
            b"NEWLINES: LF\n"
            b"RECORDS: FILE\n"
            b"ROOT_NAME: test\n"
            b"END_HEADER\n"
            b"FILE\n"
            b"PATH: ok.txt\n"
            b"CONTENT_BYTES: 10\n"
            b"BEGIN_CONTENT\n"
            + encoded
            + b"\nEND_CONTENT\nEND_FILE\n"
        )
        tmp = self._write_payload(payload, "s13.treestream")
        target = self._target("s13_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target)
        self.assertEqual(ctx.exception.code, "E8")

    # ------------------------------------------------------------------
    # S14 — Missing EOF marker → E8
    # ------------------------------------------------------------------

    def test_s14_missing_eof_marker_triggers_e8(self) -> None:
        # Payload truncated: record header present but content block is absent.
        payload = (
            b"TREESTREAM 1\n"
            b"SPEC_VERSION: v0.1.16\n"
            b"ENCODING: UTF-8\n"
            b"NEWLINES: LF\n"
            b"RECORDS: FILE\n"
            b"ROOT_NAME: test\n"
            b"END_HEADER\n"
            b"FILE\n"
            b"PATH: trunc.txt\n"
            b"CONTENT_BYTES: 5\n"
            b"BEGIN_CONTENT\n"
            # No base64 data, no structural separator, no END_CONTENT, no END_FILE
        )
        tmp = self._write_payload(payload, "s14.treestream")
        target = self._target("s14_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target)
        self.assertEqual(ctx.exception.code, "E8")

    # ------------------------------------------------------------------
    # S15 — Non-blank trailing bytes after final END_FILE → E6
    # ------------------------------------------------------------------

    def test_s15_nonblank_trailing_bytes_triggers_e6(self) -> None:
        payload = _make_treestream("test", [("hello.txt", b"Hello")])
        payload += b"JUNK\n"
        tmp = self._write_payload(payload, "s15.treestream")
        target = self._target("s15_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target)
        self.assertEqual(ctx.exception.code, "E6")

    # ------------------------------------------------------------------
    # S16 — Path traversal via ".." component → E9
    # ------------------------------------------------------------------

    def test_s16_path_traversal_triggers_e9(self) -> None:
        payload = (
            b"TREESTREAM 1\n"
            b"SPEC_VERSION: v0.1.16\n"
            b"ENCODING: UTF-8\n"
            b"NEWLINES: LF\n"
            b"RECORDS: FILE\n"
            b"ROOT_NAME: test\n"
            b"END_HEADER\n"
            b"FILE\n"
            b"PATH: ../escape.txt\n"
            b"CONTENT_BYTES: 1\n"
            b"BEGIN_CONTENT\n"
            + base64.b64encode(b"x")
            + b"\nEND_CONTENT\nEND_FILE\n"
        )
        tmp = self._write_payload(payload, "s16.treestream")
        target = self._target("s16_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target)
        self.assertEqual(ctx.exception.code, "E9")

    # ------------------------------------------------------------------
    # S17 — Case-insensitive path collision → E9
    # ------------------------------------------------------------------

    def test_s17_case_insensitive_collision_triggers_e9(self) -> None:
        # "File.txt" and "file.txt" collide under case-insensitive comparison.
        payload = _make_treestream("test", [
            ("File.txt", b"content A"),
            ("file.txt", b"content B"),
        ])
        tmp = self._write_payload(payload, "s17.treestream")
        target = self._target("s17_target")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target)
        self.assertEqual(ctx.exception.code, "E9")

    # ------------------------------------------------------------------
    # S18 — Overwrite prohibited → E11
    # ------------------------------------------------------------------

    def test_s18_overwrite_prohibited_triggers_e11(self) -> None:
        payload = _make_treestream("myroot", [("a.txt", b"original")])
        tmp = self._write_payload(payload, "s18.treestream")
        target = self._target("s18_target")
        # Pre-create the root subdir and the conflicting file
        root_subdir = target / "myroot"
        root_subdir.mkdir(parents=True, exist_ok=True)
        (root_subdir / "a.txt").write_bytes(b"existing content")
        with self.assertRaises(TreeStreamError) as ctx:
            reconstruct(tmp, target, overwrite=False)
        self.assertEqual(ctx.exception.code, "E11")

    # ------------------------------------------------------------------
    # S19 — Target directory cannot be created → E10
    # ------------------------------------------------------------------

    def test_s19_target_cannot_be_created_triggers_e10(self) -> None:
        payload = _make_treestream("test", [("hello.txt", b"Hello")])
        tmp = self._write_payload(payload, "s19.treestream")
        # Target does not yet exist; Path.mkdir is patched to raise OSError.
        target = self.workdir / "s19_target"

        with patch(
            "treestream.reconstructor.Path.mkdir",
            side_effect=OSError("permission denied"),
        ):
            with self.assertRaises(TreeStreamError) as ctx:
                reconstruct(tmp, str(target))
        self.assertEqual(ctx.exception.code, "E10")

    # ------------------------------------------------------------------
    # S20 — Email body round-trip with CRLF-normalized structure
    # ------------------------------------------------------------------

    def test_s20_email_crlf_round_trip(self) -> None:
        lf_out = self._output("s20_lf.treestream")
        serialize(_ROUNDTRIP, lf_out)
        lf_bytes = lf_out.read_bytes()
        # Serialized output must be LF-only (base64 has no \r, so any \r is structural)
        self.assertNotIn(b"\r", lf_bytes, "Serializer must emit LF-only structural lines")
        # Simulate email normalization: every LF becomes CRLF
        crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
        crlf_file = self._write_payload(crlf_bytes, "s20_crlf.treestream")
        target = self._target("s20_target")
        reconstruct(crlf_file, target)
        recon_root = target / "roundtrip"
        self.assertEqual(_collect_tree(_ROUNDTRIP), _collect_tree(recon_root))
        # Re-serializing the reconstructed output must still produce LF-only structural lines
        reserialize_out = self._output("s20_reserialize.treestream")
        serialize(recon_root, reserialize_out)
        self.assertNotIn(b"\r", reserialize_out.read_bytes())

    # ------------------------------------------------------------------
    # S21 — Clipboard round-trip with CRLF structural input tolerance
    # ------------------------------------------------------------------

    def test_s21_clipboard_crlf_round_trip(self) -> None:
        lf_out = self._output("s21_lf.treestream")
        serialize(_ROUNDTRIP, lf_out)
        lf_bytes = lf_out.read_bytes()
        # Simulate clipboard paste: structural LF → CRLF
        crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
        crlf_file = self._write_payload(crlf_bytes, "s21_crlf.treestream")
        target = self._target("s21_target")
        reconstruct(crlf_file, target)
        recon_root = target / "roundtrip"
        self.assertEqual(_collect_tree(_ROUNDTRIP), _collect_tree(recon_root))

    # ------------------------------------------------------------------
    # S22 — Trailing blank lines after final record are tolerated
    # ------------------------------------------------------------------

    def test_s22_trailing_blank_lines_tolerated(self) -> None:
        payload = _make_treestream("test", [("hello.txt", b"Hello")])
        payload += b"\n\n\n"
        tmp = self._write_payload(payload, "s22.treestream")
        target = self._target("s22_target")
        reconstruct(tmp, target)
        result_file = target / "test" / "hello.txt"
        self.assertTrue(result_file.exists())
        self.assertEqual(result_file.read_bytes(), b"Hello")

    # ------------------------------------------------------------------
    # S23 — Base64 content encoding round-trip integrity
    # ------------------------------------------------------------------

    def test_s23_base64_encoding_round_trip(self) -> None:
        out = self._output("s23.treestream")
        serialize(_ROUNDTRIP, out)
        raw = out.read_bytes()
        # Parse every record and validate base64 encoding and CONTENT_BYTES
        pos = raw.index(b"END_HEADER\n") + len(b"END_HEADER\n")
        while pos < len(raw):
            if raw[pos : pos + 5] != b"FILE\n":
                break
            pos += 5
            # PATH line
            path_end = raw.index(b"\n", pos)
            pos = path_end + 1
            # CONTENT_BYTES line
            cb_end = raw.index(b"\n", pos)
            cb_line = raw[pos:cb_end]
            self.assertTrue(cb_line.startswith(b"CONTENT_BYTES: "))
            declared = int(cb_line[len(b"CONTENT_BYTES: "):])
            pos = cb_end + 1
            # BEGIN_CONTENT line
            self.assertEqual(raw[pos : pos + 14], b"BEGIN_CONTENT\n")
            pos += 14
            # Base64 block: runs until the structural LF separator
            b64_end = raw.index(b"\n", pos)
            b64_block = raw[pos:b64_end]
            self.assertNotIn(b"\n", b64_block, "Base64 block must contain no newlines")
            if b64_block:
                try:
                    decoded = base64.b64decode(b64_block, validate=True)
                except Exception as exc:
                    self.fail(f"Invalid base64 at offset {pos}: {exc}")
                self.assertEqual(
                    len(decoded),
                    declared,
                    f"Decoded length {len(decoded)} != CONTENT_BYTES {declared}",
                )
            else:
                self.assertEqual(declared, 0)
            pos = b64_end + 1
            # END_CONTENT line
            self.assertEqual(raw[pos : pos + 12], b"END_CONTENT\n")
            pos += 12
            # END_FILE line
            self.assertEqual(raw[pos : pos + 9], b"END_FILE\n")
            pos += 9
        # Full round-trip file content verification
        target = self._target("s23_target")
        reconstruct(out, target)
        self.assertEqual(_collect_tree(_ROUNDTRIP), _collect_tree(target / "roundtrip"))

    # ------------------------------------------------------------------
    # S24 — Root directory name is preserved through round-trip
    # ------------------------------------------------------------------

    def test_s24_root_directory_name_preserved(self) -> None:
        out = self._output("s24.treestream")
        serialize(_ROUNDTRIP, out)
        raw = out.read_bytes()
        self.assertIn(b"ROOT_NAME: roundtrip\n", raw)
        target = self._target("s24_target")
        reconstruct(out, target)
        recon_root = target / "roundtrip"
        self.assertTrue(recon_root.is_dir())
        self.assertEqual(_collect_tree(_ROUNDTRIP), _collect_tree(recon_root))


if __name__ == "__main__":
    unittest.main()
