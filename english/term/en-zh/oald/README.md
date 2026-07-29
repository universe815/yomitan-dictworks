# OALD English–Chinese

## Status

| Edition | Revision | Build | Public ZIP | Planned asset |
| --- | --- | --- | --- | --- |
| Text | `2026.07.29.1` | Ready | Rights review | `OALDPE-En-Cn-2025.02.14-yomitan.zip` |
| Complete illustrated | `2026.07.29.1` | Ready | Rights review | `OALDPE-En-Cn-2025.02.14-yomitan-illustrated.zip` |

## Features

- English–Chinese structured entries and lookup redirects;
- original entry hierarchy and dictionary-scoped styling;
- optional complete illustration packaging;
- separate local MDD audio server to avoid a multi-gigabyte term archive.

## Download

Both editions are listed in the public catalog, but their ZIP files remain withheld
until redistribution rights for the dictionary text and media are documented. Once
authorized, this page will contain direct GitHub Release links, checksums, licenses,
and Yomitan automatic-update indexes.

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
