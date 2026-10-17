# Reddit —— 发帖文案（英文）

**建议板块**：`r/software`（主战场）· `r/Windows11` · `r/opensource` · `r/coolgithubprojects`
**避开发**：`r/programming`（要求技术深度，容易被骂 self-promo）· `r/Everything`（找打）

**Flair**：`r/software` 选 `Software Release` 或 `Developer`

---

## 版本 A —— r/software（推荐，最完整）

**标题**：
> `QuickFind — I made a free, MIT-licensed file search for Windows that reveals the file in Directory Opus / Explorer (not another Everything clone)`

```text
**Disclosure: I wrote this. It's free, MIT, no telemetry, no account, nothing to buy.**

I wanted one specific thing that nothing quite did: type a few characters,
hit Enter, and land in the right folder **with the file already selected** —
in Directory Opus, not just Explorer.

So I built QuickFind. ~1,200 lines of Python, zero third-party packages.

**What it does**
- Global hotkey summons it (Ctrl+Shift+/ default, fully rebindable)
- Search-as-you-type over a cached index of names *and* full paths
- Right-click → "Reveal in Directory Opus / File Explorer" → navigates there and
  selects the file
- Directory Opus auto-detected; falls back to File Explorer
- 5 themes, EN/中文 UI (auto-detect), configurable ✕ behaviour, run-at-startup
- Skips AppData / node_modules / venvs / cloud placeholders / network drives
  so the index stays small

**What it is NOT**
- Not faster than Everything. Everything reads the NTFS MFT; I walk the
  filesystem. On my machine (471k entries): ~5 s to index, 17-56 ms per search.
  **If you want raw speed, use Everything.**
- The index is a snapshot — new files appear after a rebuild (Ctrl+R or every
  12 h).
- Substring matching only. No fuzzy (`qfk` → `quickfind.py` doesn't work yet),
  no pinyin initials.
- Doesn't hook Open/Save dialogs (Listary's QuickSwitch). Deliberate — I don't
  want to inject into other processes.
- Windows only (uses RegisterHotKey / GetAsyncKeyState / explorer /select).
- Beta (v0.9.0). Binaries are unsigned → SmartScreen will warn. Source is
  right there if you'd rather `python src\quickfind.py`.

**Why open source / why Python**
So you can read it in an afternoon and change it. I don't have a business
model; I have a workflow.

**Links**
- Repo (MIT): https://github.com/FelixHong2026/quickfind
- Download: https://github.com/FelixHong2026/quickfind/releases/latest
- Screenshots in the README

Feedback very welcome — especially from Directory Opus users, since that
integration is the whole reason this exists.
```

---

## 版本 B —— r/Windows11（更短，更"用户向"）

**标题**：
> `Free & open source: press a hotkey, type, and jump straight to the file in Explorer/DOpus — QuickFind (v0.9.0 beta)`

```text
**I made this. Free, MIT, offline, no telemetry.**

The idea: you know the file exists somewhere. You don't want to open Explorer
and click through six folders. You want to type four characters and be *there*.

QuickFind:
- Hotkey (default Ctrl+Shift+/) → search box
- Type → results as you type
- Right-click → "Reveal in File Explorer" (or Directory Opus if installed)
  → folder opens with the file selected
- Enter opens the file, Ctrl+C copies the path
- 5 themes, English + Chinese UI, run-at-startup toggle

Honest limitations: slower than Everything (indexes by walking the filesystem,
not the MFT — ~5 s for 471k files on my machine, 17-56 ms per search), snapshot
index, substring matching only, Windows-only, unsigned binary (SmartScreen will
complain — build it yourself if you prefer).

https://github.com/FelixHong2026/quickfind

Happy to take feature requests, but fair warning: I'd rather keep it small than
add dialog hijacking.
```

---

## 版本 C —— r/opensource 或 r/coolgithubprojects（技术向）

**标题**：
> `QuickFind: a 1,200-line dependency-free Python file search for Windows, with Directory Opus integration (MIT)`

```text
**Disclosure: this is my project.**

A small, deliberately boring Windows file search tool. The point isn't
novelty — it's that you can read the whole thing in an afternoon.

**Design notes that might interest you**
- Index = `os.scandir` walk → SQLite cache. No MFT, no service, no driver,
  no admin rights. Trade-off: slower first index, way simpler to reason about.
- Search = pre-lowercased paths + a C-level list comprehension. 471k entries
  in 17-56 ms, measured.
- Hotkey = `RegisterHotKey` on a dedicated thread (it's thread-affine, so
  rebinding means: post WM_QUIT to the old thread, let its `finally` unregister,
  then start a new one).
- Hotkey *capture* does NOT use Tk's `<KeyPress>`. Two reasons: shifted keys
  report the wrong keysym (`Shift+/` → `question`, `Shift+0` → `parenright`),
  and some combos never reach the window at all. It polls `GetAsyncKeyState`
  every 25 ms across ~90 candidate VKs instead.
- File-manager reveal = shelling out to `dopusrt /cmd Go` + `/cmd Select`, or
  `explorer /select`. No shell extension, nothing injected.
- Index protections: skips cloud placeholders by attribute
  (`OFFLINE`/`RECALL_ON_*`), skips UNC and `DRIVE_REMOTE`, and only skips
  reparse-point folders when they point at a network path or would loop.

`src/` is ~1,200 lines across two files (`quickfind.py`, `quickfind_locales.py`).
MIT. Issues and PRs welcome — fuzzy matching and pinyin initials are the two
things I'd most like help with.

https://github.com/FelixHong2026/quickfind
```

---

## 发布注意

- **标题里必须有 "Disclosure / I made this"** 或 flair 选 Developer —— 否则会被举报 spam
- 第一个版本用 **版本 A**；如果没人理，隔 2-3 天换板块用版本 B 重发（不算刷屏，换板块允许）
- **前 2 小时必须守着回复** —— Reddit 的排序算法看早期互动
- 别在评论区跟 Everything 粉丝吵，一律回"对，Everything 更快，我这个是为了文件管理器集成"
