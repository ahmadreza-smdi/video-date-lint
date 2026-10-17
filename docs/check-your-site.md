# Check video dates before publishing a site

Run the linter against the HTML you intend to publish. A successful check means the supplied metadata passes the selected date policy. It cannot establish the real first publication time, complete structured data, indexing or ranking.

## Run against local output

Keep a copy of this utility outside the directory being scanned. With the utility in `.video-date-lint/` and your finished HTML in `public/`, run from their parent directory:

```sh
python .video-date-lint/video_datetime_lint.py public --strict-datetime --require-video --format json
```

Use Python 3.10 or newer; use `python3` if that is your local command. Replace `public` with the directory containing your actual publication output. Build the site first if the HTML is generated. Scanning a source directory containing templates or a utility checkout can produce unrelated errors or a misleading zero-video result. In particular, this utility's example directory contains intentional failures.

This example chooses two project policies: publication dates must include a full datetime and timezone, and the scan must contain at least one VideoObject. Remove `--require-video` for sites where no video is expected, while still inspecting the reported scan counts. Never invent a clock time to make an old date pass strict mode.

The command uses the current UTC clock. Omit the fixed `--now` value from teaching examples in a live publication check. Future dates fail; check public output rather than unpublished scheduled drafts.

## Add the check to GitHub Actions

Copy [the workflow example](../examples/check-site-workflow.yml) into your site's `.github/workflows/check-video-dates.yml`. It assumes the site commits finished HTML under `public/`. Change that path or add your site's build steps before the lint step. The linter itself needs no package installation.

The example checks out your site and a fixed public revision of this utility in separate directories. It uses read-only repository permissions and does not publish or repair files. Keep the utility revision explicit when updating it. The action references are also pinned; review their upstream releases before changing those pins. GitHub Actions requires network access for checkout and Python setup, although the linter's own execution makes no network requests.

The command prints its JSON report in the job log. Exit 0 permits the next step but may still include warnings; exit 1 means a date-policy failure and exit 2 means an input or usage failure. This workflow does not configure branch protection or make the check mandatory. The repository administrator chooses whether a merge or deployment requires it.

## Include a video sitemap when available

For a local video sitemap, append `--sitemap public/video-sitemap.xml` to the command. Add `--require-sitemap-dates` only if every supplied video entry is expected to have a publication date. Supply individual video sitemap files with repeated `--sitemap`; a sitemap index is unsupported. A normal page sitemap does not replace a video sitemap.

Matching requires the exact same VideoObject `contentUrl` and video sitemap `content_loc`. Different spellings, player URLs and titles do not establish identity. Inspect warnings and comparison counts to see which supplied records were actually compared.

## References

The [CLI policies](../README.md#policies-and-outcomes) and [synthetic examples](../examples/EXAMPLES.txt) explain the diagnostic and exit contracts. Action configuration follows the official [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) documentation, checked 17 October 2026. This guide and example were prepared with AI assistance for Ahmadreza Samadi's existing utility.
