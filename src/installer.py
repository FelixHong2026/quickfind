# -*- coding: utf-8 -*-
"""QuickFind 安装器（由 PyInstaller 编译为 QuickFind-Setup.exe）

做四件事：
  1) 把内嵌的 QuickFind 程序目录（onedir）装到 %LOCALAPPDATA%\\Programs\\QuickFind
  2) 建「开始菜单」快捷方式 + 注册**登录延迟 30 秒**的计划任务（开机自启）
  3) 注册到「应用和功能」卸载列表（HKCU，无需管理员）
  4) 附带 uninstall.cmd，可一键卸载
用法：直接双击；或 QuickFind-Setup.exe /S  静默安装

为什么自启用计划任务而不是「启动」文件夹：
  启动文件夹里的快捷方式是登录瞬间就拉起，跟系统刚启动的一堆服务抢 CPU/磁盘；
  用计划任务的 AtLogon + Delay 可以延后 30 秒，进桌面稳定后再起。
  热键工具不能不自启（否则每次开机都得手动双击才能用），但也没必要赶在最前面。
"""
import os
import shutil
import subprocess
import sys
import time
import winreg

APP_NAME = "QuickFind"
APP_DESC = "QuickFind - 个人高速文件查询工具 (Ctrl+Shift+/)"
APP_EXE = "QuickFind.exe"
VERSION = "0.9.4 Beta"

LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
INSTALL_DIR = os.path.join(LOCALAPPDATA, "Programs", APP_NAME)
START_MENU = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
STARTUP = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
UNINST_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\\" + APP_NAME

# 开机自启：登录后延迟多少秒再启动
TASK_NAME = APP_NAME
AUTOSTART_DELAY_SEC = 30

BUNDLE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
SILENT = "/S" in sys.argv

# NOTE: the installer deliberately does NOT ship a config.json.
# QuickFind generates its own defaults from DEFAULT_CONFIG on first run,
# which keeps a single source of truth and avoids stale copies here.

UNINSTALL_CMD = r'''@echo off
echo 正在卸载 QuickFind...
set "APP=%LOCALAPPDATA%\Programs\QuickFind"
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\QuickFind.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\QuickFind.lnk" 2>nul
schtasks /Delete /TN QuickFind /F >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\QuickFind" /f >nul 2>&1
taskkill /IM QuickFind.exe /F >nul 2>&1
echo 删除程序文件...
start "" /b cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q %APP%"
echo 卸载完成。
'''


# 用户数据：升级时不能被安装包里的同名文件覆盖
USER_FILES = ("config.json", "index.db", "index.db-wal", "index.db-shm",
              "quickfind.log", "uninstall.cmd")


def copy_tree_merge(src, dst):
    """递归复制 onedir 目录树；已存在的用户数据文件保留不动

    返回 (复制了多少文件, 保留了哪些用户文件)
    """
    copied = 0
    kept = []
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            c2, k2 = copy_tree_merge(s, d)
            copied += c2
            kept.extend(k2)
            continue
        if name in USER_FILES and os.path.exists(d):
            kept.append(name)
            continue
        shutil.copy2(s, d)
        copied += 1
    return copied, kept


def say(msg):
    print(msg)
    sys.stdout.flush()


def make_shortcut(lnk_path, target, workdir):
    ps = (
        "$w=New-Object -ComObject WScript.Shell;"
        "$s=$w.CreateShortcut('%s');"
        "$s.TargetPath='%s';$s.WorkingDirectory='%s';"
        "$s.Description='%s';$s.Save()"
    ) % (lnk_path.replace("'", "''"), target.replace("'", "''"),
         workdir.replace("'", "''"), APP_DESC)
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command", ps], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_running_app(timeout=20):
    """结束正在运行的 QuickFind

    升级时 QuickFind.exe 正被占用，不先结束就会在 copy2 时报
    PermissionError [WinError 32]。而且 taskkill 返回后文件句柄不一定立刻释放，
    所以要轮询等它真的从 tasklist 里消失。
    """
    exe = APP_EXE
    try:
        r = subprocess.run(["taskkill", "/IM", exe, "/F"],
                           capture_output=True, text=True, check=False,
                           creationflags=0x08000000)
        killed = r.returncode == 0
    except Exception:
        return True          # taskkill 不可用就算了，让后面自己去撞报错

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + exe, "/NH"],
                                 capture_output=True, text=True, check=False,
                                 creationflags=0x08000000).stdout
        except Exception:
            return True
        if exe.lower() not in out.lower():
            return killed
        time.sleep(0.5)
    return False


def create_autostart_task(exe, workdir):
    """注册「登录后延迟 30 秒」的计划任务（当前用户，无需管理员）

    注意：这里不能用 schtasks.exe —— 实测在普通用户会话里 /Create 会报
    "Access is denied"，而 PowerShell 的 Register-ScheduledTask 可以正常建用户任务。
    """
    ps = (
        "$ErrorActionPreference='Stop';"
        "$a=New-ScheduledTaskAction -Execute '{exe}' -WorkingDirectory '{wd}';"
        "$t=New-ScheduledTaskTrigger -AtLogOn -User '{user}';"
        "$t.Delay='PT{sec}S';"
        "$s=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries -StartWhenAvailable "
        "-ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew;"
        "Register-ScheduledTask -TaskName '{name}' -Action $a -Trigger $t "
        "-Settings $s -Description 'QuickFind - 登录 30 秒后自动启动' -Force | Out-Null"
    ).format(exe=exe.replace("'", "''"), wd=workdir.replace("'", "''"),
             user=os.environ.get("USERNAME", ""), sec=AUTOSTART_DELAY_SEC,
             name=TASK_NAME)
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-Command", ps], capture_output=True, text=True, check=False,
                       creationflags=0x08000000)
    if r.returncode != 0:
        return False, (r.stderr or r.stdout).strip()
    return True, ""


def remove_legacy_startup_shortcut():
    """清掉旧版本（<=0.9.3）留在「启动」文件夹里的快捷方式"""
    old = os.path.join(STARTUP, APP_NAME + ".lnk")
    if os.path.exists(old):
        try:
            os.remove(old)
            return True
        except OSError:
            pass
    return False


def main():
    say("=" * 56)
    say("  QuickFind 安装程序  v%s" % VERSION)
    say("=" * 56)

    src_dir = os.path.join(BUNDLE, APP_NAME)   # --add-data 嵌入的整个 onedir 目录
    src_exe = os.path.join(src_dir, APP_EXE)
    if not os.path.isfile(src_exe):
        say("错误：安装包内缺少 %s\\%s" % (APP_NAME, APP_EXE))
        return 1

    say("[1/5] 创建安装目录：%s" % INSTALL_DIR)
    os.makedirs(INSTALL_DIR, exist_ok=True)

    say("[2/5] 复制程序文件")
    if stop_running_app():
        say("      已结束正在运行的程序（升级覆盖需要）")
    copied, kept = copy_tree_merge(src_dir, INSTALL_DIR)
    say("      %d 个文件已写入" % copied)
    if kept:
        say("      保留已有用户数据：%s" % ", ".join(kept))
    # 安装包里不带 config.json / index.db，所以 kept 通常为空；
    # 真正要看的是安装目录里原本有没有这些文件（那就是被原样留下的）。
    existing = [n for n in ("config.json", "index.db")
                if os.path.exists(os.path.join(INSTALL_DIR, n))]
    if existing:
        say("      原有用户数据保持不动：%s" % ", ".join(existing))
    else:
        say("      config.json / index.db 将在首次启动时自动生成")
    with open(os.path.join(INSTALL_DIR, "uninstall.cmd"), "w", encoding="gbk") as f:
        f.write(UNINSTALL_CMD)

    say("[3/5] 创建快捷方式 + 开机自启")
    make_shortcut(os.path.join(START_MENU, APP_NAME + ".lnk"),
                  os.path.join(INSTALL_DIR, APP_EXE), INSTALL_DIR)
    say("      开始菜单快捷方式 已创建")
    if remove_legacy_startup_shortcut():
        say("      已清理旧版留在「启动」文件夹的快捷方式")
    ok, err = create_autostart_task(os.path.join(INSTALL_DIR, APP_EXE), INSTALL_DIR)
    if ok:
        say("      开机自启 已注册（登录后延迟 %s 秒）" % AUTOSTART_DELAY_SEC)
    else:
        say("      警告：计划任务注册失败，回退到「启动」文件夹")
        say("             %s" % err[:120])
        make_shortcut(os.path.join(STARTUP, APP_NAME + ".lnk"),
                      os.path.join(INSTALL_DIR, APP_EXE), INSTALL_DIR)

    say("[4/5] 注册卸载项")
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINST_KEY) as k:
            winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "QuickFind")
            winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, INSTALL_DIR)
            winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ,
                              os.path.join(INSTALL_DIR, APP_EXE))
            winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                              os.path.join(INSTALL_DIR, "uninstall.cmd"))
            winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        say("      已在「应用和功能」中注册")
    except Exception as ex:
        say("      警告：注册卸载项失败 %r" % (ex,))

    say("[5/5] 启动 QuickFind")
    try:
        subprocess.Popen([os.path.join(INSTALL_DIR, APP_EXE)])
    except Exception as ex:
        say("      启动失败（可稍后手动运行）%r" % (ex,))

    say("")
    say("安装完成！")
    say("  · 热键：Ctrl + Shift + /")
    say("  · 安装位置：%s" % INSTALL_DIR)
    say("  · 首次启动会在后台建立索引（约 5-30 秒），完成后即可秒搜")
    say("  · 卸载：%s\\uninstall.cmd" % INSTALL_DIR)
    if not SILENT:
        try:
            input("\n按回车关闭…")
        except EOFError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
