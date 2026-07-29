# 新日汉拟声拟态词词典 第2版

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Specialized term dictionary |
| Edition | Second edition |
| Revision | `2026.07.29.2` |
| Build | Ready |
| Update mode | Personal local server |
| Archive | `Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip` |

## Features

- original visual hierarchy and colored headwords;
- semantic categories and Japanese–Chinese example styling;
- word-group and related-form links;
- subentries promoted to independently searchable terms;
- dictionary-scoped CSS.

## Links and updates

- [Yomitan 更新清单](../../../../manifests/shin-nikkan-onomatopoeia/index.json)
- 本机更新地址：
  `http://127.0.0.1:8765/shin-nikkan-onomatopoeia/Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip`

本仓库只提供词典目录、转换工具和更新清单，不提供 ZIP。首次从本地
`dictionary-output` 导入；之后启动本地更新服务并在 Yomitan 中检查更新。

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
