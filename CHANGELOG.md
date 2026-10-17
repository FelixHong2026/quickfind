# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is [SemVer](https://semver.org/).

## [0.9.2 Beta] - 2026-10-17

### Added
- **Proper application icon** — a folder with a magnifier, rendered per size (16/24/32/48/64/128/256)
  instead of the generic Windows placeholder. Used by the tray icon, the window title bar and
  the exe file itself (so Explorer shows it too).
  * each size is rendered from an 8x supersampled source rather than downscaled from 256px,
    which keeps the 16px tray variant legible
  * `assets/quickfind.ico` is bundled with `--add-data`, so the tray can load it at runtime

## [0.9.1 Beta] - 2026-10-17

### Added
- **System tray icon** (`Shell_NotifyIcon` via ctypes, still zero third-party packages).
  Closing the window now hides it to the tray **and keeps the process alive**, so the
  global hotkey keeps working — previously quitting killed the hotkey with it.
  * left-click the tray icon → show / hide
  * right-click → Show QuickFind / About / Quit

### Changed
- `close_action` gains a third value and its default changed from `minimize` to `tray`:
  `tray` (hide to tray) | `minimize` (minimize to taskbar) | `quit`
- The settings menu shows all three options under "When clicking ✕".

### Fixed
- Clicking ✕ looked like it did nothing: the window minimised to the taskbar with no
  obvious feedback, so it was easy to click repeatedly without noticing. Hiding to a
  visible tray icon makes the state obvious.
- The tray icon is removed cleanly on quit (no ghost icon left in the notification area).

## [0.9.0 Beta] - 2026-10-17

First public release.

### Added
- Whole-disk file index built with `os.scandir`, cached in SQLite (471k entries, ~5 s build)
- Search-as-you-type over file names and full paths, folders included (17–56 ms typical)
- Global hotkey summon, default `Ctrl+Shift+/`, rebindable from the UI
- Reveal & select the original file in **Directory Opus** (`dopusrt /cmd Go` + `Select`),
  with automatic fallback to **File Explorer** (`/select`)
- Five themes: follow system / pure black / dark grey / light / grey
- Configurable ✕ behaviour: minimize to taskbar (default) or quit
- "Run at Windows startup" checkbox
- Settings menu (⚙) with theme, language, hotkey, rebuild, program folder, about
- Built-in About panel and MIT licence viewer
- English + Chinese UI with automatic detection of the Windows UI language
- Index protections: skips `AppData`/`node_modules`/`venvs`/`site-packages`/`_gsdata_`,
  cloud placeholders (`OFFLINE`, `RECALL_ON_OPEN`, `RECALL_ON_DATA_ACCESS`),
  UNC paths and network drives
- Single-instance guard, automatic index rebuild after N hours, window geometry memory
- Installer (`QuickFind-Setup.exe`) with Start Menu + startup shortcuts and an uninstall entry
- `tools/` self-check scripts: index completeness diff, hotkey verification, VK A/B test,
  Directory Opus reveal check, UI/i18n self-test

### Fixed during development
- Blanket "do not descend into reparse-point folders" wrongly skipped ordinary folders that
  merely carry the reparse attribute → now only network-pointing or cyclic links are skipped
- Hotkey capture produced a phantom `Alt` (wrong `event.state` bit on Windows) → modifiers are
  now read with `GetAsyncKeyState`
- `Ctrl+Shift+/` / `Ctrl+Shift+0` could not be captured (Tk reports `question` / `parenright`
  for shifted keys, and some combinations never reach the window at all) → capture now polls
  physical key state every 25 ms instead of relying on Tk `<KeyPress>`
- Clicking ✕ killed the process and silently disabled the global hotkey → ✕ behaviour is now
  configurable and defaults to minimize
- Window was permanently topmost, covering other applications → `-topmost` removed

### Known limitations
- Index is a snapshot; changes appear only after the next rebuild
- Substring matching only — no fuzzy matching or pinyin initials
- No hooking of other applications' Open/Save dialogs
