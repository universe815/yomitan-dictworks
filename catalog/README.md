# 机器可读词典目录

`dictionaries.json` 是所有公开 edition 的单一目录源，记录语言方向、类型、
revision、构建命令、Google Drive 文件 ID、用户下载页和 Yomitan 直下载地址。

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
