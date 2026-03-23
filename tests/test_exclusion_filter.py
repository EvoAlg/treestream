from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from treestream.cli import build_parser
from treestream.errors import TreeStreamError
from treestream.serializer import serialize


class ExclusionFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workdir = Path(__file__).resolve().parent / "_test_work"
        if self.workdir.exists():
            shutil.rmtree(self.workdir)
        self.workdir.mkdir()

    def tearDown(self) -> None:
        if self.workdir.exists():
            shutil.rmtree(self.workdir)

    def test_cli_accepts_repeatable_exclude(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["serialize", "input-root", "output.treestream", "--exclude", "__pycache__", "--exclude", "*.pyc"]
        )

        self.assertEqual(args.command, "serialize")
        self.assertEqual(args.exclude, ["__pycache__", "*.pyc"])

    def test_s25_excludes_directory_by_exact_name(self) -> None:
        root = self._make_root("s25")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_bytes(root / "__pycache__" / "main.cpython.pyc", b"\xff\xfe\xfa")

        output = self._serialize(root, exclude=["__pycache__"])

        self.assertEqual(self._record_paths(output), ["src/main.py"])

    def test_s26_excludes_files_by_glob_pattern(self) -> None:
        root = self._make_root("s26")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_bytes(root / "src" / "main.pyc", b"\xff\xfe\xfa")
        self._write_text(root / "notes.txt", "notes\n")

        output = self._serialize(root, exclude=["*.pyc"])

        self.assertEqual(self._record_paths(output), ["notes.txt", "src/main.py"])

    def test_s27_multiple_exclusion_patterns_apply_independently(self) -> None:
        root = self._make_root("s27")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_bytes(root / "__pycache__" / "main.cpython.pyc", b"\xff\xfe\xfa")
        self._write_text(root / ".git" / "config", "[core]\n")
        self._write_text(root / "notes.txt", "notes\n")

        output = self._serialize(root, exclude=["__pycache__", ".git"])

        self.assertEqual(self._record_paths(output), ["notes.txt", "src/main.py"])

    def test_s28_non_matching_pattern_matches_baseline_byte_for_byte(self) -> None:
        root = self._make_root("s28")
        self._write_text(root / "docs" / "readme.txt", "hello\n")
        self._write_text(root / "src" / "main.py", "print('ok')\n")

        baseline = self._serialize(root)
        non_matching = self._serialize(root, exclude=["__pycache__"])

        self.assertEqual(non_matching, baseline)

    def test_s29_excluded_directory_is_not_descended(self) -> None:
        root = self._make_root("s29")
        self._write_text(root / "keep" / "data.txt", "keep\n")
        self._write_text(root / "skip_dir" / "readme.txt", "skip\n")
        self._write_text(root / "skip_dir" / "notes.txt", "skip\n")

        scanned: list[Path] = []
        original_scandir = __import__("treestream.serializer", fromlist=["os"]).os.scandir

        def tracking_scandir(path):
            scanned.append(Path(path))
            return original_scandir(path)

        output_path = self.workdir / "s29.treestream"
        with patch("treestream.serializer.os.scandir", side_effect=tracking_scandir):
            serialize(root, output_path, exclude=["skip_dir"])

        self.assertEqual(self._record_paths(output_path.read_bytes()), ["keep/data.txt"])
        self.assertNotIn(root / "skip_dir", scanned)

    def test_gate_g_identical_inputs_and_exclusions_are_deterministic(self) -> None:
        root = self._make_root("gate_g_determinism")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_text(root / "docs" / "readme.txt", "hello\n")
        self._write_bytes(root / "__pycache__" / "main.cpython.pyc", b"\xff\xfe\xfa")
        self._write_bytes(root / "src" / "main.pyc", b"\x80\x81")

        run1 = self._serialize(root, exclude=["__pycache__", "*.pyc"])
        run2 = self._serialize(root, exclude=["__pycache__", "*.pyc"])

        self.assertEqual(run1, run2)

    def test_no_exclude_flag_matches_explicit_empty_exclusions(self) -> None:
        root = self._make_root("no_exclude")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_text(root / "notes.txt", "notes\n")

        baseline = self._serialize(root)
        explicit_empty = self._serialize(root, exclude=[])

        self.assertEqual(explicit_empty, baseline)

    def test_s30_root_treestreamignore_excludes_files_and_ignores_comments_and_blank_lines(self) -> None:
        root = self._make_root("s30")
        self._write_text(root / "keep.txt", "keep\n")
        self._write_text(root / "skip.pyc", "compiled?\n")
        self._write_text(root / "#literal.txt", "comment names are not patterns\n")
        self._write_text(root / "blank.txt", "blank\n")
        self._write_text(root / ".treestreamignore", "# comment\n\n*.pyc\n\n")

        output = self._serialize(root)

        self.assertEqual(self._record_paths(output), ["#literal.txt", "blank.txt", "keep.txt"])
        self.assertNotIn("PATH: .treestreamignore\n", output.decode("utf-8"))

    def test_s31_root_treestreamignore_excludes_directory_without_descent(self) -> None:
        root = self._make_root("s31")
        self._write_text(root / "keep" / "data.txt", "keep\n")
        self._write_text(root / "skip_dir" / "nested.txt", "skip\n")
        self._write_text(root / ".treestreamignore", "skip_dir\n")

        scanned: list[Path] = []
        original_scandir = __import__("treestream.serializer", fromlist=["os"]).os.scandir

        def tracking_scandir(path):
            scanned.append(Path(path))
            return original_scandir(path)

        output_path = self.workdir / "s31.treestream"
        with patch("treestream.serializer.os.scandir", side_effect=tracking_scandir):
            serialize(root, output_path)

        self.assertEqual(self._record_paths(output_path.read_bytes()), ["keep/data.txt"])
        self.assertNotIn(root / "skip_dir", scanned)

    def test_s32_absent_ignore_matches_baseline_and_empty_ignore_matches_without_ignore(self) -> None:
        baseline_root = self._make_named_root("s32", "project")
        self._write_text(baseline_root / "src" / "main.py", "print('ok')\n")
        self._write_text(baseline_root / "notes.txt", "notes\n")

        empty_ignore_root = self._make_named_root("s32_empty", "project")
        self._write_text(empty_ignore_root / "src" / "main.py", "print('ok')\n")
        self._write_text(empty_ignore_root / "notes.txt", "notes\n")
        self._write_text(empty_ignore_root / ".treestreamignore", "")

        baseline = self._serialize(baseline_root)
        absent_ignore = self._serialize(baseline_root)
        empty_ignore = self._serialize(empty_ignore_root)

        self.assertEqual(absent_ignore, baseline)
        self.assertEqual(empty_ignore, baseline)

    def test_s33_ignore_file_and_cli_exclude_are_merged(self) -> None:
        root = self._make_root("s33")
        self._write_text(root / "keep.txt", "keep\n")
        self._write_text(root / "skip.pyc", "compiled?\n")
        self._write_text(root / "cache" / "entry.txt", "cache\n")
        self._write_text(root / ".treestreamignore", "*.pyc\n")

        output = self._serialize(root, exclude=["cache"])

        self.assertEqual(self._record_paths(output), ["keep.txt"])

    def test_s34_root_ignore_is_never_serialized_and_subdirectory_ignore_is_normal_file(self) -> None:
        root = self._make_root("s34")
        self._write_text(root / "keep.txt", "keep\n")
        self._write_text(root / ".treestreamignore", "unused-pattern\n")
        self._write_text(root / "nested" / ".treestreamignore", "nested config\n")

        output = self._serialize(root)

        self.assertEqual(self._record_paths(output), ["keep.txt", "nested/.treestreamignore"])

    def test_s35_ignore_file_inputs_are_deterministic(self) -> None:
        root = self._make_root("s35")
        self._write_text(root / "docs" / "readme.txt", "hello\n")
        self._write_text(root / "src" / "main.py", "print('ok')\n")
        self._write_text(root / "src" / "main.pyc", "compiled?\n")
        self._write_text(root / ".treestreamignore", "*.pyc\n")

        run1 = self._serialize(root)
        run2 = self._serialize(root)

        self.assertEqual(run1, run2)

    def test_s36_invalid_root_ignore_raises_e13_and_writes_no_output(self) -> None:
        root = self._make_root("s36")
        self._write_text(root / "keep.txt", "keep\n")
        self._write_bytes(root / ".treestreamignore", b"\xff")

        output = self.workdir / "s36.treestream"

        with self.assertRaises(TreeStreamError) as ctx:
            serialize(root, output)

        err = ctx.exception
        self.assertEqual(err.code, "E13")
        self.assertEqual(err.operation, "serialization")
        self.assertIn(".treestreamignore", str(err))
        self.assertIn("could not be read as UTF-8", str(err))
        self.assertNotIn("E4", str(err))
        self.assertFalse(output.exists())

    def _make_root(self, name: str) -> Path:
        root = self.workdir / name
        root.mkdir()
        return root

    def _make_named_root(self, parent_name: str, root_name: str) -> Path:
        parent = self.workdir / parent_name
        parent.mkdir()
        root = parent / root_name
        root.mkdir()
        return root

    def _serialize(self, root: Path, exclude: list[str] | None = None) -> bytes:
        output = self.workdir / f"{root.name}.treestream"
        serialize(root, output, exclude=exclude)
        return output.read_bytes()

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")

    def _write_bytes(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def _record_paths(self, payload: bytes) -> list[str]:
        paths: list[str] = []
        for line in payload.decode("utf-8").splitlines():
            if line.startswith("PATH: "):
                paths.append(line[6:])
        return paths


if __name__ == "__main__":
    unittest.main()
