from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from treestream.cli import build_parser
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

    def _make_root(self, name: str) -> Path:
        root = self.workdir / name
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
