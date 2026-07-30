# OALD 英音 / 美音本地音频

OALD 词典 ZIP 不内嵌数 GB 音频。仓库中的本地伴侣直接读取用户已有的
`oaldpe.mdx` 和配套 `oaldpe*.mdd`，在 `127.0.0.1:5051` 向 Yomitan
提供原词典英音与美音。

这与 Yomitan 的工作方式一致：词条旁只有一个统一扬声器按钮；普通点击按
音频来源顺序播放首个有效来源，右键扬声器可以手动选择具体来源。词典正文
不能嵌入可访问本机文件的自定义 JavaScript 播放按钮。

## 1. 准备运行环境

在仓库根目录运行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. 启动 OALD 音频

```powershell
.\scripts\start_oald_audio_server.ps1 `
  -OaldDirectory '<OALD folder>'
```

首次启动会从 MDX 生成本地词头—音频索引，之后直接复用。看到
`Listening on http://127.0.0.1:5051/` 后保持该 PowerShell 窗口开启。
源文件发生变化时可加 `-RebuildIndex`。

## 3. 配置 Yomitan

打开 **Settings → Audio → Configure audio playback sources**，添加两个
`Custom URL (JSON)` 来源：

```text
http://127.0.0.1:5051/?term={term}&reading={reading}&accent=UK
http://127.0.0.1:5051/?term={term}&reading={reading}&accent=US
```

- 想默认播放英音：UK 放在 US 上面。
- 想默认播放美音：US 放在 UK 上面。
- 想临时选择另一口音：右键词条旁的扬声器，选择 `OALD UK` 或
  `OALD US`。
- 原有 `127.0.0.1:5050` 日语音频来源可以保留；两个服务端口不同，不会
  冲突。

也可以只添加下面这一条，让一个来源同时返回英音和美音：

```text
http://127.0.0.1:5051/?term={term}&reading={reading}
```

分成 UK / US 两条更便于固定默认口音和设置后备顺序。

## 4. 验证

服务运行时在浏览器打开：

```text
http://127.0.0.1:5051/?term=language&accent=UK
http://127.0.0.1:5051/?term=language&accent=US
```

两页都应返回 `type: "audioSourceList"`，并分别列出 `OALD UK` 与
`OALD US`。随后在 Yomitan 查询 `language`，测试普通点击与右键选择。

命令行完整性测试：

```powershell
.\.venv\Scripts\python.exe scripts\oald_audio_server.py `
  --index generated\oald-audio-index.json `
  --mdd '<OALD folder>\oaldpe.mdd' `
  --mdd '<OALD folder>\oaldpe.1.mdd' `
  --mdd '<OALD folder>\oaldpe.2.mdd' `
  --mdd '<OALD folder>\oaldpe.3.mdd' `
  --self-test language `
  --require-accent UK `
  --require-accent US
```

## `server260223` 的作用

`server260223` 是 Anki 的 Local Audio Server 补丁，监听 5050，并新增
OALD10 索引格式支持。补丁自身没有 OALD 音频；它仍需要另外放入包含
`index.json` 与 `media/` 的 `oald10_files`。本项目的 5051 方案无需先把
数 GB 音频解包成该目录，直接读取现有 MDD，也不会覆盖已有日语音频插件。

参考：

- [Yomitan 官方音频说明](https://yomitan.wiki/advanced/#audio)
- [Yomitan 官方 Anki 音频字段说明](https://yomitan.wiki/anki/)
- [英语沉浸式制卡教程](https://kenshelter.com/blog/2026-01-27-english-immersion-card-making/)
