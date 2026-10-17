# -*- coding: utf-8 -*-
"""对比磁盘实际文件 vs 索引，列出缺失项及原因"""
import os
import sys
import sqlite3

DB = r"D:\reasonix-workspace\QuickFind\index.db"
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")

EXCL = ["$recycle.bin", "system volume information", "\\appdata\\",
        "\\package cache\\", "\\node_modules\\", "\\.git\\", "\\__pycache__\\",
        "\\site-packages\\", "\\.venv\\", "\\venv\\", "_gsdata_", "\\windowsapps\\"]

con = sqlite3.connect(DB)
indexed = set()
for (p,) in con.execute("SELECT path FROM f WHERE is_dir=0 AND path LIKE ?",
                        (ROOT + "%",)):
    indexed.add(p.lower())
con.close()

disk = []
errs = []
stack = [ROOT]
while stack:
    cur = stack.pop()
    try:
        with os.scandir(cur) as it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
                    else:
                        disk.append(e.path)
                except OSError as ex:
                    errs.append((e.path, repr(ex)))
    except OSError as ex:
        errs.append((cur, repr(ex)))

print("disk files  =", len(disk))
print("index files =", len(indexed))
missing = [p for p in disk if p.lower() not in indexed]
print("MISSING     =", len(missing))
print()
for p in missing:
    low = p.lower()
    why = [x for x in EXCL if x in low]
    print("  " + p)
    print("      排除规则命中: " + (str(why) if why else "无"))
    try:
        st = os.stat(p)
        print("      size=%d  mtime=%s" % (st.st_size,
              __import__("time").strftime("%Y-%m-%d %H:%M", __import__("time").localtime(st.st_mtime))))
    except OSError as ex:
        print("      stat 失败: %r" % ex)
print()
if errs:
    print("扫描报错 %d 处:" % len(errs))
    for p, e in errs[:10]:
        print("  ", p, e)
