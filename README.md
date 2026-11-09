# Yomitan Dictworks

个人维护的 Yomitan 词典转换与发布仓库：**13 部作品、14 个版本**，其中 9 个可直接导入的 ZIP 已发布，装好后能在 Yomitan 里一键检查更新。OALD 正文版与插图版分别计数；《最新日米口語辞典》为文字预览版。

- [机器可读目录](catalog/dictionaries.json)：语言方向、修订号、构建命令、字节数与 SHA-256、更新地址。
- [统一清单](catalog/build-inventory.json)：14 个成品的版本、规模与发布状态。
- [发布规范](docs/publishing.md)、[本地构建](docs/local-builds.md)、[第三方声明](THIRD_PARTY_NOTICES.md)。

## 下载

可直接导入的 ZIP 都在 [`dictionary-assets` Release](../../releases/tag/dictionary-assets)，按版本号命名，只用最新版：

| 词典 | 修订号 | ZIP |
| --- | --- | --- |
| 新世纪日汉双解大辞典（完整图文版） | `2026.08.11.1` | `XSJRH-yomitan-illustrated-2026.08.11.1.zip` |
| 新日汉拟声拟态词词典 第2版 | `2026.08.07.1` | `Shin-Nikkan-Gisei-Gitai-Dictionary-2nd-yomitan-2026.08.07.1.zip` |
| OALDPE En-Cn 2025.02.14（正文版） | `2026.08.02.1` | `OALDPE-En-Cn-2025.02.14-text-2026.08.02.1.zip` |
| OALDPE En-Cn 2025.02.14（完整插图版） | `2026.08.02.2` | `OALDPE-En-Cn-2025.02.14-illustrated-2026.08.02.2.zip` |
| 複合動詞レキシコン〔NINJAL〕 | `2026.08.04.1` | `VVLexicon-NINJAL-yomitan-2026.08.04.1.zip` |
| 研究社 日本語口語表現辞典［第2版］ | `2026.11.09.1` | `Kenkyusha-Japanese-Colloquial-Expressions-2nd-Yomitan-2026.11.09.1.zip` |
| 現代日本語副詞用法辞典（中文版） | `2026.11.09.1` | `Modern-Japanese-Adverb-Dictionary-zh-2026.11.09.1.zip` |
| 研究社 日本語表現活用辞典 | `2026.11.09.1` | `Kenkyusha-Japanese-Expression-Usage-Yomitan-2026.11.09.1.zip` |
| 明鏡 ことわざ成句使い方辞典 | `2026.11.09.1` | `Meikyo-Kotowaza-Yomitan-2026.11.09.1.zip` |

同一份最终 ZIP 也放在公开 Drive 目录 [`Yomitan Dictionaries/Downloads/`](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)，文件名带语言方向前缀（`[JA-JA]`、`[JA-ZH]`、`[EN-ZH]`），字节数与 SHA-256 和 Release 资产一致，供手动下载与归档。

## 安装

1. 下载所需 ZIP（**不要解压**，也不要导入 `manifests/` 下的 JSON）。
2. Yomitan → **Dictionaries** → **Import** → 选择该 ZIP。
3. 之后在同一页面点 **Check for updates** 即可检查更新。

## 自动更新

每个 ZIP 内的 `index.json` 都带 `isUpdatable: true` 和指向本仓库的 `indexUrl`、`downloadUrl`：

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/download/dictionary-assets/<ASCII_ASSET>.zip"
}
```

`manifests/<id>/index.json` 从最终 ZIP 内提取，标题、修订号、URL 与 `catalog/dictionaries.json`、`config/<id>.json` 完全一致；资产先上传并做匿名下载与 SHA-256 校验，再提交清单，避免清单指向尚不存在的包。每部词典用自己的稳定清单和版本化资产，不共用 `releases/latest`。

## 已制作清单

| 词典 / 版本 | 修订号 | 检索记录 | 发布 |
| --- | --- | ---: | --- |
| 新世纪日汉双解大辞典（完整图文版） | `2026.08.11.1` | 457,696 | 已发布 |
| 新日汉拟声拟态词词典 第2版 | `2026.08.07.1` | 2,151 | 已发布 |
| OALDPE En-Cn 2025.02.14（正文版） | `2026.08.02.1` | 618,938 | 已发布 |
| OALDPE En-Cn 2025.02.14（完整插图版） | `2026.08.02.2` | 618,938 | 已发布 |
| 複合動詞レキシコン〔NINJAL〕 | `2026.08.04.1` | 3,280 | 已发布 |
| 研究社 日本語口語表現辞典［第2版］ | `2026.11.09.1` | 7,162 | 已发布 |
| 現代日本語副詞用法辞典（中文版） | `2026.11.09.1` | 2,222 | 已发布 |
| 研究社 日本語表現活用辞典 | `2026.11.09.1` | 3,527 | 已发布 |
| 明鏡 ことわざ成句使い方辞典 | `2026.11.09.1` | 10,996 | 已发布 |
| 现代日语形容词用法词典（中文版） | `2026.11.09.1` | 3,203 | 仅本地 |
| 研究社 類義語使い分け辞典 | `2026.11.09.1` | 10,363 | 仅本地 |
| 最新日米口語辞典［決定版］（文字预览版） | `2026.11.09.1` | 17,552 | 仅本地 |
| 日本語基本動詞バンク〔NINJAL・网页快照〕 | `2026.11.09.1` | 1,642 | 仅本地 |
| 日本語格助詞バンク〔NINJAL・用例版〕 | `2026.11.09.1` | 217 | 仅本地 |

“检索记录”包括表记、读音、别名或重定向，不能直接当作独立释义数。数值来自实际成品和已核对的 QA，不表示全部内容均经人工校订，也不表示已在所有 Yomitan 客户端实测。

## 来源与限制

- 新增现代形容词、研究社類義語使い分け、日米口语转换器保留现有正文；日米源缺项明确记为预览。
- [基本动词](https://www2.ninjal.ac.jp/basicverbbank/)网页快照：754 个词头、2162 义项、9199 例句、672 张活用表；官网介绍的 800 词不作为已取得数量。
- [格助词](https://www2.ninjal.ac.jp/caseparticlebank/)网页 JSON：9 种格助词、95 个语义角色组、10771 条分类用例。31 处普通文本与振假名字段差异保留原文两种写法。
- 《日本語使い分け辞典》《日本語源辞典》《新明解日汉双解第五版》仍缺完整来源，没有算入成品。

## 构建

```bash
pnpm install
pnpm xsjrh:build        # 每部词典一个 <id>:build 脚本，见 package.json
python scripts/validate_yomitan_schema.py dictionary-output/<archive>.zip
```

转换器、样式与构建配置都在本仓库；源数据不进 Git。详见 [docs/local-builds.md](docs/local-builds.md) 与各词典页面的构建命令。

发布方式参照 [W1ght/simoneta-yomitan](https://github.com/W1ght/simoneta-yomitan) 的说明结构、版本化 Release 与更新元数据设计。

## 版权

词典词条、释义、例句、图像、音频与字体的版权归各自权利人所有；本仓库只做格式转换与发布，不主张对这些内容的所有权，也不代表任何出版方。MIT 许可证仅覆盖本仓库原创代码与文档，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
