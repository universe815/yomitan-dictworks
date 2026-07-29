# Yomitan 更新清单

每个公开 edition 使用稳定的 `manifests/<id>/index.json`。Yomitan 用
`revision` 判断是否存在新版本，再从公开 HTTPS `downloadUrl` 下载 ZIP。

- `indexUrl`：GitHub Raw 上的稳定清单；
- `downloadUrl`：Google Drive 的匿名 ZIP 直下载地址；
- 用户下载页：`drive.google.com/file/d/<id>/view`；
- ZIP：Google Drive 公开 `Downloads/` 文件夹中的可直接导入文件。

新增或更新版本时必须确保词典配置、机器目录、公开清单及 ZIP 内
`index.json` 的 title、revision、indexUrl 和 downloadUrl 完全一致。
不要把清单 JSON 当作词典导入。
