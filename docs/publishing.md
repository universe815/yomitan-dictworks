# 个人词典自动更新

本项目不创建 GitHub Release，也不把生成的词典 ZIP 提交到公开仓库。
GitHub 负责保存目录、转换工具和稳定的更新清单；本机负责提供 ZIP。

## URL 结构

每个词典配置同时包含：

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "http://127.0.0.1:8765/<id>/<archive>.zip"
}
```

`indexUrl` 也写入 `manifests/<id>/index.json`。`downloadUrl` 的路径由机器可读
目录中的 `id` 与 `assetName` 组成。

## 首次安装

1. 在本地完成转换、构建和词典专项 QA。
2. 运行：

   ```powershell
   python scripts/check_update_archives.py `
     --output-dir "<dictionary-output-path>"
   ```

3. 手动把 ZIP 导入 Yomitan。只有带 `isUpdatable`、`indexUrl` 和
   `downloadUrl` 的版本才能参与后续自动更新。

## 发布一次个人更新

1. 增加词典 `revision`，不要复用旧版本号。
2. 重新构建 ZIP并完成 QA。
3. 用 `scripts/extract_update_index.py` 从 ZIP 更新对应清单。
4. 运行 `scripts/check_update_archives.py`，确认四个版本的配置、清单与 ZIP
   内元数据一致。
5. 提交目录、配置和清单，不提交 ZIP。
6. 启动本地服务：

   ```powershell
   python scripts/serve_local_updates.py `
     --output-dir "<dictionary-output-path>"
   ```

7. 在 Yomitan 中点击 **Check for Updates**。

本机服务只监听 `127.0.0.1`，其他设备无法访问。需要跨设备使用时，应另外
准备你有权使用的私有 HTTPS 存储，并同步修改配置与清单中的 `downloadUrl`。
