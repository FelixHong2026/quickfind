# -*- coding: utf-8 -*-
"""
QuickFind — a lightweight, offline instant file search for Windows.

  * global hotkey summon (default Ctrl+Shift+/)
  * search-as-you-type over a cached whole-disk index (name + full path)
  * right-click to reveal & select the file in Directory Opus or File Explorer
  * Enter to open, Ctrl+C to copy the path

Index backend: os.scandir walk cached in SQLite.  No third-party packages.
Licensed under the MIT License — see LICENSE.
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from quickfind_locales import tr, set_lang, current_lang, detect_system_lang, LANGS

if getattr(sys, "frozen", False):
    # PyInstaller 打包后：__file__ 指向临时解包目录，必须用 exe 所在目录
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
DB_PATH = os.path.join(APP_DIR, "index.db")

DEFAULT_CONFIG = {
    "roots": [os.path.expanduser("~")],
    "exclude_dirs": [
        "$Recycle.Bin", "System Volume Information", "\\appdata\\",
        "\\package cache\\", "\\node_modules\\", "\\.git\\", "\\__pycache__\\",
        "\\site-packages\\", "\\.venv\\", "\\venv\\", "_gsdata_",
        "\\windowsapps\\", "onedrive",
    ],
    "hotkey": "ctrl+shift+/",
    "reveal_app": "auto",
    "dopus_rt_path": "",
    "lang": "auto",
    "max_results": 400,
    "rebuild_hours": 12,
    "include_dirs": True,
    "exclude_network": True,
    "follow_dir_links": False,
    "skin": "dark",
    "close_action": "minimize",
    "window_width": 900,
    "window_height": 520,
}


DOPUS_CANDIDATES = [
    r"C:\Program Files\GPSoftware\Directory Opus\dopusrt.exe",
    r"C:\Program Files (x86)\GPSoftware\Directory Opus\dopusrt.exe",
]


def find_dopus():
    """Locate dopusrt.exe; returns '' when Directory Opus is not installed."""
    for p in DOPUS_CANDIDATES:
        if os.path.isfile(p):
            return p
    return ""


def resolve_fm(cfg):
    """Decide which file manager to use. Returns (mode, rt_path).
    mode is 'dopus' or 'explorer'."""
    want = str(cfg.get("reveal_app", "auto")).lower()
    rt = cfg.get("dopus_rt_path") or find_dopus()
    if want == "explorer":
        return "explorer", ""
    if rt and os.path.isfile(rt):
        return "dopus", rt
    return "explorer", ""


# ---------------------------------------------------------------- meta
APP_NAME = "QuickFind"
VERSION = "0.9.0 Beta"
BUILD = "20261017"
DEVELOPER = "FelixHong"
EMAIL = "fghsxp2026@126.com"

# ---------------------------------------------------------------- skins
# 每套皮肤：bg=窗口底 input=输入框 fg=主文字 status=状态栏文字
#          row=列表底 rowfg=列表文字 head=表头 headfg=表头文字
#          sel=选中色 selfg=选中文字 menu=菜单底 menufg=菜单文字
THEMES = {
    "black": {"label": "纯黑", "bg": "#000000", "input": "#0d0d0d", "fg": "#e6e6e6",
              "status": "#7a7a7a", "row": "#0a0a0a", "rowfg": "#e6e6e6",
              "head": "#141414", "headfg": "#9a9a9a", "sel": "#0a64a4",
              "selfg": "#ffffff", "menu": "#141414", "menufg": "#e6e6e6"},
    "dark": {"label": "深灰（默认）", "bg": "#1e1e1e", "input": "#2d2d2d", "fg": "#f0f0f0",
             "status": "#8a8a8a", "row": "#252526", "rowfg": "#e8e8e8",
             "head": "#2d2d2d", "headfg": "#bbbbbb", "sel": "#0a64a4",
             "selfg": "#ffffff", "menu": "#2d2d2d", "menufg": "#e8e8e8"},
    "light": {"label": "白底", "bg": "#ffffff", "input": "#f2f2f2", "fg": "#1f1f1f",
              "status": "#6b6b6b", "row": "#ffffff", "rowfg": "#1f1f1f",
              "head": "#ececec", "headfg": "#444444", "sel": "#cce4f7",
              "selfg": "#0a2a44", "menu": "#f7f7f7", "menufg": "#1f1f1f"},
    "gray": {"label": "灰度", "bg": "#5a5a5a", "input": "#6b6b6b", "fg": "#ffffff",
             "status": "#dedede", "row": "#525252", "rowfg": "#f2f2f2",
             "head": "#646464", "headfg": "#ffffff", "sel": "#2f2f2f",
             "selfg": "#ffffff", "menu": "#646464", "menufg": "#ffffff"},
}
SKIN_ORDER = ["auto", "black", "dark", "light", "gray"]


def _system_light():
    """读 Windows 的应用主题：True=浅色"""
    try:
        import winreg
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            v, _t = winreg.QueryValueEx(k, "AppsUseLightTheme")
            return bool(v)
    except Exception:
        return False


def resolve_theme(name):
    key = str(name or "auto").lower()
    if key in ("auto", "", "system"):
        key = "light" if _system_light() else "dark"
    return THEMES.get(key, THEMES["dark"])


def skin_label(key):
    """Localised display name for a skin key."""
    k = str(key).lower()
    if k in ("auto", "", "system"):
        return tr("skin_auto")
    return tr("skin_" + k)


ABOUT_TEXT = """{app}  —  本地高速文件检索
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
  · 右键即在 DOpus / 资源管理器中定位并选中原文件
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

免费共享软件 · 版权所有 © 2026 {dev}
"""

LICENSE_TEXT = """QuickFind 免费共享软件许可声明  v1.0

版权所有 © 2026 FelixHong。保留所有权利。

一、授权范围
1. 本软件为免费共享软件，可免费下载、安装、使用，无需付费、无需注册。
2. 允许在保持完整、未经修改、未附加任何条件的前提下，原样复制与再分发
   本软件的完整安装包。
3. 允许个人在自有设备上安装任意数量副本。

二、使用限制
1. 禁止商业销售：不得以本软件本体或其打包形式收费出售、捆绑销售，或作为
   收费服务的一部分提供。
2. 禁止修改、反编译、反汇编、反向工程本软件，或基于本软件制作衍生作品。
3. 再分发时不得移除或更改任何版权声明、作者信息与许可声明。
4. 不得利用本软件从事任何违反使用者所在地法律法规的活动。

三、免责声明
1. 本软件按「现状」（AS IS）提供，不附带任何明示或暗示的担保，包括但不
   限于适销性、特定用途适用性与不侵权之担保。
2. 本软件为只读的文件检索辅助工具：仅读取文件名、路径、大小、修改时间等
   元数据，不修改、不删除、不移动任何用户文件。
3. 因使用或无法使用本软件，或因软件缺陷、系统环境、误操作而导致的任何直
   接或间接损失（包括但不限于数据丢失、业务中断、利润损失），作者不承担
   任何责任。
4. 使用者应自行备份重要数据，并自行承担使用风险。

四、隐私声明
本软件完全离线运行：不发起任何网络请求，不收集、不存储、不上传个人信息、
文件内容或使用行为数据。

五、版本与支持
1. 当前版本为 Beta（公测版），功能与内部实现可能变更，可能存在未发现的
   缺陷。
2. 问题反馈、缺陷报告与功能建议请发送至 fghsxp2026@126.com。
3. 作者会尽力处理反馈，但不承诺响应时限与修复保证。

六、许可变更
作者保留在未来版本中调整本许可条款的权利；调整后的条款自新版本发布之日
起生效。
"""


# ---------------------------------------------------------------- config
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as ex:
            print("config load failed:", ex, file=sys.stderr)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- index
def _is_network_root(path):
    """网络位置判断：UNC 路径，或 GetDriveType==DRIVE_REMOTE(4)"""
    if path.startswith("\\\\"):
        return True
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(path)) == 4
    except Exception:
        return False


# 云占位/离线文件的属性位（索引它们会触发从云端下载）
CLOUD_ATTRS = 0x1000 | 0x40000 | 0x400000   # OFFLINE | RECALL_ON_OPEN | RECALL_ON_DATA_ACCESS
REPARSE_ATTR = 0x400                        # FILE_ATTRIBUTE_REPARSE_POINT


def build_index(cfg, progress=None):
    """全量扫描 roots，返回 (rows, skipped)。rows: (path, path_lower, name_lower, is_dir, mtime)"""
    roots = cfg["roots"]
    excl = [e.lower() for e in cfg["exclude_dirs"]]
    include_dirs = cfg.get("include_dirs", False)
    exclude_network = cfg.get("exclude_network", True)
    follow_links = cfg.get("follow_dir_links", False)
    rows = []
    skipped = 0
    net_skipped = 0
    cloud_skipped = 0
    seen_real = set()

    for root in roots:
        if any(x in root.lower() for x in excl):
            skipped += 1
            continue
        if exclude_network and _is_network_root(root):
            net_skipped += 1
            continue
        if not os.path.isdir(root):
            continue
        seen_real.add(os.path.realpath(root).lower())
        stack = [root]
        while stack:
            cur = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for e in it:
                        try:
                            lp = e.path.lower()
                            if any(x in lp for x in excl):
                                skipped += 1
                                continue
                            st = e.stat(follow_symlinks=False)
                            attrs = getattr(st, "st_file_attributes", 0)
                            # 云占位/离线文件：不索引、不下钻
                            if attrs & CLOUD_ATTRS:
                                cloud_skipped += 1
                                continue
                            is_dir = e.is_dir(follow_symlinks=False)
                            if is_dir:
                                # 重解析点目录：只排除「指向网络」或「造成环路」的，
                                # 解不出目标的（=本地普通目录，如 ★★★★焚书集）照常下钻
                                if (attrs & REPARSE_ATTR) and not follow_links:
                                    real = os.path.realpath(e.path)
                                    rl = real.lower()
                                    if rl.startswith("\\\\") or _is_network_root(real):
                                        net_skipped += 1
                                        continue
                                    if any(x in rl for x in excl):
                                        skipped += 1
                                        continue
                                    if rl in seen_real:
                                        skipped += 1
                                        continue
                                    seen_real.add(rl)
                                stack.append(e.path)
                                if not include_dirs:
                                    continue
                            rows.append((e.path, lp, e.name.lower(),
                                         1 if is_dir else 0, int(st.st_mtime)))
                        except (OSError, PermissionError):
                            skipped += 1
            except (OSError, PermissionError):
                skipped += 1
            if progress and len(rows) % 20000 == 0:
                progress(len(rows), cur)
    if net_skipped or cloud_skipped:
        print("[index] 跳过网络根 %d 个、云占位/离线 %d 个" % (net_skipped, cloud_skipped))
    return rows, skipped


def save_index(rows, skipped):
    tmp = DB_PATH + ".tmp"
    con = sqlite3.connect(tmp)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE TABLE f (path TEXT, pl TEXT, name TEXT, is_dir INT, mtime INT)")
    con.executemany("INSERT INTO f VALUES (?,?,?,?,?)", rows)
    con.execute("CREATE TABLE meta (k TEXT, v TEXT)")
    con.executemany("INSERT INTO meta VALUES (?,?)", [
        ("built_at", str(int(time.time()))),
        ("count", str(len(rows))),
        ("skipped", str(skipped)),
    ])
    con.commit()
    con.close()
    os.replace(tmp, DB_PATH)


def load_index():
    """返回 (paths, pls, names, isdirs, built_at)；pls/names 已小写"""
    if not os.path.exists(DB_PATH):
        return [], [], [], [], 0
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=OFF")
    rows = con.execute("SELECT path, pl, name, is_dir FROM f").fetchall()
    built = 0
    try:
        r = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
        built = int(r[0]) if r else 0
    except Exception:
        pass
    con.close()
    paths = [r[0] for r in rows]
    pls = [r[1] for r in rows]
    names = [r[2] for r in rows]
    isdirs = [r[3] for r in rows]
    return paths, pls, names, isdirs, built


def search(paths, pls, names, isdirs, needle, limit):
    """子串匹配 + 排序：文件名命中优先，其次路径短优先"""
    if not needle:
        return []
    n = needle.lower()
    name_hits = [i for i, nm in enumerate(names) if n in nm]
    if len(name_hits) >= limit:
        name_hits.sort(key=lambda i: (len(names[i]), len(paths[i])))
        return [(paths[i], isdirs[i]) for i in name_hits[:limit]]
    path_hits = [i for i, pl in enumerate(pls) if n in pl and n not in names[i]]
    name_hits.sort(key=lambda i: (len(names[i]), len(paths[i])))
    path_hits.sort(key=lambda i: len(paths[i]))
    picked = (name_hits + path_hits)[:limit]
    return [(paths[i], isdirs[i]) for i in picked]


# ---------------------------------------------------------------- hotkey
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN = 0x0001, 0x0002, 0x0004, 0x0008
WM_HOTKEY = 0x0312

VK = {
    "space": 0x20, "tab": 0x09, "enter": 0x0D, "backspace": 0x08,
    "escape": 0x1B, "insert": 0x2D, "delete": 0x2E,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "grave": 0xC0, "`": 0xC0, "slash": 0xBF, "/": 0xBF,
    "backslash": 0xDC, "\\": 0xDC, "semicolon": 0xBA, ";": 0xBA,
    "apostrophe": 0xDE, "'": 0xDE, "quote": 0xDE,
    "comma": 0xBC, ",": 0xBC, "period": 0xBE, ".": 0xBE,
    "minus": 0xBD, "-": 0xBD, "equal": 0xBB, "=": 0xBB,
    "bracketleft": 0xDB, "[": 0xDB, "bracketright": 0xDD, "]": 0xDD,
}
for _i in range(10):
    VK[str(_i)] = 0x30 + _i
for _i in range(26):
    _c = chr(ord("a") + _i)
    VK[_c] = 0x41 + _i
for _i in range(1, 25):
    VK["f%d" % _i] = 0x6F + _i

# 反向表：VK → 规范名（用于把捕获到的 keycode 写成可读的配置串）
VK_NAME = {}
for _n, _v in VK.items():
    if _v not in VK_NAME or len(_n) > len(VK_NAME[_v]):
        if _n.isalnum() and len(_n) > 1:
            VK_NAME.setdefault(_v, _n)
for _n, _v in list(VK.items()):
    VK_NAME.setdefault(_v, _n)


def vk_to_name(vk):
    """虚拟键码 → 配置串里用的名字；无法命名的用 vk:0xNN"""
    if vk in VK_NAME:
        return VK_NAME[vk]
    return "vk:0x%02X" % vk


def parse_hotkey(s):
    mods = 0
    key = None
    for part in str(s).lower().split("+"):
        part = part.strip()
        if part in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif part == "shift":
            mods |= MOD_SHIFT
        elif part == "alt":
            mods |= MOD_ALT
        elif part == "win":
            mods |= MOD_WIN
        elif part.startswith("vk:0x"):
            try:
                key = int(part[5:], 16)
            except ValueError:
                key = None
        elif part in VK:
            key = VK[part]
        elif len(part) == 1 and part.isalnum():
            key = ord(part.upper())
        else:
            key = None
    return mods, key


class HotkeyThread(threading.Thread):
    """独立线程注册全局热键，命中后通过队列通知 UI；支持 stop() 后重建"""

    def __init__(self, spec, q):
        super().__init__(daemon=True)
        self.spec = spec
        self.q = q
        self.hotkey_id = 0x51F7
        self.tid = 0
        self.ok = False
        self.ready = threading.Event()

    def stop(self):
        """让 GetMessageW 返回 0 → 退出循环 → finally 里注销热键"""
        if self.tid:
            try:
                ctypes.windll.user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
            except Exception:
                pass

    def run(self):
        self.tid = ctypes.windll.kernel32.GetCurrentThreadId()
        mods, key = parse_hotkey(self.spec)
        if key is None:
            self.ready.set()
            self.q.put("hotkey-invalid")
            return
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, self.hotkey_id, mods, key):
            self.ready.set()
            self.q.put("hotkey-failed")
            return
        self.ok = True
        self.ready.set()
        self.q.put("hotkey-ok")
        try:
            msg = wt.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                    self.q.put("hotkey")
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)


# ---------------------------------------------------------------- UI
class QuickFind(tk.Tk):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        set_lang(cfg.get("lang", "auto"))
        self.fm_mode, self.fm_rt = resolve_fm(cfg)
        self.paths, self.pls, self.names, self.isdirs, self.built_at = load_index()
        self.evq = queue.Queue()
        self.indexing = False

        self.skin = str(cfg.get("skin", "dark")).lower()
        self.th = resolve_theme(self.skin)
        self._menus = []

        self.title(tr("win_title", hotkey=cfg.get("hotkey", "")))
        w, h = cfg["window_width"], cfg["window_height"]
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        geo = cfg.get("last_geometry")
        if not geo:
            geo = f"{w}x{h}+{(sw - w) // 2}+{max(60, sh // 5)}"
        try:
            self.geometry(geo)
        except Exception:
            self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(60, sh // 5)}")
        self.minsize(520, 260)
        # ✕ 行为由设置决定（默认最小化到任务栏）
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # 搜索框行：输入框 + ⚙ 设置按钮
        self.wrap = tk.Frame(self)
        self.wrap.pack(fill="x", padx=10, pady=(10, 4))
        self.entry = tk.Entry(self.wrap, font=("Segoe UI", 15),
                              relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(2, 6), pady=2)
        self.btn_settings = tk.Button(self.wrap, text="⚙", command=self.open_settings_menu,
                                      font=("Segoe UI", 13), relief="flat", bd=0,
                                      width=2, cursor="hand2")
        self.btn_settings.pack(side="right", padx=(0, 2), pady=2)
        self.entry.bind("<KeyRelease>", self.on_key)
        self.entry.bind("<Escape>", lambda e: self.hide())
        self.entry.bind("<Return>", self.open_selected)
        self.entry.bind("<Down>", lambda e: self.move_sel(1))
        self.entry.bind("<Up>", lambda e: self.move_sel(-1))
        self.entry.bind("<Control-c>", lambda e: self.copy_selected())
        self.entry.bind("<Control-r>", lambda e: self.start_reindex())

        # 状态条
        self.status = tk.Label(self, text="", anchor="w", font=("Segoe UI", 9))
        self.status.pack(fill="x", padx=12)

        # 结果列表
        self.tree = ttk.Treeview(self, columns=("name", "dir"), show="headings",
                                 style="QF.Treeview", selectmode="browse")
        self.tree.heading("name", text=tr("col_name"))
        self.tree.heading("dir", text=tr("col_dir"))
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("dir", width=560, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.tree.bind("<Double-1>", self.open_selected)
        self.tree.bind("<Button-3>", self.show_menu)     # 右键
        self.tree.bind("<Escape>", lambda e: self.hide())

        # 菜单（可随语言重建）
        self._build_menus()

        self.apply_theme()

        self._debounce = None
        self.update_status()
        self.after(80, self.poll_events)

        self.hk = HotkeyThread(cfg["hotkey"], self.evq)
        self.hk.start()

        # 首次运行 / 索引为空 / --show：直接显示；否则隐藏，靠热键唤起
        if "--show" in sys.argv or not self.paths:
            self.show()
        else:
            self.withdraw()
        self.after(600, self.maybe_auto_reindex)

    # ---------------- 菜单（随语言重建）
    def _build_menus(self):
        cfg = self.cfg
        for m in self._menus:
            try:
                m.destroy()
            except Exception:
                pass
        self._menus = []

        # 结果右键菜单
        self.menu = tk.Menu(self, tearoff=0)
        self._menus.append(self.menu)
        fm = tr("fm_dopus") if self.fm_mode == "dopus" else tr("fm_explorer")
        self.menu.add_command(label=tr("reveal_in", app=fm), command=self.reveal_selected)
        self.menu.add_command(label=tr("reveal_explorer"), command=self.reveal_explorer)
        self.menu.add_command(label=tr("open_default"), command=self.open_selected)
        self.menu.add_separator()
        self.menu.add_command(label=tr("copy_path"), command=self.copy_selected)
        self.menu.add_command(label=tr("copy_folder"), command=self.copy_folder)
        self.menu.add_separator()
        self.menu.add_command(label=tr("reindex"), command=self.start_reindex)
        self.menu.add_command(label=tr("hide_bg"), command=self.hide)
        self.menu.add_command(label=tr("quit"), command=self.quit_app)

        # 设置菜单（⚙）
        self.settings_menu = tk.Menu(self, tearoff=0)
        self._menus.append(self.settings_menu)

        self.skin_menu = tk.Menu(self.settings_menu, tearoff=0)
        self._menus.append(self.skin_menu)
        for key in SKIN_ORDER:
            self.skin_menu.add_command(label=skin_label(key),
                                       command=lambda k=key: self.apply_theme(k))
        self.settings_menu.add_cascade(label=tr("skin"), menu=self.skin_menu)

        self.lang_menu = tk.Menu(self.settings_menu, tearoff=0)
        self._menus.append(self.lang_menu)
        cur_lang = str(cfg.get("lang", "auto"))
        self.var_lang = tk.StringVar(value=cur_lang)
        self.lang_menu.add_radiobutton(label=tr("lang_auto"), variable=self.var_lang,
                                       value="auto", command=lambda: self.set_language("auto"))
        self.lang_menu.add_radiobutton(label="English", variable=self.var_lang,
                                       value="en", command=lambda: self.set_language("en"))
        self.lang_menu.add_radiobutton(label="中文", variable=self.var_lang,
                                       value="zh", command=lambda: self.set_language("zh"))
        self.settings_menu.add_cascade(label=tr("language"), menu=self.lang_menu)

        self.settings_menu.add_command(label=tr("hotkey"), command=self.capture_hotkey)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=tr("reindex"), command=self.start_reindex)
        self.settings_menu.add_command(label=tr("open_program_dir"),
                                       command=self.open_program_dir)
        self.settings_menu.add_separator()

        self.var_autostart = tk.BooleanVar(value=self._autostart_on())
        self.var_close = tk.StringVar(value=str(cfg.get("close_action", "minimize")))
        close_menu = tk.Menu(self.settings_menu, tearoff=0)
        self._menus.append(close_menu)
        close_menu.add_radiobutton(label=tr("close_minimize"), variable=self.var_close,
                                   value="minimize", command=self._save_close_action)
        close_menu.add_radiobutton(label=tr("close_quit"), variable=self.var_close,
                                   value="quit", command=self._save_close_action)
        self.settings_menu.add_checkbutton(label=tr("autostart"),
                                           variable=self.var_autostart,
                                           command=self.toggle_autostart)
        self.settings_menu.add_cascade(label=tr("close_action"), menu=close_menu)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=tr("about"), command=self.show_about)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=tr("quit"), command=self.quit_app)

    def set_language(self, name):
        """Switch UI language immediately (menus rebuilt, no restart)."""
        cur = set_lang(name)
        self.cfg["lang"] = str(name).lower()
        save_config(self.cfg)
        self._build_menus()
        self.apply_theme()
        self.title(tr("win_title", hotkey=self.cfg.get("hotkey", "")))
        self.tree.heading("name", text=tr("col_name"))
        self.tree.heading("dir", text=tr("col_dir"))
        self.update_status()
        _log("lang -> %s (%s)" % (cur, self.cfg["lang"]))

    # ---------------- 状态
    def update_status(self, extra=""):
        if not self.paths:
            base = tr("st_empty")
        else:
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(self.built_at)) if self.built_at else "?"
            base = tr("st_indexed", n=len(self.paths), t=t, hotkey=self.cfg['hotkey'])
        self.status.config(text=(base + ("  |  " + extra if extra else "")))

    def maybe_auto_reindex(self):
        hrs = self.cfg.get("rebuild_hours", 0)
        if not hrs:
            return
        if not self.paths or (time.time() - self.built_at) > hrs * 3600:
            self.start_reindex()

    # ---------------- 索引
    def start_reindex(self):
        if self.indexing:
            return
        self.indexing = True
        self.update_status(tr("st_building"))
        threading.Thread(target=self._reindex_worker, daemon=True).start()

    def _reindex_worker(self):
        def prog(n, cur):
            self.evq.put(("progress", tr("st_progress", n=n, cur=cur[:60])))
        try:
            rows, skipped = build_index(self.cfg, prog)
            save_index(rows, skipped)
            self.evq.put(("indexed", (rows, skipped)))
        except Exception as ex:
            self.evq.put(("index-error", repr(ex)))

    # ---------------- 事件泵
    def poll_events(self):
        try:
            while True:
                item = self.evq.get_nowait()
                if isinstance(item, tuple):
                    kind, payload = item
                    if kind == "progress":
                        self.update_status(payload)
                    elif kind == "indexed":
                        rows, skipped = payload
                        self.paths = [r[0] for r in rows]
                        self.pls = [r[1] for r in rows]
                        self.names = [r[2] for r in rows]
                        self.isdirs = [r[3] for r in rows]
                        self.built_at = int(time.time())
                        self.indexing = False
                        self.update_status(tr("st_done", skipped=skipped))
                    elif kind == "index-error":
                        self.indexing = False
                        self.update_status(tr("st_failed", err=payload))
                else:
                    if item == "hotkey":
                        _log("hotkey fired -> toggle()")
                        self.toggle()
                    elif item == "hotkey-failed":
                        _log("hotkey registration FAILED")
                        self.update_status(tr("st_hotkey_failed"))
                    elif item == "hotkey-ok":
                        _log("hotkey registered OK: " + self.cfg["hotkey"])
                    elif item == "hotkey-invalid":
                        _log("hotkey spec invalid: " + self.cfg["hotkey"])
            # 处理完再动 UI
            if self.paths and self.entry.get():
                self.run_search()
        except queue.Empty:
            pass
        self.after(80, self.poll_events)

    # ---------------- 搜索
    def on_key(self, _ev=None):
        if self._debounce:
            self.after_cancel(self._debounce)
        self._debounce = self.after(120, self.run_search)

    def run_search(self):
        self._debounce = None
        q = self.entry.get().strip()
        self.tree.delete(*self.tree.get_children())
        if not q:
            self.update_status()
            return
        hits = search(self.paths, self.pls, self.names, self.isdirs, q, self.cfg["max_results"])
        for path, is_dir in hits:
            self.tree.insert("", "end", values=(
                ("📁 " if is_dir else "") + os.path.basename(path.rstrip("\\")) or path,
                os.path.dirname(path) or path))
        if hits:
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
        self.update_status(tr("st_matches", n=len(hits)))

    def move_sel(self, delta):
        ch = self.tree.get_children()
        if not ch:
            return "break"
        cur = self.tree.selection()
        idx = ch.index(cur[0]) if cur else -1
        idx = max(0, min(len(ch) - 1, idx + delta))
        self.tree.selection_set(ch[idx])
        self.tree.focus(ch[idx])
        self.tree.see(ch[idx])
        return "break"

    def selected_path(self):
        sel = self.tree.selection()
        if not sel:
            return None
        name, folder = self.tree.item(sel[0], "values")
        name = name.replace("📁 ", "", 1)
        return os.path.join(folder, name) if folder else name

    # ---------------- 动作
    def reveal_selected(self, _ev=None):
        """★ 核心需求：在文件管理器中定位（默认 Directory Opus，可退回资源管理器）"""
        p = self.selected_path()
        if not p:
            return "break"
        try:
            if not os.path.exists(p):
                parent = os.path.dirname(p)
                if os.path.isdir(parent):
                    self._reveal_with(parent)
                else:
                    messagebox.showwarning(APP_NAME, tr("dlg_path_gone", p=p))
                return "break"
            self._reveal_with(p)
        except Exception as ex:
            messagebox.showerror(APP_NAME, tr("dlg_open_failed", err=ex))
        return "break"

    def reveal_explorer(self):
        """备用：用系统资源管理器定位"""
        p = self.selected_path()
        if not p:
            return "break"
        try:
            if os.path.isdir(p):
                os.startfile(p)
            else:
                subprocess.Popen(['explorer.exe', '/select,' + p])
        except Exception as ex:
            messagebox.showerror(APP_NAME, tr("dlg_open_failed", err=ex))
        return "break"

    def _reveal_with(self, p):
        """Reveal p (file or folder) in the configured file manager."""
        if self.fm_mode == "dopus" and self.fm_rt:
            rt = self.fm_rt
            if os.path.isdir(p):
                subprocess.Popen([rt, "/cmd", "Go", p])
            else:
                parent = os.path.dirname(p)
                subprocess.Popen([rt, "/cmd", "Go", parent])
                time.sleep(0.25)          # let the lister navigate first
                subprocess.Popen([rt, "/cmd", "Select", os.path.basename(p)])
            return
        # explorer fallback
        if os.path.isdir(p):
            os.startfile(p)
        else:
            subprocess.Popen(['explorer.exe', '/select,' + p])

    def open_selected(self, _ev=None):
        p = self.selected_path()
        if not p:
            return "break"
        try:
            os.startfile(p)
            self.hide()
        except Exception as ex:
            messagebox.showerror(APP_NAME, tr("dlg_open_failed", err=ex))
        return "break"

    def copy_selected(self):
        p = self.selected_path()
        if p:
            self.clipboard_clear()
            self.clipboard_append(p)
            self.update_status(tr("st_copied_path"))
        return "break"

    def copy_folder(self):
        p = self.selected_path()
        if p:
            self.clipboard_clear()
            self.clipboard_append(os.path.dirname(p))
            self.update_status(tr("st_copied_folder"))
        return "break"

    def show_menu(self, ev):
        row = self.tree.identify_row(ev.y)
        if row:
            self.tree.selection_set(row)
            self.tree.focus(row)
            self.menu.tk_popup(ev.x_root, ev.y_root)
        return "break"

    # ---------------- 设置 / 皮肤 / 关于
    def apply_theme(self, skin=None):
        """应用皮肤；skin=None 表示按当前配置重绘"""
        if skin is not None:
            self.skin = str(skin).lower()
            self.cfg["skin"] = self.skin
            save_config(self.cfg)
        t = resolve_theme(self.skin)
        self.th = t
        try:
            self.configure(bg=t["bg"])
            self.wrap.configure(bg=t["bg"])
            self.entry.configure(bg=t["input"], fg=t["fg"], insertbackground=t["fg"],
                                 selectbackground=t["sel"], selectforeground=t["selfg"])
            self.btn_settings.configure(bg=t["input"], fg=t["fg"],
                                        activebackground=t["sel"], activeforeground=t["selfg"])
            self.status.configure(bg=t["bg"], fg=t["status"])
        except Exception as ex:
            _log("apply_theme widget err: %r" % (ex,))
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("QF.Treeview", background=t["row"], fieldbackground=t["row"],
                     foreground=t["rowfg"], rowheight=24, borderwidth=0,
                     font=("Segoe UI", 10))
        st.configure("QF.Treeview.Heading", background=t["head"], foreground=t["headfg"],
                     font=("Segoe UI", 9))
        st.map("QF.Treeview",
               background=[("selected", t["sel"])],
               foreground=[("selected", t["selfg"])])
        for m in getattr(self, "_menus", []):
            try:
                m.configure(bg=t["menu"], fg=t["menufg"],
                            activebackground=t["sel"], activeforeground=t["selfg"])
            except Exception:
                pass
        self.update_status()

    def open_settings_menu(self):
        try:
            x = self.btn_settings.winfo_rootx()
            y = self.btn_settings.winfo_rooty() + self.btn_settings.winfo_height()
            self.settings_menu.tk_popup(x, y)
        except Exception as ex:
            _log("settings menu err: %r" % (ex,))

    def open_program_dir(self):
        try:
            os.startfile(APP_DIR)
        except Exception as ex:
            messagebox.showerror(APP_NAME, tr("dlg_open_failed", err=repr(ex)))

    def restart_hotkey(self, spec):
        """停掉旧线程、按 spec 重新注册；返回是否成功"""
        try:
            if getattr(self, "hk", None):
                self.hk.stop()
                self.hk.join(timeout=2)
        except Exception:
            pass
        self.hk = HotkeyThread(spec, self.evq)
        self.hk.start()
        self.hk.ready.wait(timeout=4)
        return bool(self.hk.ok)

    def _apply_new_hotkey(self, spec):
        old = self.cfg.get("hotkey", "")
        if spec == old:
            return
        mods, vk = parse_hotkey(spec)
        if not mods or not vk:
            messagebox.showwarning(APP_NAME, tr("dlg_hotkey_invalid", spec=spec))
            return
        self.cfg["hotkey"] = spec
        save_config(self.cfg)
        if self.restart_hotkey(spec):
            self.title(tr("win_title", hotkey=spec))
            _log("hotkey changed to %s (mods=%d vk=0x%02X)" % (spec, mods, vk))
            self.update_status(tr("st_hotkey_changed", spec=spec))
        else:
            self.cfg["hotkey"] = old
            save_config(self.cfg)
            self.restart_hotkey(old)
            _log("hotkey change FAILED (%s), reverted to %s" % (spec, old))
            messagebox.showwarning(
                APP_NAME, tr("dlg_hotkey_conflict", spec=spec, old=old))

    def capture_hotkey(self):
        t = resolve_theme(self.skin)
        top = tk.Toplevel(self)
        top.title(tr("cap_title"))
        top.transient(self)
        top.grab_set()
        top.resizable(False, False)
        top.configure(bg=t["bg"])
        tk.Label(top, text=tr("cap_hint"),
                 bg=t["bg"], fg=t["fg"], font=("Segoe UI", 11),
                 justify="center").pack(padx=26, pady=(18, 8))
        cur = tk.Label(top, text="…", bg=t["input"], fg=t["fg"],
                       font=("Consolas", 14), width=30)
        cur.pack(padx=26, pady=(0, 18), ipady=7)
        done = {"v": False}
        CAND = ([0x1B] + [0x30 + _i for _i in range(10)] + [0x41 + _i for _i in range(26)]
                + [0x6F + _i for _i in range(1, 25)]
                + [0x20, 0xBF, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xC0, 0xDB, 0xDC, 0xDD,
                   0x25, 0x26, 0x27, 0x28, 0x09, 0x0D, 0x08, 0x2D, 0x2E,
                   0x24, 0x23, 0x21, 0x22])
        prev = {v: False for v in CAND}
        MOD_CTRL, MOD_ALT, MOD_SHIFT = 0x11, 0x12, 0x10

        def poll():
            """轮询物理键状态 —— 不依赖 Tk 的 KeyPress（某些组合会被 IME/系统吞掉）"""
            if done["v"]:
                return
            u32 = ctypes.windll.user32
            down_ctrl = bool(u32.GetAsyncKeyState(MOD_CTRL) & 0x8000)
            down_alt = bool(u32.GetAsyncKeyState(MOD_ALT) & 0x8000)
            down_shift = bool(u32.GetAsyncKeyState(MOD_SHIFT) & 0x8000)
            mods = [m for m, on in (("ctrl", down_ctrl), ("alt", down_alt),
                                    ("shift", down_shift)) if on]
            hit = 0
            for vk in CAND:
                cur_down = bool(u32.GetAsyncKeyState(vk) & 0x8000)
                if cur_down and not prev[vk]:
                    hit = vk
                    break
                prev[vk] = cur_down
            if not hit:
                # 只显示当前修饰键，给出即时反馈
                cur.config(text=("+".join(mods) + "+…") if mods else "…")
                top.after(25, poll)
                return
            if hit == 0x1B:                     # Esc 取消
                done["v"] = True
                top.destroy()
                return
            if not mods:
                cur.config(text=tr("cap_need_mod"))
                top.after(25, poll)
                return
            spec = "+".join(mods + [vk_to_name(hit)])
            cur.config(text=spec)
            done["v"] = True
            _log("capture: spec=%s (vk=0x%02X)" % (spec, hit))
            top.after(220, lambda: (top.destroy(), self._apply_new_hotkey(spec)))

        top.bind("<Escape>", lambda e: (done.__setitem__("v", True), top.destroy()))
        top.focus_force()
        top.after(60, lambda: top.focus_force())
        top.after(120, poll)

    def show_about(self):
        t = resolve_theme(self.skin)
        top = tk.Toplevel(self)
        top.title(tr("about").replace("…", "").strip() + " — " + APP_NAME)
        top.transient(self)
        top.configure(bg=t["bg"])
        txt = tk.Text(top, width=78, height=36, bg=t["row"], fg=t["rowfg"],
                      relief="flat", bd=0, font=("Consolas", 9), wrap="word")
        txt.insert("1.0", tr("about_text", app=APP_NAME, ver=VERSION, build=BUILD,
                             dev=DEVELOPER, email=EMAIL))
        txt.config(state="disabled")
        txt.pack(padx=12, pady=(12, 8))
        bar = tk.Frame(top, bg=t["bg"])
        bar.pack(pady=(0, 12))

        def mk(text, cmd):
            return tk.Button(bar, text=text, command=cmd, font=("Segoe UI", 10),
                             bg=t["input"], fg=t["fg"], relief="flat", bd=0,
                             activebackground=t["sel"], activeforeground=t["selfg"],
                             padx=16, pady=5, cursor="hand2")

        mk(tr("btn_license"), lambda: self.show_license(t)).pack(side="left", padx=6)
        mk(tr("btn_ok"), top.destroy).pack(side="left", padx=6)
        top.focus_force()

    def show_license(self, t=None):
        t = t or resolve_theme(self.skin)
        top = tk.Toplevel(self)
        top.title(APP_NAME + " — " + tr("btn_license"))
        top.transient(self)
        top.configure(bg=t["bg"])
        txt = tk.Text(top, width=78, height=30, bg=t["row"], fg=t["rowfg"],
                      relief="flat", bd=0, font=("Consolas", 9), wrap="word")
        txt.insert("1.0", tr("license_text"))
        txt.config(state="disabled")
        txt.pack(padx=12, pady=(12, 8))
        tk.Button(top, text=tr("btn_close"), command=top.destroy, font=("Segoe UI", 10),
                  bg=t["input"], fg=t["fg"], relief="flat", bd=0,
                  activebackground=t["sel"], activeforeground=t["selfg"],
                  padx=16, pady=5, cursor="hand2").pack(pady=(0, 12))
        top.focus_force()

    # ---------------- ✕ 行为 / 开机启动
    def _startup_lnk(self):
        return os.path.join(os.environ.get("APPDATA", ""),
                            r"Microsoft\Windows\Start Menu\Programs\Startup\QuickFind.lnk")

    def _autostart_on(self):
        try:
            return os.path.exists(self._startup_lnk())
        except Exception:
            return False

    def toggle_autostart(self):
        want = bool(self.var_autostart.get())
        lnk = self._startup_lnk()
        try:
            if want:
                if getattr(sys, "frozen", False):
                    target = os.path.abspath(sys.executable)
                    args = ""
                else:
                    target = sys.executable
                    args = '"%s"' % os.path.abspath(__file__)
                ps = ("$w=New-Object -ComObject WScript.Shell;"
                      "$s=$w.CreateShortcut('%s');$s.TargetPath='%s';$s.Arguments='%s';"
                      "$s.WorkingDirectory='%s';$s.Description='QuickFind';$s.Save()") % (
                    lnk.replace("'", "''"), target.replace("'", "''"),
                    args.replace("'", "''"), APP_DIR.replace("'", "''"))
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-Command", ps], check=False,
                               creationflags=0x08000000)
            else:
                if os.path.exists(lnk):
                    os.remove(lnk)
        except Exception as ex:
            messagebox.showerror(APP_NAME, tr("dlg_autostart_failed", err=repr(ex)))
        now = self._autostart_on()
        try:
            self.var_autostart.set(now)
        except Exception:
            pass
        _log("autostart -> %s" % now)
        self.update_status(tr("st_autostart_on") if now else tr("st_autostart_off"))

    def _save_close_action(self):
        self.cfg["close_action"] = self.var_close.get()
        save_config(self.cfg)
        _log("close_action -> %s" % self.cfg["close_action"])
        self.update_status(tr("st_close_min") if self.cfg["close_action"] == "minimize"
                            else tr("st_close_quit"))

    def on_close(self):
        act = str(self.cfg.get("close_action", "minimize"))
        try:
            if hasattr(self, "var_close"):
                act = self.var_close.get() or act
        except Exception:
            pass
        _log("WM_CLOSE -> %s" % act)
        if act == "quit":
            self.quit_app()
        elif act == "hide":
            self.hide()
        else:
            self.iconify()

    # ---------------- 显示
    def show(self):
        try:
            self.deiconify()
        except Exception:
            pass
        self.lift()
        self.focus_force()
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def hide(self):
        _log("hide() called (still running in background)")
        try:
            self.cfg["last_geometry"] = self.geometry()
            save_config(self.cfg)
        except Exception:
            pass
        self.withdraw()

    def quit_app(self):
        _log("quit_app() called")
        try:
            self.cfg["last_geometry"] = self.geometry()
            save_config(self.cfg)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def toggle(self):
        """热键行为：隐藏/最小化时→显示；已是前台→隐藏；否则→提到前台"""
        try:
            st = self.state()
        except Exception:
            st = "normal"
        if st in ("withdrawn", "iconic"):
            self.show()
            return
        try:
            fg = int(ctypes.windll.user32.GetForegroundWindow())
            mine = int(self.wm_frame(), 16)
        except Exception:
            fg, mine = 0, -1
        if fg == mine:
            self.hide()
        else:
            self.show()


# ---------------------------------------------------------------- selftest
def selftest():
    cfg = load_config()
    t0 = time.time()
    rows, skipped = build_index(cfg)
    t1 = time.time()
    print(f"[index] {len(rows):,} 项, 跳过 {skipped:,}, 耗时 {t1 - t0:.1f}s")
    if rows:
        save_index(rows, skipped)
        paths, pls, names, isdirs, built = load_index()
        print(f"[cache] 载入 {len(paths):,} 项, built_at={built}")
        for q in ("quickfind", "listary", ".py", "报告"):
            t2 = time.time()
            hits = search(paths, pls, names, isdirs, q, 600)
            print(f"[search] '{q}' -> {len(hits)} 命中, 耗时 {(time.time() - t2) * 1000:.0f}ms")
            for h in hits[:3]:
                print("         ", h[0])
    return 0


def _log(msg):
    try:
        with open(os.path.join(APP_DIR, "quickfind.log"), "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


_MUTEX = None


def main():
    global _MUTEX
    if "--selftest" in sys.argv:
        return selftest()
    # 单实例保护：重复启动会产生两个窗口，并让全局热键注册失败
    try:
        _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False,
                                                     "Local\\QuickFind_SingleInstance")
        if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            _log("another instance is already running; exiting this one")
            return 0
    except Exception:
        pass
    try:
        cfg = load_config()
        if not os.path.exists(CONFIG_PATH):
            save_config(cfg)
        _log("starting; index_count=%d" % len(load_index()[0]))
        app = QuickFind(cfg)
        _log("window created, entering mainloop")
        app.mainloop()
        _log("mainloop returned normally")
    except BaseException:
        import traceback
        _log("CRASH:\n" + traceback.format_exc())
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
