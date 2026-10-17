# -*- coding: utf-8 -*-
"""QuickFind UI strings / locales.

Add a language by copying the "en" dict and translating the values.
Keys must stay identical across languages; missing keys fall back to English.
"""
import os

# ---------------------------------------------------------------- strings

EN = {
    # window / columns
    "app_name": "QuickFind",
    "win_title": "QuickFind — {hotkey}",
    "col_name": "Name",
    "col_dir": "Location",

    # result context menu
    "reveal_in": "Reveal in {app}",
    "fm_explorer": "File Explorer",
    "fm_dopus": "Directory Opus",
    "reveal_explorer": "Reveal in File Explorer (fallback)",
    "open_default": "Open with default program",
    "copy_path": "Copy full path",
    "copy_folder": "Copy containing folder",
    "reindex": "Rebuild index",
    "hide_bg": "Hide to background",
    "quit": "Quit QuickFind",

    # settings menu
    "skin": "Theme",
    "hotkey": "Shortcut key…",
    "open_program_dir": "Open program folder",
    "autostart": "Run at Windows startup",
    "close_action": "When clicking ✕",
    "close_minimize": "Minimize to taskbar",
    "close_quit": "Quit the program",
    "language": "Language",
    "lang_auto": "Follow system",
    "about": "About QuickFind…",

    # skins
    "skin_auto": "Follow system",
    "skin_black": "Pure black",
    "skin_dark": "Dark grey (default)",
    "skin_light": "Light",
    "skin_gray": "Grey",

    # status bar
    "st_empty": "Index is empty — right-click → Rebuild index",
    "st_indexed": "{n:,} items indexed · built {t} · hotkey {hotkey}",
    "st_building": "Rebuilding index…",
    "st_progress": "Scanned {n:,} … {cur}",
    "st_done": "Index rebuilt (skipped {skipped:,})",
    "st_failed": "Index failed: {err}",
    "st_matches": "{n} matches",
    "st_copied_path": "Path copied",
    "st_copied_folder": "Folder copied",
    "st_hotkey_changed": "Shortcut changed to {spec}",
    "st_autostart_on": "Run at startup: ON",
    "st_autostart_off": "Run at startup: OFF",
    "st_close_min": "✕ action: minimize to taskbar",
    "st_close_quit": "✕ action: quit",
    "st_hotkey_failed": "Global hotkey registration failed (already in use?)",

    # dialogs
    "dlg_open_failed": "Open failed: {err}",
    "dlg_path_gone": "Path no longer exists:\n{p}",
    "dlg_hotkey_invalid": "This key combination cannot be registered:\n{spec}\n\nPick another one (Ctrl/Alt/Shift + a normal key).",
    "dlg_hotkey_conflict": "Could not register {spec}:\nthat combination is taken by another program (or reserved by Windows).\nRestored to {old}.",
    "dlg_autostart_failed": "Could not change the startup setting: {err}",

    # hotkey capture window
    "cap_title": "Set shortcut key",
    "cap_hint": "Press the new key combination\n(requires Ctrl / Alt / Shift + a key)\n\nEsc to cancel",
    "cap_need_mod": "⚠ Needs Ctrl/Alt/Shift",
    "cap_unsupported": "⚠ Unsupported key, try another",

    # about / license
    "btn_license": "License",
    "btn_ok": "OK",
    "btn_close": "Close",
    "about_text": """{app}  —  instant local file search
Version   v{ver}   (Build {build})
Author    {dev}
Contact   {email}
Platform  Windows 10 / 11 (x64)

WHAT IT IS
  Builds a lightweight index of every file on your local drives, then lets
  you jump to any of them in milliseconds — and hand the result straight to
  your file manager (Directory Opus or File Explorer) with one right-click.

FEATURES
  · Whole-disk index, search-as-you-type (471k entries in 17-56 ms here)
  · Matches both file names and full paths; folders included
  · Global hotkey to summon it from anywhere
  · Right-click to reveal & select the original file in your file manager
  · Index cached locally, instant start; rebuilds on a schedule
  · Skips system caches, dependency folders, cloud placeholders and network
    locations, so the index stays small and fast

PRIVACY
  · Fully offline: no network calls, no telemetry, no usage reporting
  · Index and settings live next to the program (config.json / index.db)
  · File paths and contents never leave your machine

KNOWN LIMITATIONS
  · The index is a snapshot: new/removed files appear after the next rebuild
  · Substring matching only — no fuzzy matching or pinyin initials yet
  · Does not hook the Open/Save dialogs of other applications

THIRD-PARTY COMPONENTS
  Python (PSF License) · Tcl/Tk (BSD-style)
  SQLite (Public Domain) · PyInstaller (GPL 2.0 + bootloader exception)

  MIT License · Copyright (c) 2026 {dev}
""",
    "license_text": """MIT License
Copyright (c) 2026 FelixHong

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

--------------------------------------------------------------------
本软件以 MIT 许可证发布：可自由使用、修改、再分发（含商业用途），
唯一要求是保留上述版权与许可声明。软件按「现状」提供，不附带担保。
它只读取文件名/路径/大小/修改时间等元数据，不修改或删除任何用户文件。
""",
}

ZH = {
    "app_name": "QuickFind",
    "win_title": "QuickFind — {hotkey}",
    "col_name": "名称",
    "col_dir": "位置",

    "reveal_in": "在 {app} 中定位",
    "fm_explorer": "资源管理器",
    "fm_dopus": "Directory Opus",
    "reveal_explorer": "在资源管理器中打开（备用）",
    "open_default": "用默认程序打开",
    "copy_path": "复制完整路径",
    "copy_folder": "复制所在文件夹",
    "reindex": "重建索引",
    "hide_bg": "隐藏窗口（后台运行）",
    "quit": "退出 QuickFind",

    "skin": "皮肤",
    "hotkey": "快捷键…",
    "open_program_dir": "打开程序目录",
    "autostart": "允许开机启动",
    "close_action": "点击 ✕ 时",
    "close_minimize": "隐藏到任务栏",
    "close_quit": "关闭并退出",
    "language": "语言",
    "lang_auto": "跟随系统",
    "about": "关于 QuickFind…",

    "skin_auto": "跟随系统",
    "skin_black": "纯黑",
    "skin_dark": "深灰（默认）",
    "skin_light": "白底",
    "skin_gray": "灰度",

    "st_empty": "索引为空 — 右键菜单 → 重建索引",
    "st_indexed": "已索引 {n:,} 项 · 建于 {t} · 热键 {hotkey}",
    "st_building": "正在重建索引…",
    "st_progress": "已扫 {n:,} … {cur}",
    "st_done": "索引完成（跳过 {skipped:,}）",
    "st_failed": "索引失败: {err}",
    "st_matches": "{n} 条匹配",
    "st_copied_path": "已复制路径",
    "st_copied_folder": "已复制文件夹",
    "st_hotkey_changed": "快捷键已改为 {spec}",
    "st_autostart_on": "开机启动：已启用",
    "st_autostart_off": "开机启动：已关闭",
    "st_close_min": "点击 ✕ :隐藏到任务栏",
    "st_close_quit": "点击 ✕ :关闭并退出",
    "st_hotkey_failed": "全局热键注册失败（被占用？）",

    "dlg_open_failed": "打开失败：{err}",
    "dlg_path_gone": "路径已不存在：\n{p}",
    "dlg_hotkey_invalid": "这个组合键无法注册：\n{spec}\n\n请换一个（必须含 Ctrl/Alt/Shift 之一 + 一个普通键）",
    "dlg_hotkey_conflict": "快捷键 {spec} 注册失败：\n该组合已被其它程序占用（或为系统保留）。\n已恢复为 {old}",
    "dlg_autostart_failed": "设置开机启动失败：{err}",

    "cap_title": "设置快捷键",
    "cap_hint": "请按下新的组合键\n（需含 Ctrl / Alt / Shift 之一）\n\nEsc 取消",
    "cap_need_mod": "⚠ 必须包含 Ctrl/Alt/Shift",
    "cap_unsupported": "⚠ 这个键不支持，请换一个",

    "btn_license": "查看许可",
    "btn_ok": "确定",
    "btn_close": "关闭",
    "about_text": """{app}  —  本地高速文件检索
版本    v{ver}   (Build {build})
开发者  {dev}
反馈    {email}
环境    Windows 10 / 11 (x64)

【它是什么】
  给本机全盘文件建一份轻量索引，输入几个字就能毫秒级定位，
  并用右键直接把文件交给 Directory Opus / 资源管理器打开。

【核心特性】
  · 全盘索引，边打边搜（本机实测 47 万条目，17-56 ms）
  · 同时匹配文件名与完整路径，文件夹也在搜索范围内
  · 全局热键随时唤起（默认 Ctrl + Shift + /）
  · 右键即在文件管理器中定位并选中原文件
  · 索引本地缓存，重启秒开；按设定的间隔自动重建
  · 排除系统缓存、依赖目录、云占位与网络位置，索引干净高效

【数据与隐私】
  · 完全离线运行：不联网、无遥测、无统计上报
  · 索引与配置仅存于本机程序目录（config.json / index.db）
  · 文件路径与内容不出本机

【已知限制】
  · 索引为快照：新增/删除的文件需下次重建后才反映
  · 匹配为子串匹配，暂不支持模糊匹配与拼音首字母
  · 不支持在其它程序的「打开/另存为」对话框内跳转

【第三方组件】
  Python (PSF License) · Tcl/Tk (BSD-style)
  SQLite (Public Domain) · PyInstaller (GPL 2.0 + bootloader exception)

  MIT 许可证 · 版权所有 (c) 2026 {dev}
""",
    "license_text": """MIT License
Copyright (c) 2026 FelixHong

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

--------------------------------------------------------------------
本软件以 MIT 许可证发布：可自由使用、修改、再分发（含商业用途），
唯一要求是保留上述版权与许可声明。软件按「现状」提供，不附带担保。
它只读取文件名/路径/大小/修改时间等元数据，不修改或删除任何用户文件。
""",
}

LANGS = {"en": EN, "zh": ZH}

# ---------------------------------------------------------------- runtime
_current = "en"


def detect_system_lang():
    """Return 'zh' when the Windows UI language is Chinese, else 'en'."""
    try:
        import ctypes
        import locale
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        # primary language id in low 10 bits; 0x04 == LANG_CHINESE
        if (langid & 0x3FF) == 0x04:
            return "zh"
    except Exception:
        pass
    try:
        import locale
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("zh"):
            return "zh"
    except Exception:
        pass
    return "en"


def set_lang(name):
    """name: 'auto' | 'en' | 'zh'. Unknown values fall back to auto-detect."""
    global _current
    n = str(name or "auto").lower()
    if n in ("auto", "", "system"):
        _current = detect_system_lang()
    elif n in LANGS:
        _current = n
    else:
        _current = detect_system_lang()
    return _current


def current_lang():
    return _current


def tr(key, **kw):
    """Translate a key; missing keys fall back to English, then to the key."""
    table = LANGS.get(_current) or EN
    s = table.get(key)
    if s is None:
        s = EN.get(key, key)
    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError):
            return s
    return s
