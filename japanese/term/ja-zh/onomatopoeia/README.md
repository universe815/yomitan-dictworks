# 新日汉拟声拟态词词典 第2版

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Specialized term dictionary |
| Edition | Second edition |
| Revision | `2026.07.29.2` |
| Build | Ready |
| Update mode | Google Drive + local server |
| Archive | `Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip` |

## Features

- original visual hierarchy and colored headwords;
- semantic categories and Japanese–Chinese example styling;
- word-group and related-form links;
- subentries promoted to independently searchable terms;
- dictionary-scoped CSS.

## Links and updates

- [Yomitan 更新清单](../../../../manifests/shin-nikkan-onomatopoeia/index.json)
- [下载可直接导入的 ZIP](https://drive.google.com/file/d/1ovhYNnA7g9QP_KSHFCmX0yzCUZWKHppy/view?usp=sharing)
- [Google Drive 下载文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)
- 本机更新地址：
  `http://127.0.0.1:8765/shin-nikkan-onomatopoeia/Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan.zip`

Google Drive 文件夹中的
`[JA-ZH Onomatopoeia] 新日汉拟声拟态词词典 第2版.zip` 可直接导入
Yomitan；之后从同步盘启动本机更新服务并检查更新。

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
