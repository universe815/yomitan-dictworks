# 現代日本語副詞用法辞典（中文版）

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Adverb usage dictionary |
| Revision | `2026.08.13.1` |
| Build | Ready locally |
| Distribution | Local use only; redistribution rights not documented |
| Archive | `现代日本语副词用法辞典-Yomitan.zip` |

## Features

- 972 structured dictionary articles;
- kana and kanji search forms;
- grouped Japanese examples with Chinese translations;
- usage analysis, comparisons, warnings, Ruby readings, references, and page numbers;
- dictionary-scoped CSS with high-contrast Lapis/Anki night-mode fallbacks.

## Local build

```powershell
python scripts/convert_modern_adverb.py `
  --json "<path-to-现代日本语副词用法辞典.json>" `
  --output generated/modern-adverb.ndjson `
  --report generated/modern-adverb-report.json `
  --resources-dir generated/modern-adverb-resources

pnpm modern-adverb:build

python scripts/qa_specialized_dictionaries.py `
  modern-adverb `
  dictionary-output/现代日本语副词用法辞典-Yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/现代日本语副词用法辞典-Yomitan.zip
```

The generated archive is intended for personal local use by someone who already
has a lawful source copy. Public redistribution and automatic updates remain
disabled unless redistribution rights are documented.
