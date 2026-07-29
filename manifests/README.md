# Yomitan 更新清单

每个版本有一个稳定的 `manifests/<id>/index.json`。Yomitan 用 `revision`
判断是否存在新版本，再从 `downloadUrl` 取得 ZIP。

本仓库的个人词典采用以下组合：

- `indexUrl`：GitHub Raw 上的稳定清单；
- `downloadUrl`：`http://127.0.0.1:8765/<id>/<archive>.zip`；
- ZIP：保存在本机 `dictionary-output`，由
  [`scripts/serve_local_updates.py`](../scripts/serve_local_updates.py) 提供。

新增版本时从 `index.template.json` 复制清单，并确保清单、词典配置及 ZIP 内
`index.json` 三处元数据完全一致。
