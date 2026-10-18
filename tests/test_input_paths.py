# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ahmadreza Samadi
"""Path-inspection errors must not replace an audit report with a traceback."""

import contextlib
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "video_datetime_lint.py"
NOW = "2026-10-18T00:00:00Z"


class InputPathFailures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="input-path-")
        self.root = Path(self.temp.name)
        self.good = self.root / "good.html"
        self.good.write_text('<script type="application/ld+json">'
                             '{"@type":"VideoObject","uploadDate":"2026-10-01T00:00:00Z",'
                             '"contentUrl":"https://example.invalid/film.mp4"}</script>', encoding="utf-8")
        self.before = self.good.read_bytes()

    def tearDown(self):
        self.assertEqual(self.good.read_bytes(), self.before)
        self.temp.cleanup()

    def test_inspection_oserrors_report_and_continue_with_valid_inputs(self):
        spec = importlib.util.spec_from_file_location("linter_path_fixture", CLI)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bad = self.root / "uninspectable.html"
        for operation in ("absolute", "is_dir", "is_file"):
            with self.subTest(operation=operation):
                original = getattr(Path, operation)

                def fail_selected(path, *args, **kwargs):
                    if path == bad:
                        raise OSError(errno.ENAMETOOLONG, "synthetic path inspection failure", str(path))
                    return original(path, *args, **kwargs)

                output, errors = io.StringIO(), io.StringIO()
                with mock.patch.object(Path, operation, fail_selected):
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                        code = module.main([str(bad), str(self.good), "--now", NOW, "--format", "json"])
                body = json.loads(output.getvalue())
                self.assertEqual((code, body["exit_code"]), (2, 2))
                self.assertEqual(errors.getvalue(), "")
                self.assertEqual(body["counts"]["html_files"], 1)
                self.assertEqual(body["counts"]["video_objects"], 1)
                self.assertEqual(len(body["diagnostics"]), 1)
                self.assertEqual(body["diagnostics"][0]["code"], "unreadable_input")
                self.assertEqual(body["diagnostics"][0]["path"], str(bad))
                self.assertIn("synthetic path inspection failure", body["diagnostics"][0]["message"])

    def test_long_component_subprocess_keeps_valid_file_and_json_contract(self):
        bad = self.root / ("x" * 300 + ".html")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, str(CLI), str(bad), str(self.good),
                                 "--now", NOW, "--format", "json"],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, "")
        body = json.loads(result.stdout)
        self.assertEqual(body["exit_code"], 2)
        self.assertEqual(body["counts"]["html_files"], 1)
        self.assertEqual(body["counts"]["video_objects"], 1)
        self.assertEqual(body["counts"]["errors"], 1)
        # Windows/Python versions may classify an invalid long path as missing.
        self.assertIn(body["diagnostics"][0]["code"], {"unreadable_input", "missing_input"})
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["good.html"])

    def test_text_long_path_with_unicode_parent_is_ascii_reportable(self):
        parent = self.root / "داده"
        parent.mkdir()
        bad = parent / ("x" * 300 + ".html")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="ascii:strict")
        result = subprocess.run([sys.executable, str(CLI), str(bad), str(self.good), "--now", NOW],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.isascii())
        self.assertIn("1 HTML files", result.stdout)
        self.assertIn("exit 2", result.stdout)
        self.assertIn("داده".encode("ascii", "backslashreplace").decode("ascii"), result.stdout)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["good.html", "داده"])


if __name__ == "__main__":
    unittest.main()
