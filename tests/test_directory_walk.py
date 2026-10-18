# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ahmadreza Samadi
"""Excluded trees are not visited; unreadable included trees cannot yield a clean scan."""
import contextlib
import errno
import glob
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

CLI = Path(__file__).resolve().parents[1] / "video_datetime_lint.py"

class DirectoryWalk(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.good = self.root / "good.html"
        self.good.write_text('<script type="application/ld+json">{"@type":"VideoObject",'
                             '"uploadDate":"2026-10-01T00:00:00Z"}</script>', encoding="utf-8")
        spec = importlib.util.spec_from_file_location("linter_directory_fixture", CLI)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def tearDown(self):
        self.temp.cleanup()

    def scan(self, denied):
        original = os.scandir
        visited = []
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        def scandir(path):
            value = Path(path)
            visited.append(value)
            if value in denied:
                raise PermissionError(errno.EACCES, "synthetic directory access denial", str(value))
            return original(path)
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("os.scandir", scandir))
            # Python 3.13+ glob retains its own scandir reference.
            if hasattr(glob, "_StringGlobber"):
                stack.enter_context(mock.patch.object(glob._StringGlobber, "scandir", staticmethod(scandir)))
            stack.enter_context(contextlib.redirect_stdout(out))
            code = self.module.main([str(self.root), "--now", "2026-10-18T00:00:00Z", "--format", "json"])
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        return code, json.loads(out.getvalue()), visited

    def test_ignored_subtrees_are_pruned_before_scandir(self):
        ignored = []
        for name in (".git", "node_modules", "__pycache__"):
            folder = self.root / "nested" / name
            folder.mkdir(parents=True)
            (folder / "invalid.html").write_text('<script type="application/ld+json">invalid</script>')
            ignored.append(folder)
        code, report, visited = self.scan(set(ignored))
        self.assertIn(self.root, visited)
        self.assertEqual((code, report["counts"]["html_files"]), (0, 1))
        self.assertFalse(set(ignored).intersection(visited), visited)

    def test_unreadable_included_subtree_is_error_but_good_html_is_kept(self):
        denied = self.root / "included"
        denied.mkdir()
        (denied / "hidden.html").write_text("<html></html>")
        code, report, visited = self.scan({denied})
        self.assertIn(denied, visited)
        self.assertEqual((code, report["exit_code"]), (2, 2))
        self.assertEqual(report["counts"]["html_files"], 1)
        self.assertEqual(report["counts"]["video_objects"], 1)
        errors = [d for d in report["diagnostics"] if d["code"] == "unreadable_directory"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["path"], str(denied))
        self.assertIn("synthetic directory access denial", errors[0]["message"])

    def test_one_html_stat_failure_does_not_discard_later_sibling(self):
        bad = self.root / "denied.html"
        bad.write_text("<html></html>")
        original_stat = Path.stat
        before = {p.name: p.read_bytes() for p in (bad, self.good)}

        def stat(path, *args, **kwargs):
            if path == bad:
                raise PermissionError(errno.EACCES, "synthetic HTML metadata denial", str(path))
            return original_stat(path, *args, **kwargs)

        output = io.StringIO()
        # A fixed discovery order proves that readable files after the bad one
        # are retained; no filesystem enumeration-order assumption is involved.
        with mock.patch.object(self.module.os, "walk", return_value=[
                (str(self.root), [], [bad.name, self.good.name])]):
            with mock.patch.object(Path, "stat", stat), contextlib.redirect_stdout(output):
                code = self.module.main([str(self.root), "--now", "2026-10-18T00:00:00Z", "--format", "json"])
        report = json.loads(output.getvalue())
        self.assertEqual((code, report["exit_code"]), (2, 2))
        self.assertEqual(report["counts"]["html_files"], 1)
        self.assertEqual(report["counts"]["video_objects"], 1)
        errors = [d for d in report["diagnostics"] if d["severity"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "unreadable_html")
        self.assertEqual(errors[0]["path"], str(bad))
        self.assertIn("synthetic HTML metadata denial", errors[0]["message"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in (bad, self.good)})

    def test_one_html_resolve_failure_does_not_discard_later_sibling(self):
        bad = self.root / "unresolvable.html"
        bad.write_text("<html></html>")
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == bad:
                raise RuntimeError("synthetic HTML symlink resolution failure")
            return original_resolve(path, *args, **kwargs)

        output = io.StringIO()
        with mock.patch.object(self.module.os, "walk", return_value=[
                (str(self.root), [], [bad.name, self.good.name])]):
            with mock.patch.object(Path, "resolve", resolve), contextlib.redirect_stdout(output):
                code = self.module.main([str(self.root), "--now", "2026-10-18T00:00:00Z", "--format", "json"])
        report = json.loads(output.getvalue())
        self.assertEqual((code, report["exit_code"]), (2, 2))
        self.assertEqual(report["counts"]["html_files"], 1)
        errors = [d for d in report["diagnostics"] if d["severity"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["code"], "unreadable_html")
        self.assertEqual(errors[0]["path"], str(bad))

if __name__ == "__main__":
    unittest.main()
