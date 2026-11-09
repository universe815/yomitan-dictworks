# 机器可读词典目录

`dictionaries.json` 是所有已发布 edition 的单一目录源，记录语言方向、类型、revision、构建命令、文件大小、SHA-256、Drive 归档信息和 Yomitan 自动更新地址。

分发字段：

- `hosting`、`archivePath`、`driveFolderUrl`：面向用户的手动下载与归档副本；
- `updateHosting`、`indexUrl`、`downloadUrl`：Yomitan 自动更新链路。现役版本统一 `github-release`，并记录 `releaseTag` 与版本化 `releaseAssetName`。Release 实际文件名用 ASCII，日语词典另记中文 `releaseAssetLabel`；Yomitan 的 `title` 与 Drive 里的 ZIP 用中文。

分发状态：

- `public`：ZIP、稳定更新清单和 HTTPS 自动更新地址都已配置；
- `retired`：不再向新用户提供，且不保留活动下载或更新字段。

`rightsStatus` 描述内容来源：`third-party`（版权归第三方）、`licensed`（有可核验的公开许可或书面授权）、`public-domain`。`rightsStatement` 如实说明归属。

发布时 Drive 副本与 GitHub Release 资产必须是同一份字节，并与 catalog 的 `bytes`、`sha256` 一致。
