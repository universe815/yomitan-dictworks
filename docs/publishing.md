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
`updateHosting`、`releaseTag` 和 `releaseAssetName`。所有现役词典统一
使用 Release。GitHub 会改写中文资产文件名，因此 Release 的实际文件名
使用稳定 ASCII，日语词典另设中文资产标签；Yomitan 标题和用于手动下载的
ZIP 仍使用中文。

## 首次安装

1. 从 README 或共享 Drive 文件夹下载所需 ZIP。
2. 不要解压 ZIP，也不要导入 `manifests/` 下的 JSON。
3. 在 Yomitan 的 **Dictionaries** 页面选择 **Import**。
4. 以后点击 **Check for Updates** 即可更新。

## 发布一次更新

必须按以下顺序发布，避免清单先更新、ZIP 尚未就绪：

Google Drive 与 GitHub Release 是同一次发布的两个必要通道。两端必须保存
同一个最终 ZIP，并与 catalog 中的 `bytes` 和 `sha256` 一致；任一端尚未
同步完成时，不得提交或合并新版清单。

1. 修改转换器或源数据，并增加对应 config、catalog 与文档中的 `revision`。
2. 重新构建 ZIP并运行专项 QA、Yomitan schema 校验与：

   ```powershell
   python scripts/check_update_archives.py `
     --output-dir "<dictionary-output-path>"
   ```

3. 计算并记录每个 ZIP 的 `bytes` 与 `sha256`。
4. 使用版本化 ASCII 文件名将最终 ZIP 上传到 `dictionary-assets` Release。
   不要覆盖同名资产；每个 revision 使用新的 `releaseAssetName`。日语
   词典通过 `#中文标签` 设置 Release 页面显示名：

   ```powershell
   gh release upload dictionary-assets `
     "<ASCII_ASSET>.zip#<中文词典名>" `
     --repo universe815/yomitan-dictworks
   ```

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
   python scripts/check_public_links.py `
     --local-manifests `
     --full-hash `
     --timeout 120
   ```

9. 等待 PR 的 **Verify public dictionary links** 检查通过；它会重新下载
   Drive 与 Release 两份 ZIP 并核对完整 SHA-256。通过后再合并配置、目录、
   清单和文档；不要提交 ZIP。
10. 使用另一套 Yomitan 配置执行一次真实的 **Check for Updates**。

如果正文和资源没有改变，只迁移或修正更新元数据，可以从已经通过 QA 的
正式 ZIP 生成新版本，避免重新转换第三方源文件：

```powershell
python scripts/repack_update_archive.py `
  --dictionary-id "<catalog-id>" `
  --source "<previous-formal-zip>" `
  --output-dir dictionary-output
```

该命令只替换 ZIP 内的 `index.json`，其余成员保持原有顺序、路径和压缩
方式；生成后仍必须运行完整 ZIP、schema、SHA-256 与公开下载检查。

## Google Drive 目录

公开目录为：

<https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8>

`Downloads/` 保持扁平结构，每个 edition 对应一个可直接导入的 ZIP。文件名
使用语言方向或类型前缀。同步盘脚本仍可用于本地复制和 SHA-256 校验：

```powershell
python scripts/sync_google_drive_archives.py `
  --source-dir "<dictionary-output-path>" `
  --drive-root "<google-drive-yomitan-path>" `
  --dictionary-id "<catalog-id>"
```

重复 `--dictionary-id` 可在一次发布中只同步若干已重新构建的 edition；
省略时同步 catalog 中全部公开词典。

本地 HTTP 服务仅保留给维护者做发布前路由测试，不属于公开更新链路。
