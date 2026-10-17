# Reproducing a problem

Start with the [worked examples](examples/EXAMPLES.txt) to distinguish an input failure from a date-policy finding.

For a useful bug report, include:

- The release tag or commit, Python version and operating system.
- The exact command, including any strictness flags and the `--now` value.
- A minimal fictional HTML or XML file that reproduces the problem.
- The observed exit code and diagnostic, and the behavior you expected.

Use an explicit aware `--now` timestamp when reproducing clock-dependent behavior. It is the assessment clock, not evidence of a video's actual publication time. Replace private content with a small fictional example before sharing it.

Exit `0` may still contain warnings or a zero-video scan. Exit `1` means lint or policy errors; exit `2` means an input, parse or usage failure. Review scan counts and diagnostic codes alongside the exit code. The tool reads local files and does not fetch video URLs or repair inputs.

# Checking a change

From the repository root, use Python 3.10 or newer:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B examples/verify_examples.py
```

On Windows, use `python` if `python3` is unavailable. No third-party packages are required. The example verifier returns `0` when its seven documented CLI outcomes match, including demonstrations that intentionally produce errors.

For a proposed change, add a small behavioral fixture that demonstrates the problem and its expected result. Keep the default and strict policies distinct, preserve input files, and describe any intentional change to the CLI or report format. A passing local check does not establish video availability, indexing or ranking.

This guide was prepared with AI assistance. Project context and maintainer: [Ahmadreza Samadi](https://a-samadi.com/about.html).
