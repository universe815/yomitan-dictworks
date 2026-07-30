# OALD English–Chinese

## Status

| Edition | Revision | Build | Update mode | Archive |
| --- | --- | --- | --- | --- |
| Text | `2026.07.30.3` | Ready | GitHub Release | `OALDPE-En-Cn-2025.02.14-yomitan.zip` |
| Complete illustrated | `2026.07.30.3` | Ready | GitHub Release | `OALDPE-En-Cn-2025.02.14-yomitan-illustrated.zip` |

## Features

- English–Chinese structured entries and lookup redirects;
- restored inline spacing around collocations, labels, and translations;
- distinct headword, pronunciation, sense, definition, example, topic, idiom,
  and phrasal-verb hierarchy with dictionary-scoped light/dark styling;
- separate visual source markers for original OALD, AI, and Leon Chinese text;
- color-coded native folding for all 18 source module kinds, including extra
  examples, synonyms, Wordfinder, verb forms, collocations, word families,
  British/American usage, grammar, language banks, culture, and Word Origin;
- native folding for Idioms and Phrasal Verbs, with Word Origin expanded by
  default;
- optional complete illustration packaging;
- separate local MDD audio server to avoid a multi-gigabyte term archive.

## Links and updates

- Text edition: [Yomitan 更新清单](../../../../manifests/oald-en-zh/index.json)
  · [下载 ZIP](https://drive.google.com/file/d/1pt7r1-meO8dA4fCfRSMH3R4NKYuOY_Hz/view?usp=sharing)
- Complete illustrated edition:
  [Yomitan 更新清单](../../../../manifests/oald-en-zh-illustrated/index.json)
  · [下载 ZIP](https://drive.google.com/file/d/1ti0TcgrWnjGSd72f3AxoXy1HN7ReIWdu/view?usp=sharing)
- [Google Drive 下载文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)

两个 OALD ZIP 均可直接导入 Yomitan。Google Drive 继续提供手动下载和
归档；`2026.07.30.1` 及之后版本分别通过 GitHub Release 资产自动更新，
不需要启动本机服务。

## Build the text edition

```powershell
python scripts/convert_oald.py `
  --mdx "<path-to-your-oald.mdx>" `
  --output generated/oald-structured.ndjson `
  --report generated/oald-report.json

pnpm oald:build

python scripts/qa_oald.py generated/oald-structured.ndjson
python scripts/qa_oald_archive.py `
  dictionary-output/OALDPE-En-Cn-2025.02.14-yomitan.zip `
  --revision 2026.07.30.3
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

python scripts/qa_oald_archive.py `
  dictionary-output/OALDPE-En-Cn-2025.02.14-yomitan-illustrated.zip `
  --revision 2026.07.30.3 `
  --expect-images 622
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
