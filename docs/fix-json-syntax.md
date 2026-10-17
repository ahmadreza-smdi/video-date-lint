# Fix a JSON syntax error before checking video dates

This walkthrough uses fictional teaching data and the source revision that includes physical HTML line diagnostics. Older tagged archives may report only JSON-relative positions. It does not describe an actual video or publication.

## 1. Reproduce the error

From the utility repository root, save this exact text as `broken.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Fictional video date example</title>
  <script
    type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Fictional teaching video"
  "uploadDate": "2026-10-09T22:00:00Z",
  "contentUrl": "https://example.com/fictional-video.mp4"
}
  </script>
</head>
<body><p>Fictional teaching example; no video is hosted here.</p></body>
</html>
```

Run with a fixed clock so the example is reproducible:

```sh
python3 video_datetime_lint.py broken.html --format json --now 2026-10-10T00:00:00Z --require-video
```

The command exits with code `2` and an `invalid_jsonld` diagnostic at `script[1]`. Because no video can be read from the broken JSON, `--require-video` also reports `no_video_objects`. The syntax diagnostic message includes `HTML line 12, JSON column 3`.

Line 12 is where the JSON parser detected the problem. The missing comma is at the end of the preceding `name` line, line 11. The line number counts from the beginning of the HTML file; the column counts within the JSON line. In this example, the HTML and JSON line numbers differ because the script begins below the page header and its opening tag spans two lines.

## 2. Repair the comma

Save this version as `fixed.html`. The only change is the comma after `"Fictional teaching video"`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Fictional video date example</title>
  <script
    type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "Fictional teaching video",
  "uploadDate": "2026-10-09T22:00:00Z",
  "contentUrl": "https://example.com/fictional-video.mp4"
}
  </script>
</head>
<body><p>Fictional teaching example; no video is hosted here.</p></body>
</html>
```

Run the same check against the repaired file:

```sh
python3 video_datetime_lint.py fixed.html --format json --now 2026-10-10T00:00:00Z --require-video
```

It exits with code `0`, finds one video, and reports no diagnostics. The tool reads files without repairing or rewriting them. Edit your own input, then rerun the command; do not remove a script simply to hide its error.

## 3. Read the result narrowly

Fixing JSON lets the date checks run. A passing result does not establish that the video URL exists, that the timestamp is its real publication time, or that the page meets every structured-data requirement or will be indexed. This example contains no real video file and makes no network request.

Duplicate keys and other custom validation errors retain script-block diagnostics without a guessed physical line. For other warning and error examples, see [the worked examples](../examples/EXAMPLES.txt); for publication-workflow use, see [the site guide](check-your-site.md).
