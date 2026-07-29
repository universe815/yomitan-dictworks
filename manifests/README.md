# Yomitan 更新清单

每个公开 edition 使用稳定的 `manifests/<id>/index.json`。Yomitan 用
`revision` 判断是否存在新版本，再从公开 HTTPS `downloadUrl` 下载 ZIP。

- `indexUrl`：GitHub Raw 上的稳定清单；
- `downloadUrl`：使用版本化 GitHub Release 资产；实际资产名使用稳定
  ASCII，避免 GitHub 改写中文文件名；
- 用户手动下载页：`drive.google.com/file/d/<id>/view`；
- 完整 ZIP：Google Drive 公开 `Downloads/` 文件夹保留可直接导入和归档
  副本，Release 资产用于稳定自动更新。

新增或更新版本时必须确保词典配置、机器目录、公开清单及 ZIP 内
`index.json` 的 title、revision、indexUrl 和 downloadUrl 完全一致。
同时核对目录记录的文件大小、SHA-256 和远端 ZIP 尾部；不要把清单 JSON
当作词典导入。
