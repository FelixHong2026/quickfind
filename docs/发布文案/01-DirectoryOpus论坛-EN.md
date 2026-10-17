# Directory Opus 官方论坛 —— 发帖文案（英文）

**发帖板块**：https://resource.dopus.com/ → 建议 `General Discussion` 或 `Tips & Tricks`（不要发到 Feature Requests）
**标题（推荐）**：

> `[Utility] QuickFind — instant file search that reveals & selects in Opus (MIT, open source)`

**备选标题**：

- `Made a free search tool that jumps straight into an Opus lister — feedback wanted`
- `QuickFind: type, hit Enter, land in the right folder with the file already selected`

---

## 正文（直接复制）

```text
Hi all,

Long-time Opus user here. One thing I kept wanting: a search box that doesn't
just *find* a file, but puts me in front of it — in Opus, with the file already
selected.

So I wrote one. It's called QuickFind, it's MIT licensed, and it's about 1,200
lines of dependency-free Python.

WHAT IT DOES
  • Global hotkey (Ctrl+Shift+/ by default, rebindable — digits, letters,
    F-keys and symbols all work)
  • Type a few characters, results appear as you type
  • Right-click a result → "Reveal in Directory Opus"
      → Opus navigates to the containing folder and selects the file
  • Matches both file names and full paths, folders included
  • Index is cached locally, so startup is instant

HOW THE OPUS INTEGRATION WORKS
  It shells out to dopusrt:
      dopusrt.exe /cmd Go "<parent folder>"
      dopusrt.exe /cmd Select "<file name>"
  Nothing is injected into Opus, no shell extension, no DLL — if Opus isn't
  installed it falls back to explorer /select. So it can't destabilise your
  Opus install.

THE HONEST BIT
  • It is NOT fast like Everything. Everything reads the NTFS MFT; I walk the
    filesystem with os.scandir. On my machine (471k entries) the index takes
    about 5 seconds and searches take 17-56 ms. Everything will beat it.
  • The index is a snapshot — new files show up after the next rebuild
    (Ctrl+R, or automatically every 12 hours).
  • Substring matching only. No fuzzy matching, no pinyin initials yet.
  • It does NOT hook Open/Save dialogs (Listary's QuickSwitch). That's a
    deliberate choice — I didn't want to inject into other processes.
  • Beta. v0.9.0. Expect rough edges.
  • The binaries are unsigned, so Windows SmartScreen will complain. Source is
    all there if you'd rather run `python src\quickfind.py` or build it
    yourself.

WHAT I'D LIKE FROM YOU
  I built this for my own workflow with Opus, so I'm probably blind to how
  others use it. Specifically curious about:
    • Do you want the selection behaviour configurable (left vs right lister,
      new tab vs current tab, split)?
    • Would a "reveal in the *other* pane" option be useful?
    • Any Opus command I should be calling instead of Go + Select?

LINKS
  Repo (MIT): https://github.com/FelixHong2026/quickfind
  Download:   https://github.com/FelixHong2026/quickfind/releases/latest
  Screenshots are in the README.

Happy to answer anything, and thanks for reading.
```

---

## 发布后注意

- **Opus 论坛的人会关注"会不会搞坏我的 Opus 配置"** —— 文案里已经强调"只调 dopusrt，不注入、不扩展"，别删掉这段
- 如果他们给了更好的 Opus 命令（比如用 `Go` 的某个参数直接带选中），**立刻采纳并回复**，这是最容易赢得社区好感的动作
- 如果有人说"我用 Everything + 快捷键就够了" —— 别争，回一句"对，Everything 更快，我这边主要是为了 Opus 集成"，保持体面
