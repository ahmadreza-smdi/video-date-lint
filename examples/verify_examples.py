"""Run documented synthetic examples through the real CLI, without edits or network."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLOCK = "2026-10-10T12:00:00Z"

# Expected public behavior, not generated from the implementation under test.
CASES = [
    ("equivalent", ["examples/equivalent", "--sitemap", "examples/equivalent/sitemap.xml",
                    "--strict-datetime", "--require-video", "--require-sitemap-dates"],
     0, [], {"html_files": 2, "video_objects": 2, "repeated_video_comparisons": 1,
             "sitemap_comparisons": 1, "errors": 0, "warnings": 0}),
    ("impossible", ["examples/impossible.html"], 1,
     [("invalid_publication_date", "error")], {"video_objects": 1, "errors": 1}),
    ("missing-zone-default", ["examples/missing-zone.html"], 0,
     [("missing_timezone", "warning")], {"video_objects": 1, "errors": 0, "warnings": 1}),
    ("missing-zone-strict", ["examples/missing-zone.html", "--strict-datetime"], 1,
     [("missing_timezone", "error")], {"video_objects": 1, "errors": 1, "warnings": 0}),
    ("empty-default", ["examples/no-video.html"], 0, [],
     {"video_objects": 0, "errors": 0, "warnings": 0}),
    ("empty-required", ["examples/no-video.html", "--require-video"], 1,
     [("no_video_objects", "error")], {"video_objects": 0, "errors": 1}),
    ("malformed", ["examples/malformed.html"], 2,
     [("invalid_jsonld", "error")], {"video_objects": 0, "errors": 1}),
]


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in HERE.rglob("*") if p.suffix in {".html", ".xml"}}


def main():
    before = hashes()
    failed = []
    for name, args, exit_code, diagnostics, counts in CASES:
        run = subprocess.run(
            [sys.executable, "-B", str(ROOT / "video_datetime_lint.py"), *args,
             "--now", CLOCK, "--format", "json"], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", timeout=30)
        try:
            report = json.loads(run.stdout)
            actual = sorted((d["code"], d["severity"]) for d in report["diagnostics"])
            passed = (run.returncode == exit_code == report["exit_code"]
                      and actual == sorted(diagnostics) and not run.stderr
                      and all(report["counts"][k] == v for k, v in counts.items()))
        except (ValueError, KeyError, TypeError):
            passed = False
        print(("PASS " if passed else "FAIL ") + name + " (expected CLI exit " + str(exit_code) + ")")
        if not passed:
            failed.append(name)
            print(run.stdout)
            print(run.stderr)
    if hashes() != before:
        failed.append("input files changed")
    print("Input HTML/XML bytes unchanged: " + str(hashes() == before))
    print("7 synthetic CLI runs; these do not establish actual publication or indexing.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
