# 新世纪日汉双解大辞典 converter

Status: converter and styles only. No dictionary data, extracted media, or generated
ZIP is distributed.

```powershell
python scripts/convert_xsjrh.py `
  --mdx "<path-to-your-dictionary.mdx>" `
  --mdd "<path-to-your-dictionary.mdd>" `
  --output generated/xsjrh.ndjson `
  --report generated/xsjrh-report.json `
  --resources-dir generated/xsjrh-resources

pnpm xsjrh:build
python scripts/qa_xsjrh.py `
  dictionary-output/XSJRH-2026.07.21-yomitan-illustrated.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/XSJRH-2026.07.21-yomitan-illustrated.zip
```

The pipeline preserves Japanese and Chinese definitions, examples, Ruby annotation,
internal links, lookup redirects, illustrations, and gaiji resources. The QA step
checks representative entries and archive structure; also inspect entries in Yomitan
after every formatting change.

Update `config/xsjrh.json` when the source edition or generated revision changes.
