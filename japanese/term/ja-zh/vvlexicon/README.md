# 複合動詞レキシコン〔NINJAL〕

## 状态

| 项目 | 值 |
| --- | --- |
| 方向 | 日语 → 中文 |
| 类型 | 复合动词词典 |
| 来源 | [NINJAL 官方词典](https://www2.ninjal.ac.jp/vvlexicon/about.html) |
| 收录 | 2,759 条正文；另含 521 条检索跳转 |
| 构建 | 本地转换版 |
| Revision | `2026.08.04.1` |
| 公开分发 | GitHub Release + Google Drive |

## 内容

- 日文词头、读音、动词结构与自他动词标签；
- 日文释义，以及简体中文、繁体中文、英文、韩文译文；
- 句型、日文例句、译文和罗马字；
- 相关形式、类义词、反义词、名词形、注记和 NLB 编号；
- 词条级 CSS，支持明暗主题。

## 下载与更新

- [下载可直接导入的 ZIP](https://drive.google.com/file/d/1FYfk02zZuuuegz-OkGWgLdwM4u2WUpQs/view?usp=sharing)
- [Yomitan 更新清单](../../../../manifests/vvlexicon/index.json)
- [Google Drive 下载文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)

这是非官方转换版；原始资料及其使用条件以 NINJAL 官方说明为准。本项目与原机构无隶属关系，请仅在符合当地法律并拥有合法内容来源的前提下使用。

## 本地构建

官网搜索页把完整词条数组作为 `headwords.js` 提供给前端。可以先运行下面的脚本取得当前网页源文件，然后运行转换和构建：

```powershell
pwsh -File scripts/fetch_vvlexicon_source.ps1

node scripts/convert_vvlexicon.mjs `
  --source data/vvlexicon/headwords.js `
  --output generated/vvlexicon.ndjson `
  --report generated/vvlexicon-report.json

pnpm vvlexicon:build
python scripts/qa_vvlexicon.py `
  dictionary-output/複合動詞レキシコン-NINJAL-Yomitan.zip
python scripts/validate_yomitan_schema.py `
  dictionary-output/複合動詞レキシコン-NINJAL-Yomitan.zip
```

当前版本同时生成公开更新清单、GitHub Release 资产和 Google Drive 归档副本。NINJAL 原始资料的权利与使用条件仍以官方说明为准；本项目不主张取得额外授权。
