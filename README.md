# Yomitan Dictworks

面向长期维护的 Yomitan 多词典转换工程。仓库结构参考
[MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries) 的词典门户思路，
构建层使用
[MarvNC/yomichan-dict-builder](https://github.com/MarvNC/yomichan-dict-builder)。

## 词典目录

| 语言 | 词典 | 当前实现 | 发布状态 |
| --- | --- | --- | --- |
| 英语 → 中文 | [OALD 本地转换版](english/en-zh/oald/) | 正文、结构化内容、插图、检索别名、本地音频伴侣 | 仅转换代码 |
| 日语 → 中文 | [新世纪日汉双解大辞典](japanese/ja-zh/xsjrh/) | 日中释义、例句、Ruby、内部链接、插图、外字 | 仅转换代码 |
| 日语 → 中文 | [新日汉拟声拟态词词典](japanese/ja-zh/onomatopoeia/) | 原版层级与配色、词群跳转、子词条检索 | 仅转换代码 |
| 日语 → 中文 | 最小示例词典 | JSON → Yomitan term bank | 可本地构建 |

具体参数见各词典目录中的说明；新增词典见
[docs/adding-a-dictionary.md](docs/adding-a-dictionary.md)。

## 自动更新与发布

构建器支持 Yomitan 的 `isUpdatable`、`indexUrl` 和 `downloadUrl` 字段，但默认关闭。只有在
源数据许可允许再分发、下载地址稳定且 ZIP 已通过检查时才应启用。发布约定与 GitHub Release
流程见 [docs/publishing.md](docs/publishing.md)，远程索引模板见
[manifests/index.template.json](manifests/index.template.json)。

## 仓库约定

- `config/`：构建元数据和本地生成物的相对路径。
- `src/`：将中间数据打包成 Yomitan ZIP 的 TypeScript 代码。
- `scripts/`：MDict 转换、资源提取、QA 与 schema 验证工具。
- `styles/`：随词典打包的 Yomitan scoped CSS。
- `generated/`：本地中间文件，永不提交。
- `dictionary-output/`：本地成品，默认永不提交；可公开发布的成品应放 GitHub Release。
- `manifests/`：可公开词典的远程更新索引。

变更记录见 [dict-changelog.md](dict-changelog.md)。

## 许可与版权

本仓库原创代码使用 MIT License。词典正文、图片、音频、字体、商标及其他第三方内容不因此
获得 MIT 授权；详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。提交词典前必须说明
来源、许可、署名与可否再分发。
