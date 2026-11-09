# 再分发许可核验（2026-11-09）

本记录说明实际找到的依据与未解决事项，不承诺“无版权风险”。13 部词典、14 个版本中，2026-11-09 维护者决定先公开四部已完成包的正文（明鏡成句、现代副词、研究社表达活用、研究社口语），对应条目记为 `publication.status: released`；其余十部仍为 `metadata-and-tools-only`。`released` 只说明文件已公开上传，不表示取得再分发许可，这些包随时可能因权利人异议而撤回。

| 内容组 | 现有证据 | 本次处理 |
| --- | --- | --- |
| OALD、新世纪、新日汉拟声拟态、研究社口语／表达活用／類義語、现代副词／形容词、明鏡成句、日米口语 | 书名、源版本、本地成品和转换记录；未提供覆盖再分发的许可。口语辞典源版权页另有复制与再分发限制说明 | 发布兼容性说明、原创转换器、统计与哈希；不上传原 MDX/MDD、正文、媒体或可恢复全文的报告 |
| NINJAL 複合動詞レキシコン | [官网](https://www2.ninjal.ac.jp/vvlexicon/about.html)、[仓库记录](https://repository.ninjal.ac.jp/records/2000261) | 网页可公开访问；无法据此推断改编或再分发许可。仓库与随附说明访问失败，待核验 |
| NINJAL 基本動詞バンク | [官网](https://www2.ninjal.ac.jp/basicverbbank/about.html)、[数据集](https://doi.org/10.15084/0002000614) | 当前包来自网站快照，未证实仓库许可覆盖网站增补、活用表和全部文本；不发布正文 |
| NINJAL 格助詞バンク | [官网](https://www2.ninjal.ac.jp/caseparticlebank/about/)、[数据集](https://doi.org/10.15084/0002000644) | 当前包来自网页使用的 JSON，仓库 readme 访问返回 503；待确认数据范围和许可 |

## 参考项目的适用范围

[simoneta-yomitan 的 README](https://github.com/W1ght/simoneta-yomitan/blob/main/README.md) 展示了 Release 下载、版本化 ZIP 和 Yomitan 更新字段，也声明词条权利归上游。它不向本项目授予任何其他词典的再分发权。该仓库当前未提供明确代码 LICENSE，因此这里只参考发布方式，不复制其实现。

[GitHub 的许可说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) 解释了缺少许可证时的默认权利状态。仅加署名、免责声明、非盈利说明或把文件从 Git 移到 Release，均不能作为本项目的再分发授权依据。

## 后续放行需要记录什么

在 `catalog/build-inventory.json` 对应项中记录具体许可证名称、可访问的权利人许可依据、适用数据版本与范围，并确认文本、译文、图片、音频、外字和字体均被覆盖或已排除。完成要求的署名、修改说明及许可证随附后，才将 `redistributionApproved` 设为 `true`。

核验正文 ZIP 时运行 `python scripts/check_public_inventory.py --dictionary-id <id> --archive <path>`。当前条目会被拒绝；不能为了通过检查填写没有证据的许可证。

## 历史资产

仓库已有 `dictionary-assets` Release、公开 Drive 链接和五个旧版更新接口，旧目录含 `contentLicense: null`、`rightsEvidence: null`。旧发布行为不构成授权证据。

本轮没有删除、撤回或重写这些外部资产及 Git 历史；因此尚不能声称已消除既有分发风险。需要另行核实其授权，或决定撤回历史分发。撤下当前链接也不能保证移除下载者副本或历史缓存。

## 2026-11-09 正文公开发布（维护者决定）

维护者要求把已完成的四部日语包直接公开在 `dictionary-assets` Release。执行结果记录如下，避免把“已上传”误读成“已授权”：

| 词典 | 发布资产 | 权利状态 |
| --- | --- | --- |
| 明鏡 ことわざ成句使い方辞典 | `Meikyo-Kotowaza-Yomitan-2026.08.13.1.zip` | 第三方内容，许可未核验 |
| 現代日本語副詞用法辞典（中文版） | `Modern-Japanese-Adverb-Dictionary-zh-2026.08.13.1.zip` | 同上 |
| 研究社 日本語表現活用辞典 | `Kenkyusha-Japanese-Expression-Usage-Yomitan-2026.08.13.1.zip` | 同上 |
| 研究社 日本語口語表現辞典［第2版］ | `Kenkyusha-Japanese-Colloquial-Expressions-2nd-Yomitan-2026.08.08.1.zip` | 同上；源版权页另有复制与再分发限制说明 |

对应条目的 `redistributionApproved` 保持 `false`、`contentLicense` 与 `rightsEvidence` 保持 `null`，因此 `check_public_inventory.py --dictionary-id ... --archive ...` 对这些包仍按“许可未确认”失败——这是预期行为，不应通过填假许可证绕过。若权利人提出异议，撤下对应 Release 资产并同步删除 `manifests/<id>/index.json` 与 catalog 条目。