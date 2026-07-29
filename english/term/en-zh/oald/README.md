# OALD English–Chinese

## Status

| Edition | Revision | Build | Update mode | Archive |
| --- | --- | --- | --- | --- |
| Text | `2026.07.29.2` | Ready | Google Drive + local server | `OALDPE-En-Cn-2025.02.14-yomitan.zip` |
| Complete illustrated | `2026.07.29.2` | Ready | Google Drive + local server | `OALDPE-En-Cn-2025.02.14-yomitan-illustrated.zip` |

## Features

- English–Chinese structured entries and lookup redirects;
- original entry hierarchy and dictionary-scoped styling;
- optional complete illustration packaging;
- separate local MDD audio server to avoid a multi-gigabyte term archive.

## Links and updates

- Text edition: [Yomitan 更新清单](../../../../manifests/oald-en-zh/index.json)
  · [Google Drive](https://drive.google.com/file/d/1OnmPmRFtpCtaNUGszWlxyQB3tPBSQr5j/view)
- Complete illustrated edition:
  [Yomitan 更新清单](../../../../manifests/oald-en-zh-illustrated/index.json)
  · [Google Drive](https://drive.google.com/file/d/1dGChYanOf3V5Hum8GwSj0YalkJg_2owT/view)

本机更新地址分别为：

- `http://127.0.0.1:8765/oald-en-zh/OALDPE-En-Cn-2025.02.14-yomitan.zip`
- `http://127.0.0.1:8765/oald-en-zh-illustrated/OALDPE-En-Cn-2025.02.14-yomitan-illustrated.zip`

ZIP 归档在 Google Drive 的 `en-zh/OALDPE En-Cn/`。本仓库只提供词典目录、
转换工具和更新清单；之后从同步盘启动本机更新服务并在 Yomitan 中检查更新。

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
