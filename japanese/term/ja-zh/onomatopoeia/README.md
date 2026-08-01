# 新日汉拟声拟态词词典 第2版

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Specialized term dictionary |
| Edition | Second edition |
| Revision | `2026.08.01.2` |
| Build | Ready |
| Update mode | GitHub Release |
| Archive | `新日汉拟声拟态词词典-第2版-Yomitan.zip` |

## Features

- original visual hierarchy and colored headwords;
- semantic categories and Japanese–Chinese example styling;
- a Yomitan-aware dark palette with readable meanings, translations, labels,
  separators, and related-word chips, plus flat host selectors for readers
  exposing `data-theme="dark"`, `data-mode="dark"`, or common dark-mode classes;
- word-group and related-form links;
- subentries promoted to independently searchable terms;
- dictionary-scoped CSS.

## Links and updates

- [Yomitan 更新清单](../../../../manifests/shin-nikkan-onomatopoeia/index.json)
- [下载可直接导入的 ZIP](https://drive.google.com/file/d/1ovhYNnA7g9QP_KSHFCmX0yzCUZWKHppy/view?usp=sharing)
- [Google Drive 下载文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)

下载的 ZIP 可直接导入 Yomitan。Google Drive 继续提供手动下载和归档；
`2026.07.30.1` 及之后版本通过中文命名的 GitHub Release 资产自动更新，
不需要启动本机服务。

## Local build

```powershell
python scripts/convert_onomatopoeia.py `
  --mdx "<path-to-your-dictionary.mdx>" `
  --output generated/onomatopoeia.ndjson `
  --report generated/onomatopoeia-report.json `
  --resources-dir generated/onomatopoeia-resources

pnpm onomatopoeia:build
python scripts/qa_onomatopoeia.py `
  dictionary-output/新日汉拟声拟态词词典-第2版-Yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/新日汉拟声拟态词词典-第2版-Yomitan.zip
```

The converter preserves the original visual hierarchy, colored headwords and
examples, categories, word-group links, and searchable subentries. Formatting rules
live in `styles/onomatopoeia.css`.

Update `config/onomatopoeia.json` whenever the generated archive changes.
