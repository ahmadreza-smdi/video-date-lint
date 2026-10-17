# Read a video-sitemap mismatch and a skipped comparison

These are fictional teaching fixtures, prepared with AI assistance for Ahmadreza Samadi's offline utility. No video is hosted or fetched. The XML contains only the fields this narrow checker uses; it is not a complete video-sitemap template.

Run from the utility repository root with Python 3.10 or newer. Use `python` if that is your local command. Keep the supplied `examples/equivalent/utc.html` unchanged: its exact video URL is `https://example.invalid/film.mp4`, and its timestamp is `2026-10-09T22:00:00Z`.

## 1. A matching video URL with a different instant

Save this as `mismatch.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
  <url><loc>https://example.invalid/watch</loc><video:video>
    <video:content_loc>https://example.invalid/film.mp4</video:content_loc>
    <video:publication_date>2026-10-10T00:30:00+03:30</video:publication_date>
  </video:video></url>
</urlset>
```

```sh
python3 video_datetime_lint.py examples/equivalent/utc.html --sitemap mismatch.xml --strict-datetime --require-sitemap-dates --require-video --now 2026-10-10T12:00:00Z --format json
```

Expected: exit `1`, one `sitemap_video_mismatch` error and `sitemap_comparisons: 1`. The sitemap time represents `2026-10-09T21:00:00Z`, one hour earlier than the HTML time. Both strings have timezones; timezone presence alone does not make them agree. Different local calendar dates are not themselves an error.

## 2. Two spellings of the same instant

For this fictional exercise, take the existing HTML instant as the intended reference. Save this as `equivalent.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
  <url><loc>https://example.invalid/watch</loc><video:video>
    <video:content_loc>https://example.invalid/film.mp4</video:content_loc>
    <video:publication_date>2026-10-10T01:30:00+03:30</video:publication_date>
  </video:video></url>
</urlset>
```

```sh
python3 video_datetime_lint.py examples/equivalent/utc.html --sitemap equivalent.xml --strict-datetime --require-sitemap-dates --require-video --now 2026-10-10T12:00:00Z --format json
```

Expected: exit `0`, no diagnostics and `sitemap_comparisons: 1`. The XML's `01:30+03:30` and the HTML's previous-day `22:00Z` are the same instant.

For a real publication, first establish the intended timestamp from your publication record, then correct the relevant source or generator. Do not invent a timestamp, change the clock or copy one inconsistent value to another merely to obtain a pass. This tool does not identify which record is historically correct or rewrite either input.

## 3. A successful exit with no comparison

Save this as `unmatched.xml`. Only the video URL differs from the preceding XML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
  <url><loc>https://example.invalid/watch</loc><video:video>
    <video:content_loc>https://example.invalid/another-film.mp4</video:content_loc>
    <video:publication_date>2026-10-10T01:30:00+03:30</video:publication_date>
  </video:video></url>
</urlset>
```

```sh
python3 video_datetime_lint.py examples/equivalent/utc.html --sitemap unmatched.xml --strict-datetime --require-sitemap-dates --require-video --now 2026-10-10T12:00:00Z --format json
```

Expected: exit `0`, one `unmatched_sitemap_video` warning, `sitemap_comparisons: 0` and `skipped_consistency_checks: 1`. The supplied HTML has a VideoObject, so `--require-video` passes, but it is not the video named in this sitemap entry. Strict datetime and required-date policies do not turn an unmatched identity warning into an error.

For real files, inspect whether the HTML input set is incomplete or the exact video URL differs. The tool does not infer identity from the watch-page URL, title or player URL. Do not rename an unrelated video just to suppress the warning. Check diagnostics and comparison counts alongside the exit code.

The fixed `--now` makes these examples repeatable. Omit it to use the current UTC clock in a live publication check, or deliberately choose the clock you intend to assess. Agreement of supplied local metadata does not prove actual publication, delivery, complete schema, indexing or ranking. See [the site-workflow guide](check-your-site.md) for use on your own generated output.
