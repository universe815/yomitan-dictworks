# 新世纪日汉双解大辞典

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Term dictionary |
| Edition | Complete illustrated edition |
| Revision | `2026.07.29.1` |
| Build | Ready |
| Public ZIP | Rights review |
| Planned asset | `XSJRH-yomitan-illustrated.zip` |

## Features

- Japanese and Chinese definitions and examples;
- Ruby annotation and internal query links;
- searchable aliases;
- encyclopedia illustrations, gaiji, and bundled font resources;
- Yomitan structured content and dictionary-scoped CSS.

## Download

The catalog entry is public, but the generated archive is not yet offered because a
redistribution license for the source dictionary and embedded media has not been
documented. Once authorized, this page will contain the direct GitHub Release link,
checksum, license, and automatic-update index.

## Local build

```powershell
python scripts/convert_xsjrh.py `
  --mdx "<path-to-your-dictionary.mdx>" `
  --mdd "<path-to-your-dictionary.mdd>" `
  --output generated/xsjrh.ndjson `
  --report generated/xsjrh-report.json `
  --resources-dir generated/xsjrh-resources

pnpm xsjrh:build
python scripts/qa_xsjrh.py `
  dictionary-output/XSJRH-yomitan-illustrated.zip

python scripts/validate_yomitan_schema.py `
  dictionary-output/XSJRH-yomitan-illustrated.zip
```

The pipeline preserves Japanese and Chinese definitions, examples, Ruby annotation,
internal links, lookup redirects, illustrations, and gaiji resources. The QA step
checks representative entries and archive structure; also inspect entries in Yomitan
after every formatting change.

Update `config/xsjrh.json` when the source edition or generated revision changes.
