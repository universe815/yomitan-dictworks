# 机器可读词典目录

`dictionaries.json` 是所有公开 edition 的单一目录源，记录语言方向、类型、
revision、构建命令、文件大小、SHA-256、Google Drive 归档信息和 Yomitan
自动更新地址。

分发字段分成两层：

- `hosting`、`driveFileId`、`driveFileUrl` 和 `archivePath`：面向用户的
  Google Drive 手动下载及归档副本；
- `updateHosting`、`indexUrl` 和 `downloadUrl`：Yomitan 自动更新链路。
  所有现役版本使用 `github-release`，并记录 `releaseTag` 与版本化
  `releaseAssetName`。Release 实际文件名使用 ASCII；日语词典可以另记
  中文 `releaseAssetLabel`，Yomitan 的 `title` 与手动下载 ZIP 使用中文。

分发状态：

- `public`：公开 ZIP、稳定更新清单和 HTTPS 自动更新地址均已配置；
- `retired`：停止向新用户提供，且不得保留活动下载或更新字段。

`rightsStatus` 独立描述第三方内容状态：

- `third-party`：版权归第三方，本仓库不主张授权或隶属关系；
- `licensed`：存在可核验的公开许可或书面授权；
- `public-domain`：内容已确认属于公有领域。

`status: public` 只描述技术可访问性，不等同于版权许可。`rightsStatement`
必须如实显示；标记为 `licensed` 时还必须提供 `contentLicense` 和
`rightsEvidence`。
