# 研究社 日本語口語表現辞典［第2版］

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Japanese |
| Type | Colloquial expression dictionary |
| Edition | Second edition |
| Revision | `2026.08.08.1` |
| Build | Ready locally |
| Distribution | Pending redistribution authorization |
| Archive | `研究社-日本語口語表現辞典-第2版-Yomitan.zip` |

## Features

- 3,335 dictionary articles plus the original front matter and appendices;
- searchable kana, orthographic variants, punctuation variants, and aliases;
- definitions, usage patterns, explanations, notation notes, and dialogue examples;
- Ruby readings and resolved cross-entry links;
- the supplied cover image;
- dictionary-scoped CSS with Lapis/Anki night-mode variables.

## Local build

```powershell
python scripts/convert_kenkyusha_colloquial.py `
  --mdx "<path-to-日本語口語表現辞典［第二版］.mdx>" `
  --cover "<path-to-日本語口語表現辞典［第二版］.png>" `
  --output generated/kenkyusha-colloquial.ndjson `
  --report generated/kenkyusha-colloquial-report.json `
  --resources-dir generated/kenkyusha-colloquial-resources

pnpm kenkyusha-colloquial:build

python scripts/qa_kenkyusha_colloquial.py `
  dictionary-output/研究社-日本語口語表現辞典-第2版-Yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/研究社-日本語口語表現辞典-第2版-Yomitan.zip
```

The source dictionary's copyright page states that its data is protected and may
not be reproduced or redistributed except where legally permitted. The generated
archive is therefore not enabled for public distribution or automatic updates
without documented redistribution authorization.
