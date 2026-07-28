# 新日汉拟声拟态词词典 第2版

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Specialized term dictionary |
| Edition | Second edition |
| Revision | `2026.07.28.3` |
| Build | Ready |
| Public ZIP | Rights review |
| Planned asset | `Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip` |

## Features

- original visual hierarchy and colored headwords;
- semantic categories and Japanese–Chinese example styling;
- word-group and related-form links;
- subentries promoted to independently searchable terms;
- dictionary-scoped CSS.

## Download

The catalog entry is public, but the ZIP remains withheld until redistribution rights
for the source dictionary are documented. Once authorized, this page will contain
the direct GitHub Release link, checksum, license, and automatic-update index.

## Local build

```powershell
python scripts/convert_onomatopoeia.py `
  --mdx "<path-to-your-dictionary.mdx>" `
  --output generated/onomatopoeia.ndjson `
  --report generated/onomatopoeia-report.json `
  --resources-dir generated/onomatopoeia-resources

pnpm onomatopoeia:build
python scripts/qa_onomatopoeia.py `
  dictionary-output/Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip
```

The converter preserves the original visual hierarchy, colored headwords and
examples, categories, word-group links, and searchable subentries. Formatting rules
live in `styles/onomatopoeia.css`.

Update `config/onomatopoeia.json` whenever the generated archive changes.
