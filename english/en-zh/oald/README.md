# OALD local converter

Status: converter and styles only. No dictionary data or generated ZIP is distributed.

## Build the text edition

```powershell
python scripts/convert_oald.py `
  --mdx "<path-to-your-oald.mdx>" `
  --output generated/oald-structured.ndjson `
  --report generated/oald-report.json

pnpm oald:build
```

## Build the illustrated edition

Use `--include-images`, place the referenced image files in
`generated/oald-images/`, and check that
`generated/oald-rich-report.json` reports the expected image set.

```powershell
python scripts/convert_oald.py `
  --mdx "<path-to-your-oald.mdx>" `
  --output generated/oald-rich.ndjson `
  --report generated/oald-rich-report.json `
  --include-images

pnpm oald:build:rich
```

The current rich builder preserves structured entries, redirects, and PNG/JPEG/SVG
illustrations. Audio is intentionally served separately to avoid embedding several
gigabytes in the term dictionary:

```powershell
python scripts/build_oald_audio_index.py `
  --mdx "<path-to-your-oald.mdx>" `
  --output generated/oald-audio-index.json `
  --report generated/oald-audio-report.json

python scripts/oald_audio_server.py `
  --index generated/oald-audio-index.json `
  --mdd "<path-to-your-first-audio.mdd>" `
  --mdd "<path-to-your-second-audio.mdd>" `
  --self-test example
```

The source product and media are third-party content. Keep all source files,
extracted images, reports, indexes, and ZIP outputs local.
