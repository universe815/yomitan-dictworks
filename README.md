# Yomitan Dictworks

个人维护的 Yomitan 词典目录与可复现转换工程。目录组织参考
[MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries)，
构建层使用
[MarvNC/yomichan-dict-builder](https://github.com/MarvNC/yomichan-dict-builder)。
本仓库不使用 GitHub Release，也不提交本地生成的商业词典 ZIP。

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

三部词典都已写入 Yomitan 自动更新元数据。GitHub 保存稳定的
`indexUrl`，ZIP 统一归档到个人 Google Drive；本机更新服务从同步盘读取
ZIP，不放入仓库或 Release。

- [Google Drive：全部可直接导入的 ZIP](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8)
- [个人自动更新说明](docs/publishing.md)
- [添加词典](docs/adding-a-dictionary.md)
- [机器可读目录](catalog/README.md)
- [词典更新记录](dict-changelog.md)

首次需从本地生成目录导入 ZIP；之后启动本机服务并在 Yomitan 中点击
**Check for Updates**。

## 许可与第三方内容

原创代码和文档使用 MIT 许可证。词典正文、例句、图片、音频、字体、商标和
其他第三方内容仍受各自权利与许可约束，详见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
