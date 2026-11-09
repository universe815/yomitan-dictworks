# 明鏡 ことわざ成句使い方辞典

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Japanese |
| Type | Proverbs, idioms, and usage dictionary |
| Revision | `2026.08.13.1` |
| Build | Ready locally |
| Distribution | Published: `Meikyo-Kotowaza-Yomitan-2026.08.13.1.zip` (GitHub Release + Drive) |
| Archive | `明鏡-ことわざ成句使い方辞典-Yomitan.zip` |

## Features

- 5,540 source articles, appendices, and phrase-index entries;
- preserved Ruby, cross-entry links, labels, gaiji replacements, and supplied images;
- restored searchable aliases from the general, misuse, classification, source,
  and idiom indexes;
- original index paths attached to entries in a collapsible block;
- dictionary-scoped CSS with high-contrast Lapis/Anki night-mode fallbacks.

## Local build

```powershell
python scripts/convert_meikyo_kotowaza.py `
  --jsonl "<path-to-dongri_data.jsonl>" `
  --index-tree "<path-to-dongri_index_tree.json>" `
  --images-dir "<path-to-img>" `
  --output generated/meikyo-kotowaza.ndjson `
  --report generated/meikyo-kotowaza-report.json `
  --resources-dir generated/meikyo-kotowaza-resources

pnpm meikyo-kotowaza:build

python scripts/qa_specialized_dictionaries.py `
  meikyo-kotowaza `
  dictionary-output/明鏡-ことわざ成句使い方辞典-Yomitan.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/明鏡-ことわざ成句使い方辞典-Yomitan.zip
```
