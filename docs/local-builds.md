# 本地构建已制作词典

使用 Python 3.12+ 安装 `requirements.txt`，Node 构建器另需 Node 20+ 和项目指定 pnpm：

```shell
python -m pip install -r requirements.txt
pnpm install --frozen-lockfile
```

先准备自己有权使用的源文件。仓库不附第三方正文、MDX、MDD、OCR 或网页快照。

## 既有转换器

- [新世纪](../japanese/term/ja-zh/xsjrh/README.md)
- [拟声拟态](../japanese/term/ja-zh/onomatopoeia/README.md)
- [OALD 两版](../english/term/en-zh/oald/README.md)
- [复合动词](../japanese/term/ja-zh/vvlexicon/README.md)
- [研究社口语](../japanese/term/ja-ja/kenkyusha-colloquial/README.md)
- [现代副词](../japanese/term/ja-zh/modern-adverb/README.md)
- [研究社表达活用](../japanese/term/ja-ja/kenkyusha-expression-usage/README.md)
- [明鏡成句](../japanese/term/ja-ja/meikyo-kotowaza/README.md)

旧页面中的公开下载描述属于历史配置，不能用来证明再分发授权；当前统一状态以 `catalog/build-inventory.json` 为准。

## 新增五个版本

| 转换目标 | 准备文件／来源 | 命令 |
| --- | --- | --- |
| 现代形容词 | `sources/modern-adjective.mdx`；[来源说明](https://forum.freemdict.com/t/topic/43714) | `python scripts/build_modern_adjective.py` |
| 研究社類義語 | `sources/ruigigo.mdx`、`ruigigo.mdd`；[来源说明](https://forum.freemdict.com/t/topic/43916) | `python scripts/build_additional.py ruigigo` |
| 日米口语文字预览 | `sources/nichibei.mdx`、`nichibei-original.mdx`；[来源说明](https://forum.freemdict.com/t/topic/44009/6) | `python scripts/build_additional.py nichibei` |
| 基本动词、格助词 | 使用 PowerShell 7 运行 `scripts/Download-NinjalBanks.ps1` 缓存官网公开文件 | `python scripts/build_ninjal_banks.py verbs cases` |

产物写入 `dictionary-output/`，详细源问题和预览写入 `reports/`，这两个目录及 `sources/` 均不公开提交。源码中的源网址是溯源信息，不是权利保证。

脚本中的固定修订号对应本次已审查快照；更新源文件后必须人工提升修订号并复核统计、源差异及许可，不能仅运行抓取脚本就自动发布新包。
