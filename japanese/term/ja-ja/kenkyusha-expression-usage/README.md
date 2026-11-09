# 研究社 日本語表現活用辞典

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Japanese |
| Type | Collocation and expression usage dictionary |
| Revision | `2026.08.13.1` |
| Build | Ready locally |
| Distribution | Published: `Kenkyusha-Japanese-Expression-Usage-Yomitan-2026.08.13.1.zip` (GitHub Release + Drive) |
| Archive | `研究社-日本語表現活用辞典-Yomitan.zip` |

## Features

- 1,641 structured dictionary articles;
- original kana, orthographic, English, and synonym search aliases;
- collocation patterns, examples, idioms, compounds, and noun usages;
- compact dictionary-scoped CSS with Lapis/Anki night-mode variables.

## Local build

```powershell
python scripts/convert_kenkyusha_expression_usage.py `
  --mdx "<path-to-日本語表現活用辞典.mdx>" `
  --output generated/kenkyusha-expression-usage.ndjson `
  --report generated/kenkyusha-expression-usage-report.json `
  --resources-dir generated/kenkyusha-expression-usage-resources

pnpm kenkyusha-expression-usage:build

python scripts/qa_specialized_dictionaries.py `
  kenkyusha-expression-usage `
  dictionary-output/研究社-日本語表現活用辞典-Yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/研究社-日本語表現活用辞典-Yomitan.zip
```
