# AlternativeTo / GitHub 元信息 / Release Notes（英文）

---

## 一、AlternativeTo

**提交地址**：https://alternativeto.net/manage/add-app/
**关键**：一定要挂到「作为替代品」的关系上 —— 那是流量来源

### 基础字段

| 字段 | 填写内容 |
|---|---|
| **Name** | `QuickFind` |
| **License** | `Open Source (MIT)` |
| **Platform** | `Windows` |
| **Application type** | `File Manager` / `Search tool` |
| **Homepage** | `https://github.com/FelixHong2026/quickfind` |
| **Tags** | `file-search` `launcher` `desktop-search` `productivity` `keyboard-shortcut` `directory-opus` |

### Tagline（一句话，≤90 字符）

> `Offline instant file search for Windows that reveals & selects files in Directory Opus or Explorer.`

### Description

```text
QuickFind is a small, offline file search tool for Windows. Press a hotkey,
type a few characters, and results appear as you type. What sets it apart is
the last step: right-click a result and it opens your file manager at that
folder with the file already selected — Directory Opus if installed, otherwise
File Explorer.

It builds its index by walking the filesystem (no NTFS MFT, no service, no
driver, no admin rights), caches it in SQLite, and searches 470k+ entries in
17-56 ms on the author's machine. The first index takes a few seconds.

Deliberately narrow: no fuzzy matching yet, no hooking of Open/Save dialogs,
Windows only. MIT licensed, ~1,200 lines of dependency-free Python, readable
in an afternoon.

  • Global hotkey, freely rebindable (digits / letters / F-keys / symbols)
  • Matches file names and full paths, folders included
  • Reveal & select in Directory Opus or File Explorer
  • 5 themes, English + Chinese UI (auto-detected)
  • Configurable ✕ behaviour, run-at-Windows-startup toggle
  • Skips AppData, node_modules, virtualenvs, cloud placeholders and network drives
  • Fully offline: no telemetry, no network calls
```

### 应挂的 "alternative to"（重要）

```
Listary
Everything (voidtools)
Wox
Flow Launcher
Keypirinha
Launchy
```

### 应挂的 "alternative of"（反向，几乎没人做）

```
Directory Opus  ← 如果 AlternativeTo 有这个条目，挂上
```

---

## 二、GitHub 仓库元信息（已配置，供核对 / 改版用）

### About 描述（当前已设置）

```text
A lightweight, offline instant file search for Windows - one-key reveal in Directory Opus or File Explorer.
```

### Topics（当前已设置 9 个）

```text
file-search  launcher  windows  python  tkinter
listary-alternative  directory-opus  productivity  desktop-search
```

### 建议补充：Social preview 图片

GitHub → Settings → General → Social preview
**上传 1280×640 的图**，否则分享到 Twitter/Discord/Reddit 时是一张灰底空白卡。

制作建议：用 `docs/screenshots/01-main-en.jpg` 缩放居中，左侧加一行大字
`QuickFind` + 一行小字 `Instant search · reveal in DOpus`。任何图片工具都行。

### 命令（改描述/加 topics）

```powershell
Set-Location "E:\数据中心\软件中心\HugeSoft\程序开发\QuickFind"
gh repo edit --description "A lightweight, offline instant file search for Windows - one-key reveal in Directory Opus or File Explorer."
gh repo edit --add-topic file-search --add-topic directory-opus
```

---

## 三、Release Notes 模板（下一个版本直接用）

**打 tag 前**：把下面内容写进 `CHANGELOG.md`，CI 会自动用它生成 Release 正文
（工作流里开了 `generate_release_notes: true`，会同时附上 commit 列表）。

### 模板

```markdown
## What's changed

### Added
- <新功能 1>
- <新功能 2>

### Fixed
- <修了什么问题>（描述现象 → 原因 → 现在怎样）

### Changed
- <行为变化>（⚠️ 破坏性变更要单独标出来）

### Known issues
- <已知未修的问题>

**Full changelog**: https://github.com/FelixHong2026/quickfind/compare/vPREV...vNEW

---

### Install
- **Installer** (recommended): `QuickFind-Setup.exe`
- **Portable**: `QuickFind.exe` — settings and index are written next to the exe
- **From source**: `python src\quickfind.py`

> Binaries are unsigned, so Windows SmartScreen may warn you. Build from source
> if you'd rather not run them.
```

### 发版命令

```powershell
Set-Location "E:\数据中心\软件中心\HugeSoft\程序开发\QuickFind"

# 1) 改 CHANGELOG.md
# 2) 本地构建验证
powershell -ExecutionPolicy Bypass -File build\build.ps1
powershell -ExecutionPolicy Bypass -File build\deploy.ps1

# 3) 提交
git add -A
git commit -m "chore(release): v0.9.1"
git push origin main

# 4) 打 tag → CI 自动构建 + 发 Release
git tag -a v0.9.1 -m "QuickFind v0.9.1"
git push origin v0.9.1

# 5) 盯 CI
gh run watch
```

---

## 四、发布后可以追加的小动作

| 动作 | 成本 | 收益 |
|---|---|---|
| 在 README 顶部加 Shields 徽章（release / license / platform） | 5 分钟 | 提升可信度 |
| 提 `winget` 包（windows-package-manager 仓库） | 半小时 | 安装门槛降为一行命令 |
| 给项目加 `.github/ISSUE_TEMPLATE` | 10 分钟 | issue 质量明显提升 |
| 录 5 秒 GIF 放 README 顶部 | 20 分钟 | **对转化率影响最大** |

### Shields 徽章（贴 README 顶部）

```markdown
[![Release](https://img.shields.io/github/v/release/FelixHong2026/quickfind?include_prereleases&style=flat-square)](https://github.com/FelixHong2026/quickfind/releases)
[![License](https://img.shields.io/github/license/FelixHong2026/quickfind?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D4?style=flat-square)](#)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square)](#)
```
