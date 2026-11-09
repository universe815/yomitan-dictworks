# 发布与自动更新

Yomitan 词典的发布流程：版本化 ZIP、稳定清单、匿名校验、目录同步。实现参照 [W1ght/simoneta-yomitan](https://github.com/W1ght/simoneta-yomitan) 的 Release 与 `index.json` 设计。

## 两个通道

- **GitHub Release** `dictionary-assets`：版本化 ASCII 文件名的 ZIP，Yomitan 自动更新从这里下载；
- **Google Drive** `Yomitan Dictionaries/Downloads/`：同一份 ZIP 的扁平副本，用 `[语言方向] 中文名.zip` 命名，供手动下载与归档。

两端必须是同一份字节，且与 `catalog/dictionaries.json` 的 `bytes`、`sha256` 一致。

## URL 结构

ZIP 内 `index.json`、`config/<id>.json`、`manifests/<id>/index.json` 和 catalog 使用同一组：

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/download/dictionary-assets/<ASCII_ASSET>.zip"
}
```

GitHub 会改写中文资产文件名，所以 Release 实际文件名用稳定 ASCII，Yomitan 显示的 `title` 与 Drive 里的 ZIP 仍用中文。

## 发布一次更新

1. 修改转换器或源数据，同步提升 `config/<id>.json`、`catalog/dictionaries.json`、`catalog/build-inventory.json` 里的 `revision`。
2. 重新构建 ZIP，运行专项 QA 与 `scripts/validate_yomitan_schema.py`。
3. 正文与资源未变、只改更新元数据时，从已通过 QA 的正式 ZIP 重新打包，不重跑第三方源：

   ```powershell
   python scripts/repack_update_archive.py `
     --dictionary-id "<catalog-id>" `
     --source "<previous-formal-zip>" `
     --output-dir dictionary-output
   ```

   该命令只替换 ZIP 内的 `index.json`，其余成员的顺序、CRC 与压缩方式保持不变。
4. 计算 `bytes` 与 `sha256`，用版本化 ASCII 文件名上传，每个 revision 一个新资产，不覆盖旧名字：

   ```powershell
   gh release upload dictionary-assets `
     "<ASCII_ASSET>.zip#<中文词典名>" `
     --repo universe815/yomitan-dictworks
   ```

5. 匿名下载资产，核对 Content-Length、SHA-256 与 ZIP 完整性。
6. 从最终 ZIP 提取清单：

   ```powershell
   python scripts/extract_update_index.py `
     "dictionary-output/<archive>.zip" `
     "manifests/<id>/index.json"
   ```

7. 把同一份 ZIP 复制进 Drive（脚本会校验复制后的哈希）：

   ```powershell
   python scripts/sync_google_drive_archives.py `
     --source-dir "<dictionary-output-path>" `
     --drive-root "<google-drive-yomitan-path>" `
     --dictionary-id "<catalog-id>"
   ```

8. 更新 catalog、inventory、README 与 `dict-changelog.md`，然后运行：

   ```powershell
   pnpm check
   python -m compileall -q scripts
   python scripts/check_repository.py
   python scripts/check_catalog.py
   python scripts/check_public_inventory.py
   ```

9. 提交推送，等 CI 通过；用另一套 Yomitan 配置做一次真实的 Check for Updates。

清单在资产与 Drive 副本都就绪之后再提交，避免指向尚不存在的包。多部词典各用 `manifests/<id>/index.json`，不要共用一个 `releases/latest` 附件。

## 资产清理

同一词典只保留最新一个 revision 的资产。发布新版本后删除被替代的旧资产：

```powershell
gh release delete-asset dictionary-assets "<OLD_ASSET>.zip" `
  --repo universe815/yomitan-dictworks --yes
```

旧 revision 仍留在 Git 历史与 `dict-changelog.md` 中，随时可以按需重传。

## Google Drive 目录

公开目录：<https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8>

`Downloads/` 保持扁平结构，每个 edition 一个可直接导入的 ZIP，文件名用语言方向前缀。`scripts/sync_google_drive_archives.py` 只做复制与哈希校验；上传由 Drive 桌面客户端完成。
