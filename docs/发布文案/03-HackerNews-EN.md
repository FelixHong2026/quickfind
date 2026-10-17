# Hacker News —— Show HN 文案（英文）

**提交地址**：https://news.ycombinator.com/submit
**标题格式必须**：`Show HN: <名字> – <一句话>`（不加前缀会被当成普通帖，曝光差一半）

**推荐标题（≤80 字符最好）**：
> `Show HN: QuickFind – a 1,200-line Python file search with file-manager integration`

**备选**：
- `Show HN: An offline Windows file search I wrote because Listary was closed-source`
- `Show HN: QuickFind – type, Enter, land in the folder with the file selected`

**URL 字段**：填仓库首页 `https://github.com/FelixHong2026/quickfind`

---

## 正文（第一个 comment，发帖后立刻自己发）

```text
Author here. Some notes on how it's built and what it deliberately isn't.

WHAT IT IS
A Windows file search tool. Hotkey → type → results as you type → right-click
to reveal and *select* the file in Directory Opus or File Explorer. MIT, no
telemetry, no service, no driver, no admin rights.

WHY ANOTHER ONE
Everything already solved fast search and it's better at it than I'll ever be.
What I wanted was the last mile: search results are useless if I then have to
click through a folder tree to find the thing. So the design goal was
"right-click → already there, already selected".

HOW IT WORKS (the parts that were annoying)
• Index: os.scandir walk → SQLite cache. Deliberately not the NTFS MFT, because
  that requires a service and privileged access, and I wanted something a
  contributor could read in an afternoon. Cost: a slow first index (~5 s for
  471k entries on this machine) instead of ~1 s.

• Search: pre-lowercased path list + a C-level list comprehension. 471k
  entries in 17-56 ms. No trigram index, no clever data structure. The naive
  thing was fast enough that doing it properly felt like premature optimisation.

• Hotkey capture: this is where the real bug hunt was. Two separate problems.
  (1) Shifted keys report the wrong keysym to Tk — Shift+/ is "question",
  Shift+0 is "parenright" — so mapping from characters silently registers the
  wrong virtual key. (2) Some combinations never reach the window as a
  <KeyPress> at all. Fix: don't use key events. Poll GetAsyncKeyState every
  25 ms across ~90 candidate VKs, and read the modifier state the same way.

• Index hygiene: cloud placeholder files are skipped by attribute (OFFLINE /
  RECALL_ON_OPEN / RECALL_ON_DATA_ACCESS) so indexing never triggers a
  download. UNC paths and DRIVE_REMOTE drives are skipped. Reparse-point
  folders are only skipped when they point at a network path or would create a
  cycle — a blanket "don't follow reparse points" rule silently skipped an
  ordinary folder that happened to carry the attribute, which took a while to
  notice.

WHAT'S MISSING, HONESTLY
• Snapshot index. No USN journal tracking. New files need a rebuild.
• Substring only. No fuzzy matching, no pinyin initials.
• No dialog hooking (Listary's QuickSwitch). Not an oversight — I don't want to
  inject into other people's processes.
• Windows only.
• Unsigned binaries, so SmartScreen complains. `python src\quickfind.py` works
  if you'd rather not trust the exe.

WHAT I'D LIKE TO KNOW
If you use Directory Opus: is `dopusrt /cmd Go` + `/cmd Select` the right way
to do this, or is there a better single command? That's the part I'm least
confident about. I'm also unsure whether the reindex-on-interval behaviour is
the right default versus just telling people to hit Ctrl+R.

https://github.com/FelixHong2026/quickfind
```

---

## HN 生存指南

| 事项 | 说明 |
|---|---|
| **发帖时间** | 美东 **周二~周四 08:00-10:00**（= 北京 20:00-22:00）。周五下午、周末基本沉底 |
| **标题不要夸张** | HN 最恨 "revolutionary"、"blazing fast"、"10x"。你写 "1,200-line Python" 反而是加分项 |
| **不要报速度假数据** | 一定要说"在我的机器上"，否则会被要求 benchmark |
| **预计会被喷的点** | ① "为什么不用 Everything" ② "Python 太慢" ③ "为什么不用 Rust" ④ "子串匹配也叫搜索？" |
| **应答原则** | **承认 + 给出取舍理由**，绝不辩解。HN 对诚实的人很宽容，对狡辩的人很残忍 |
| **前 1 小时** | 至少每 10 分钟刷一次回复。HN 前 30 分钟的投票决定能不能上首页 |

### 预演过的三条回复

**"Why not just use Everything?"**
> Everything is better at this than mine is — MFT indexing, realtime updates,
> 20 years of polish. I use it too. What I wanted was the file-manager handoff:
> nothing I tried would open Directory Opus with the result already selected,
> and that's 90% of my search usage. So this is narrow on purpose.

**"Python for a file search tool? Why not Rust?"**
> Because the goal was "readable in an afternoon". A 1,200-line Python file is
> something a stranger can audit and change; the same tool in Rust would be
> four times the code and I'd lose the only advantage I have over Everything.
> If it turns out search speed is the actual bottleneck for real users, porting
> the indexer to Rust is the obvious next step — but I'd rather find that out
> first than assume it.

**"Substring matching is not search."**
> Correct, it isn't. Fuzzy matching is the next thing on the list. I shipped
> without it because I wanted the file-manager integration validated first —
> that's the part I wasn't sure anyone else wanted.
