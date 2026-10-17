# QuickFind

**A lightweight, offline instant file search for Windows — with one-key reveal in Directory Opus or File Explorer.**

Type a few characters, hit Enter, done. Right-click a result to jump straight to the original file in your file manager — with the file already selected.

> A small alternative to Listary / Everything, written in ~1,200 lines of dependency-free Python.
> [中文说明](README.zh-CN.md)

---

## Why another file search?

| | QuickFind | Everything | Listary |
|---|---|---|---|
| Instant substring search over a whole-disk index | ✅ | ✅ | ✅ |
| **Reveal & select the file in Directory Opus** | ✅ | ❌ | ⚠️ partial |
| Plain Python, hackable in an afternoon | ✅ | ❌ (closed) | ❌ (closed) |
| No admin rights, no kernel driver, no service | ✅ | ⚠️ needs service | ✅ |
| Index rebuild with live progress + timestamp | ✅ | ✅ | ✅ |
| Multi-language UI (EN / 中文, auto-detect) | ✅ | ⚠️ | ✅ |

QuickFind is **not** the fastest indexer out there — it walks the filesystem with `os.scandir` instead of reading the NTFS MFT. On ~470k files that is a one-off **5 s** index build and **17–56 ms** search. If you need Everything-grade speed with realtime USN tracking, use Everything. If you want something you can read, tweak and integrate with your file manager, this is for you.

## Features

- **Whole-disk index, search-as-you-type** — matches file names *and* full paths; folders included
- **Global hotkey** (default `Ctrl+Shift+/`, freely rebindable — digits, letters, F-keys and symbols all supported)
- **Reveal in your file manager** — Directory Opus (`dopusrt /cmd Go` + `Select`) or File Explorer (`/select`), auto-detected
- **Five themes** — follow system / pure black / dark grey / light / grey
- **X behaviour is configurable** — minimize to taskbar (default) or quit
- **Run at Windows startup** — one checkbox, no registry hunting
- **Clean index** — skips system caches, `node_modules`, virtualenvs, cloud placeholders (`OFFLINE`/`RECALL_ON_*`) and network locations (UNC / mapped drives), so the index stays small and fast
- **Fully offline** — no network calls, no telemetry, no accounts
- **Localisation** — English and Chinese out of the box, auto-detected from the Windows UI language

## Install

### Option A — installer (recommended)

Download `QuickFind-Setup.exe` from [Releases](../../releases) and run it.

It installs to `%LOCALAPPDATA%\Programs\QuickFind`, creates Start Menu + startup shortcuts, registers an uninstall entry, and launches the app. No admin rights needed.

### Option B — portable

Download `QuickFind.exe` and put it in its own folder, e.g. `D:\Tools\QuickFind\`.
Settings and index are written **next to the exe**.

### Option C — from source

```bat
git clone https://github.com/<you>/quickfind.git
cd quickfind
python src\quickfind.py
```

Requires Python 3.10+ with tkinter (bundled in the standard Windows installer). No third-party packages.

### First run

The app builds its index in the background — the status bar shows progress.
Default index root is your home folder. To index more, edit `config.json` (see below) and press `Ctrl+R`.

## Usage

| Action | Result |
|---|---|
| `Ctrl+Shift+/` (global) | Show / hide the window |
| Type | Instant filtering |
| `↑` / `↓` | Move selection |
| `Enter` / double-click | Open with the default program |
| **Right-click** | Reveal in file manager · copy path · copy folder · rebuild index |
| `Ctrl+C` | Copy the full path |
| `Esc` | Hide |
| `Ctrl+R` | Rebuild the index |
| `⚙` (top right) | Theme · language · hotkey · startup · about |

## Configuration

`config.json` lives next to the program (or the exe). A default one is generated on first run.

```jsonc
{
  "roots": ["C:\\Users\\you"],     // folders/drives to index — add "D:\\" etc.
  "exclude_dirs": [                // lowercase substring match on the full path
    "$Recycle.Bin", "System Volume Information", "\\appdata\\",
    "\\node_modules\\", "\\.git\\", "\\__pycache__\\",
    "\\site-packages\\", "\\.venv\\", "onedrive"
  ],
  "hotkey": "ctrl+shift+/",        // ctrl+alt+p, ctrl+shift+0, ctrl+alt+f5 …
  "reveal_app": "auto",           // "auto" | "dopus" | "explorer"
  "dopus_rt_path": "",            // empty = auto-detect Directory Opus
  "lang": "auto",                 // "auto" | "en" | "zh"
  "skin": "dark",                 // auto | black | dark | light | gray
  "close_action": "minimize",     // minimize | quit
  "max_results": 400,
  "rebuild_hours": 12,            // auto-rebuild if the index is older; 0 = never
  "include_dirs": true,
  "exclude_network": true,        // skip UNC paths and network drives
  "follow_dir_links": false
}
```

Anything you change in the UI is written back here.

## Build from source

```powershell
powershell -ExecutionPolicy Bypass -File build\build.ps1
```

Produces `release\QuickFind.exe` (windowed) and `release\QuickFind-Setup.exe` (installer, embeds the first one).

To update an existing installation in place:

```powershell
powershell -ExecutionPolicy Bypass -File build\deploy.ps1
```

## Known limitations

- The index is a **snapshot** — new/removed files show up after the next rebuild (or after `Ctrl+R`)
- **Substring matching only** — no fuzzy matching (`qfk` → `quickfind.py`) or pinyin initials yet
- Does **not** hook the Open/Save dialogs of other apps (that is Listary's signature feature)
- Windows-only (uses `RegisterHotKey`, `GetAsyncKeyState`, `explorer /select`)

## Privacy

QuickFind runs completely offline. It never opens a network connection, collects nothing, and reports nothing.
It only **reads** file name / path size / mtime metadata — it never modifies, moves or deletes your files.

## Troubleshooting

**SmartScreen / antivirus warnings** — the executables are unsigned and PyInstaller one-file builds are sometimes flagged by heuristic scanners. Build from source if you prefer, or use Option C above.

**Hotkey does nothing** — another program already owns it. Open `⚙ → Shortcut key…` and press a different combination; the settings dialog reads the *physical* key state, so any digit, letter, F-key or symbol works.

**A file I know exists is not found** — it is probably outside `roots`, or matches an `exclude_dirs` entry. `tools/check_index_completeness.py` diffs the disk against the index and tells you which rule excluded it.

## License

[MIT](LICENSE) © 2026 FelixHong

Feedback: fghsxp2026@126.com
