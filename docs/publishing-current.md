# 发布与自动更新（2026-11-09 起）

本规范替代旧 `publishing.md` 的全量公开／Drive 双通道要求。完整目录与原创工具公开，正文逐项核验许可。`catalog/build-inventory.json` 为统一清单；旧 `catalog/dictionaries.json` 与 `manifests/` 保留历史五个分发接口兼容性，不代表已通过新的权利核验。

## 目录和工具发布

1. 核对本地 ZIP 的版本、数量、大小和 SHA-256，写入统一目录。
2. 只提交原创转换器、样式、构建配置和不含内容的统计。不提交来源、详细报告、正文 ZIP、MDX/MDD、截图、完整源差异或聊天历史。
3. 运行 TypeScript、Python 编译、仓库、目录检查及 `python scripts/check_public_inventory.py`。
4. 提交推送，等待 CI。可创建明确标为“目录与工具”的 Release；不附未获授权的正文包。

## 获许可的词典包

1. 在统一目录写明具体许可证、权利人依据、数据版本与适用范围，核对媒体及译文并记录署名与修改说明。充分核验后才标记 `redistributionApproved: true`、`status: release-eligible`。
2. 对最终 ZIP 做格式、文本覆盖、媒体、内部链接及使用测试；SHA-256 一致不是内容质量证明。
3. 运行 `python scripts/check_public_inventory.py --dictionary-id <id> --archive <path>`；授权未确认或文件不匹配时失败。
4. 以稳定 ASCII 版本化文件名上传 Release，随附许可证及来源说明，不覆盖旧 revision 附件。
5. 匿名下载核对哈希和大小，然后才在 ZIP 内及仓库清单设置一致的 `isUpdatable`、`indexUrl`、`downloadUrl`。
6. 在独立 Yomitan 配置验证导入与更新后，更新下载入口。

多部词典应使用各自稳定的 `manifests/<id>/index.json` 与版本化资产 URL，避免所有词典共用一个 `releases/latest` 附件导致误更新。

本次用户要求统一到 GitHub，新发布不再强制同步 Drive。现有 Drive 链接是历史链路，本次不安排每日抓取或自动公开任务，不为没有附件的词典建立更新清单。

## GitHub-only 正文发布（2026-11-09 补充）

维护者决定先公开四部已完成的日语正文包，只走 GitHub Release，不建 Drive 副本。这类条目的 `distribution` 使用 `hosting: github-release`，因此不需要 `driveFileId`、`driveFolderUrl`、`driveFileUrl`；`check_catalog.py` 只对 `hosting: google-drive-public` 的条目强制 Drive 字段。统一目录里对应条目的 `publication.status` 记为 `released`，`redistributionApproved` 仍为 `false`——**公开上传是维护者决定，不是许可结论**。

发布顺序（旧 `publishing.md` 仍然适用）：

1. 用 `scripts/repack_update_archive.py` 从已通过 QA 的正式 ZIP 生成新版，只替换 `index.json`，其余成员保持原顺序、CRC 与压缩方式。
2. 以稳定 ASCII 版本化文件名上传，`gh release upload dictionary-assets "<ASSET>.zip#<中文标题>"`，不覆盖旧 revision。
3. 匿名下载核对 Content-Length 与 SHA-256。
4. `scripts/extract_update_index.py` 从最终 ZIP 提取 `manifests/<id>/index.json`。
5. 更新 `catalog/dictionaries.json`、`catalog/build-inventory.json`、README 与 changelog，再提交推送；清单绝不先于资产合并。
6. 在独立 Yomitan 配置验证导入与 **Check for updates**。

已有 Release、Drive 与旧清单未撤回，许可仍需核实。没有新增正文不等于消除了历史分发风险，见 [rights-review.md](rights-review.md)。
