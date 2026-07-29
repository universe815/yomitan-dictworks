# 公开词典发布与自动更新

本项目的所有现役词典均采用公开模式：

- GitHub 保存目录、转换器、配置和稳定更新清单；
- Google Drive 保存每个版本可直接导入的完整 ZIP，供手动下载和归档；
- GitHub Release 保存供 Yomitan 自动更新使用的版本化 ZIP 资产；
- Yomitan 通过 GitHub `indexUrl` 检查 revision，通过公开 HTTPS
  `downloadUrl` 下载新版；
- 用户不需要运行本机服务器。

## URL 结构

每个 ZIP 内的 `index.json`、`config/<id>.json`、
`manifests/<id>/index.json` 和 `catalog/dictionaries.json` 必须使用同一组：

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/download/dictionary-assets/<VERSIONED_ASSET>.zip"
}
```

README 面向用户链接 `https://drive.google.com/file/d/<DRIVE_FILE_ID>/view`；
Yomitan 的 `downloadUrl` 使用 GitHub Release 资产。机器目录同时记录
`updateHosting`、`releaseTag` 和 `releaseAssetName`。尚未迁移的旧条目仍可
暂时使用 Drive 更新地址，但新发布和新修订应使用 Release。

## 首次安装

1. 从 README 或共享 Drive 文件夹下载所需 ZIP。
2. 不要解压 ZIP，也不要导入 `manifests/` 下的 JSON。
3. 在 Yomitan 的 **Dictionaries** 页面选择 **Import**。
4. 以后点击 **Check for Updates** 即可更新。

## 发布一次更新

必须按以下顺序发布，避免清单先更新、ZIP 尚未就绪：

1. 修改转换器或源数据，并增加对应 config、catalog 与文档中的 `revision`。
2. 重新构建 ZIP并运行专项 QA、Yomitan schema 校验与：

   ```powershell
   python scripts/check_update_archives.py `
     --output-dir "<dictionary-output-path>"
   ```

3. 计算并记录每个 ZIP 的 `bytes` 与 `sha256`。
4. 使用版本化文件名将最终 ZIP 上传到 `dictionary-assets` Release。不要
   覆盖同名资产；每个 revision 使用新的 `releaseAssetName`。
5. 匿名下载 Release 资产，核对 Content-Length、SHA-256 和 ZIP 完整性。
6. **覆盖原 Google Drive 文件的内容，不要删除后重新上传。** 保持
   `driveFileId` 不变，并验证 Drive 文件大小和公开权限。
7. 从最终 ZIP 提取清单：

   ```powershell
   python scripts/extract_update_index.py `
     "<dictionary-output-path>/<archive>.zip" `
     "manifests/<id>/index.json"
   ```

8. 运行完整检查：

   ```powershell
   pnpm check
   python -m compileall -q scripts
   python scripts/check_repository.py
   python scripts/check_catalog.py
   python scripts/check_public_links.py
   ```

9. 提交并合并配置、目录、清单和文档；不要提交 ZIP。
10. 使用另一套 Yomitan 配置执行一次真实的 **Check for Updates**。

## Google Drive 目录

公开目录为：

<https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8>

`Downloads/` 保持扁平结构，每个 edition 对应一个可直接导入的 ZIP。文件名
使用语言方向或类型前缀。同步盘脚本仍可用于本地复制和 SHA-256 校验：

```powershell
python scripts/sync_google_drive_archives.py `
  --source-dir "<dictionary-output-path>" `
  --drive-root "<google-drive-yomitan-path>"
```

本地 HTTP 服务仅保留给维护者做发布前路由测试，不属于公开更新链路。
