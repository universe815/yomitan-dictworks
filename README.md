# Yomitan Dictworks

个人维护的 Yomitan 词典目录与可复现转换工具。目录组织参考
[MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries)，
按源语言、词典类型和翻译方向分类；本仓库不使用 GitHub Release，也不提交
本地生成的商业词典 ZIP。

## 词典目录

### 日语

#### 词语词典

##### 日语 → 中文

- [新世纪日汉双解大辞典（完整图文版）](japanese/term/ja-zh/xsjrh/)
  · [更新清单](manifests/xsjrh-illustrated/index.json)
- [新日汉拟声拟态词词典 第2版](japanese/term/ja-zh/onomatopoeia/)
  · [更新清单](manifests/shin-nikkan-onomatopoeia/index.json)

[浏览日语词典目录](japanese/)

### 英语

#### 词语词典

##### 英语 → 中文

- [OALDPE En-Cn 2025.02.14](english/term/en-zh/oald/)
  · [正文版更新清单](manifests/oald-en-zh/index.json)
  · [完整插图版更新清单](manifests/oald-en-zh-illustrated/index.json)

[浏览英语词典目录](english/)

## 自动更新

三部词典都已写入 Yomitan 自动更新元数据。GitHub 仅保存稳定的
`indexUrl`；ZIP 由本机 `127.0.0.1:8765` 提供，不放入仓库或 Release。

启动本地更新服务：

```powershell
python scripts/serve_local_updates.py `
  --output-dir "<dictionary-output-path>"
```

保持窗口运行，然后在 Yomitan 的词典管理页面点击 **Check for Updates**。
首次仍需手动导入对应 ZIP；之后 Yomitan 才能依据内嵌的 `indexUrl` 检查更新。

## 仓库结构

```text
english/term/en-zh/<dictionary>/   英中词语词典说明
japanese/term/ja-zh/<dictionary>/  日中词语词典说明
manifests/<edition>/index.json     Yomitan 更新清单
config/                            构建与更新元数据
scripts/                           转换、质量检查和本地更新服务
styles/                            词典专用样式
dictionary-output/                 本地生成物（Git 忽略）
```

## 本地构建

环境要求：Node.js 20+、pnpm、Python 3.11+。

```powershell
pnpm install --frozen-lockfile
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

具体转换、构建和质量检查命令见每部词典的目录页。

- [添加词典](docs/adding-a-dictionary.md)
- [个人更新流程](docs/publishing.md)
- [机器可读目录](catalog/README.md)
- [词典更新记录](dict-changelog.md)

## 许可与第三方内容

原创代码和文档使用 MIT 许可证。词典正文、例句、图片、音频、字体和品牌等
第三方内容仍受各自权利与许可约束，详见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
