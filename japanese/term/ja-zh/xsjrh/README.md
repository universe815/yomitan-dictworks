# 新世纪日汉双解大辞典

## Status

| Item | Value |
| --- | --- |
| Direction | Japanese → Chinese |
| Type | Term dictionary |
| Edition | Complete illustrated edition |
| Revision | `2026.07.29.2` |
| Build | Ready |
| Update mode | Google Drive + local server |
| Archive | `XSJRH-yomitan-illustrated.zip` |

## Features

- Japanese and Chinese definitions and examples;
- Ruby annotation and internal query links;
- searchable aliases;
- encyclopedia illustrations, gaiji, and bundled font resources;
- Yomitan structured content and dictionary-scoped CSS.

## Links and updates

- [Yomitan 更新清单](../../../../manifests/xsjrh-illustrated/index.json)
- [下载可直接导入的 ZIP](https://drive.google.com/file/d/1X_TOhkLsxOaTd_7ATWKpUq_WbxnO9rRa/view?usp=sharing)
- [Google Drive 下载文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)
- 本机更新地址：
  `http://127.0.0.1:8765/xsjrh-illustrated/XSJRH-yomitan-illustrated.zip`

Google Drive 文件夹中的 `[JA-ZH] 新世纪日汉双解大辞典（完整图文版）.zip`
可直接导入 Yomitan；之后从同步盘启动本机更新服务并检查更新。

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
