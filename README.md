# Yomitan 词典目录

目录呈现方式主要参考
[W1ght/yomitan-guide](https://github.com/W1ght/yomitan-guide) 与
[MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries)；
转换层使用
[MarvNC/yomichan-dict-builder](https://github.com/MarvNC/yomichan-dict-builder)。

---

## 核心入口

| 资源 | 用途 | 链接 |
|---|---|---|
| Google Drive 公开下载目录 | 全部可直接导入 Yomitan 的完整 ZIP | [打开文件夹](https://drive.google.com/drive/folders/1Hm-Qt2CHAoqkG_k5G40cowWYgE-7CWT8) |
| 词典更新记录 | 版本号、格式修复与资源变更 | [dict-changelog.md](dict-changelog.md) |
| 机器可读目录 | 文件 ID、公开下载地址与构建配置 | [catalog/dictionaries.json](catalog/dictionaries.json) |
| 发布流程 | 构建、验证、上传与自动更新步骤 | [docs/publishing.md](docs/publishing.md) |
| 添加词典 | 新增公开词典的目录和质量要求 | [docs/adding-a-dictionary.md](docs/adding-a-dictionary.md) |
| OALD 英美音 | 用现有 MDX/MDD 为 Yomitan 提供 OALD UK/US 原声音频 | [docs/oald-audio.md](docs/oald-audio.md) |
| Yomitan | 浏览器扩展与官方格式说明 | <https://yomitan.wiki/> |

---

## 日语词典

### 日中 / 双语

| 词典 | 说明 | 获取 | 自动更新 |
|---|---|---|---|
| [新世纪日汉双解大辞典（完整图文版）](japanese/term/ja-zh/xsjrh/) | 日中双解；保留例句、Ruby、内部链接、百科插图、外字与字体资源 | [下载 ZIP](https://drive.google.com/file/d/1X_TOhkLsxOaTd_7ATWKpUq_WbxnO9rRa/view?usp=sharing) | [更新清单](manifests/xsjrh-illustrated/index.json) |
| [新日汉拟声拟态词词典 第2版](japanese/term/ja-zh/onomatopoeia/) | 拟声拟态词专项；保留原版层级、配色、分类、词群关系和独立子词条检索 | [下载 ZIP](https://drive.google.com/file/d/1ovhYNnA7g9QP_KSHFCmX0yzCUZWKHppy/view?usp=sharing) | [更新清单](manifests/shin-nikkan-onomatopoeia/index.json) |

[浏览日语分类目录](japanese/)

---

## 英语词典

### 英中 / 双语

| 词典 | 类型 | 说明 | 获取 | 自动更新 |
|---|---|---|---|---|
| [OALDPE En-Cn 2025.02.14（正文版）](english/term/en-zh/oald/) | 英中学习词典 | 完整正文与检索别名；紧凑 CEFR 徽章、可查询的 Idioms / Phrasal Verbs 入口，以及按类型配色的义项、翻译、例句、搭配、词族、辨析和可展开栏目；英美原声由本地音频伴侣提供 | [下载 ZIP](https://drive.google.com/file/d/1pt7r1-meO8dA4fCfRSMH3R4NKYuOY_Hz/view?usp=sharing) | [更新清单](manifests/oald-en-zh/index.json) |
| [OALDPE En-Cn 2025.02.14（完整插图版）](english/term/en-zh/oald/) | 英中学习词典 / 图文 | 同版式的完整正文、检索别名、导航与特色栏目，并含 622 张原版插图；支持本地 OALD UK/US 原声音频 | [下载 ZIP](https://drive.google.com/file/d/1ti0TcgrWnjGSd72f3AxoXy1HN7ReIWdu/view?usp=sharing) | [更新清单](manifests/oald-en-zh-illustrated/index.json) |

[浏览英语分类目录](english/)

---

## 安装与自动更新

1. 从上表下载所需的完整 ZIP；不要解压，也不要下载或导入更新清单 JSON。
2. 打开 Yomitan 设置中的 **Dictionaries**，选择 **Import** 并导入 ZIP。
3. 以后在同一页面点击 **Check for Updates**。词典会从 GitHub 读取最新
   revision，再从 GitHub Release 下载新版 ZIP。

四个现役版本从 `2026.07.30.1` 起全部使用 GitHub Release 自动更新；
Google Drive 继续提供首次安装、手动下载和归档。更新清单只是 Yomitan
的机器接口，首次安装仍必须导入 ZIP。

---

## 项目结构

GitHub 仓库保存公开目录、转换器、样式、配置、测试和稳定更新清单；生成的
词典 ZIP 不提交到 Git。Google Drive 保存手动下载与归档副本，GitHub
Release 保存 Yomitan 自动更新所需的版本化资产。

```text
<源语言>/<类型>/<语言方向>/<词典>/
config/       构建与公开更新元数据
manifests/    Yomitan 稳定更新清单
scripts/      转换、QA、发布和公开链接检查
styles/       词典专用样式
```

原创代码和文档使用 MIT 许可证。第三方词典正文、例句、图片、音频、字体、
商标及其他内容不包含在该许可证中，详见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
