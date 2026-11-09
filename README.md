# Yomitan Dictworks

截至 2026-11-09，已制作并核对 **13 部词典、14 个版本**。OALD 正文版和插图版分别计数；《最新日米口語辞典》为文字预览版。

本仓库汇总转换器、构建方法、版本、规模和 SHA-256。仓库维护者决定先公开**四部已完成转换的中日／日日语词典正文包**（明鏡ことわざ、現代副詞、研究社表現活用、研究社口語），发布在 `dictionary-assets` Release，并按 [W1ght/simoneta-yomitan](https://github.com/W1ght/simoneta-yomitan) 的方式在 ZIP 内写入 `isUpdatable`、`indexUrl`、`downloadUrl`，装好后可在 Yomitan 里直接 **Check for updates**。

其余十部成品仍只公开工具、目录与哈希：商业词典未提供可核验的再分发授权；三项 NINJAL 网页资料的许可范围仍待确认。来源可访问、个人已持有文件、标注原作者或放在 Release，都不等于获得公开再分发许可——四部已发布包的第三方内容权利状态同样未核验，见[版权核验记录](docs/rights-review.md)。

- [完整机器目录](catalog/build-inventory.json)：14 个本地成品的版本、大小、哈希及发布状态。
- [本次发布说明](docs/release-2026-11-09.md)：上传内容、已知限制及历史资产状态。
- [版权核验记录](docs/rights-review.md)与[第三方声明](THIRD_PARTY_NOTICES.md)。
- [本地构建](docs/local-builds.md)与[发布规范](docs/publishing-current.md)。

## 已制作清单

| 词典 / 版本 | 修订号 | 检索记录 | 状态 |
| --- | --- | ---: | --- |
| 新世纪日汉双解大辞典（完整图文版） | `2026.08.11.1` | 457,696 | 本地构建已核对；仅公开工具及元数据 |
| 新日汉拟声拟态词词典 第2版 | `2026.08.07.1` | 2,151 | 本地构建已核对；仅公开工具及元数据 |
| OALDPE En-Cn 2025.02.14（正文版） | `2026.08.02.1` | 618,938 | 本地构建已核对；仅公开工具及元数据 |
| OALDPE En-Cn 2025.02.14（完整插图版） | `2026.08.02.2` | 618,938 | 本地构建已核对；仅公开工具及元数据 |
| 複合動詞レキシコン〔NINJAL〕 | `2026.08.04.1` | 3,280 | 本地构建已核对；仅公开工具及元数据 |
| 研究社 日本語口語表現辞典［第2版］ | `2026.08.08.1` | 7,162 | 已发布正文 ZIP（`dictionary-assets`） |
| 現代日本語副詞用法辞典（中文版） | `2026.08.13.1` | 2,222 | 已发布正文 ZIP（`dictionary-assets`） |
| 研究社 日本語表現活用辞典 | `2026.08.13.1` | 3,527 | 已发布正文 ZIP（`dictionary-assets`） |
| 明鏡 ことわざ成句使い方辞典 | `2026.08.13.1` | 10,996 | 已发布正文 ZIP（`dictionary-assets`） |
| 现代日语形容词用法词典（中文版） | `2026.11.09.1` | 3,203 | 本地构建已核对；仅公开工具及元数据 |
| 研究社 類義語使い分け辞典 | `2026.11.09.1` | 10,363 | 本地构建已核对；仅公开工具及元数据 |
| 最新日米口語辞典［決定版］（文字预览版） | `2026.11.09.1` | 17,552 | 文字预览；仅公开工具及元数据 |
| 日本語基本動詞バンク〔NINJAL・网页快照〕 | `2026.11.09.1` | 1,642 | 本地构建已核对；仅公开工具及元数据 |
| 日本語格助詞バンク〔NINJAL・用例版〕 | `2026.11.09.1` | 217 | 本地构建已核对；仅公开工具及元数据 |

“检索记录”包括表记、读音、别名或重定向，不能直接当作独立释义数。数值来自实际成品和已核对的 QA，不表示全部内容均经人工校订，也不表示已在所有 Yomitan 客户端实测。

## 来源与限制

- 新增现代形容词、研究社類義語使い分け、日米口语转换器保留现有正文；日米源缺项明确记为预览。
- [基本动词](https://www2.ninjal.ac.jp/basicverbbank/)网页快照：754 个词头、2162 义项、9199 例句、672 张活用表；官网介绍的 800 词不作为已取得数量。
- [格助词](https://www2.ninjal.ac.jp/caseparticlebank/)网页 JSON：9 种格助词、95 个语义角色组、10771 条分类用例。31 处普通文本与振假名字段差异保留原文两种写法。
- 《日本語使い分け辞典》《日本語源辞典》《新明解日汉双解第五版》仍缺完整来源，没有算入成品。

## 下载与更新

可直接导入的正文 ZIP 在 [`dictionary-assets` Release](../../releases/tag/dictionary-assets) 下，按版本号命名，最新四部：

| 词典 | Release 资产 |
| --- | --- |
| 明鏡 ことわざ成句使い方辞典 | `Meikyo-Kotowaza-Yomitan-2026.08.13.1.zip` |
| 現代日本語副詞用法辞典（中文版） | `Modern-Japanese-Adverb-Dictionary-zh-2026.08.13.1.zip` |
| 研究社 日本語表現活用辞典 | `Kenkyusha-Japanese-Expression-Usage-Yomitan-2026.08.13.1.zip` |
| 研究社 日本語口語表現辞典［第2版］ | `Kenkyusha-Japanese-Colloquial-Expressions-2nd-Yomitan-2026.08.08.1.zip` |

### 首次安装

1. 从上面的 Release 下载所需 ZIP（**不要解压**，也不要导入 `manifests/` 下的 JSON）。
2. Yomitan → **Dictionaries** → **Import** → 选择该 ZIP。
3. 之后在同一页面点 **Check for updates** 即可检查更新。

### 自动更新

每个 ZIP 内的 `index.json` 都带 `isUpdatable: true` 和指向本仓库的 `indexUrl`、`downloadUrl`：

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/download/dictionary-assets/<ASCII_ASSET>.zip"
}
```

`manifests/<id>/index.json` 从最终 ZIP 内提取，标题、修订号、URL 与 `catalog/dictionaries.json` 和 `config/<id>.json` 完全一致；资产上传后先做匿名下载与 SHA-256 校验，再提交清单，避免清单指向尚不存在的包。多部词典各用自己的稳定清单，不共用 `releases/latest`。

参照 [W1ght/simoneta-yomitan](https://github.com/W1ght/simoneta-yomitan) 的说明结构、Release 版本与更新元数据设计；没有复制其实现，也没有把其版权声明当作本项目内容的授权。GitHub 自动生成的 Source code ZIP 是项目源码，不能导入 Yomitan。

仓库已有 `dictionary-assets` Release、历史 Drive 链接及旧更新清单。**这些历史公开资产的权利状态也尚未证实，本次未删除或撤回它们。** `catalog/dictionaries.json` 保留旧发布链路兼容元数据，不是新的授权清单。权利人如需报告问题，可通过仓库 Issues 提供涉及作品和资产信息；请勿公开个人敏感证明材料。

## 代码许可

本仓库原创代码和文档依现有 MIT 许可证发布。MIT 不覆盖第三方词条、例句、图片、音频、字体及商标。来源记录和工具公开不能保证不存在版权争议，详见第三方声明。
