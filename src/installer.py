# -*- coding: utf-8 -*-
"""QuickFind 安装器（由 PyInstaller 编译为 QuickFind-Setup.exe）

做四件事：
  1) 把内嵌的 QuickFind.exe 装到 %LOCALAPPDATA%\\Programs\\QuickFind
  2) 建「开始菜单」快捷方式 + 「启动」快捷方式（开机自启）
  3) 注册到「应用和功能」卸载列表（HKCU，无需管理员）
  4) 附带 uninstall.cmd，可一键卸载
用法：直接双击；或 QuickFind-Setup.exe /S  静默安装
"""
import os
import shutil
import subprocess
import sys
import winreg

APP_NAME = "QuickFind"
APP_DESC = "QuickFind - 个人高速文件查询工具 (Ctrl+Shift+/)"
APP_EXE = "QuickFind.exe"
VERSION = "0.9.2 Beta"

LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
INSTALL_DIR = os.path.join(LOCALAPPDATA, "Programs", APP_NAME)
START_MENU = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
STARTUP = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
UNINST_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\\" + APP_NAME

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
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\QuickFind" /f >nul 2>&1
taskkill /IM QuickFind.exe /F >nul 2>&1
echo 删除程序文件...
start "" /b cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q %APP%"
echo 卸载完成。
'''


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


def main():
    say("=" * 56)
    say("  QuickFind 安装程序  v%s" % VERSION)
    say("=" * 56)

    src_exe = os.path.join(BUNDLE, APP_EXE)
    if not os.path.isfile(src_exe):
        say("错误：安装包内缺少 %s" % APP_EXE)
        return 1

    say("[1/5] 创建安装目录：%s" % INSTALL_DIR)
    os.makedirs(INSTALL_DIR, exist_ok=True)

    say("[2/5] 复制程序文件")
    shutil.copy2(src_exe, os.path.join(INSTALL_DIR, APP_EXE))
    # 配置：由程序首次启动时自行生成（保留用户已有配置）
    if os.path.exists(os.path.join(INSTALL_DIR, "config.json")):
        say("      保留已有 config.json")
    else:
        say("      config.json 将在首次启动时自动生成")
    with open(os.path.join(INSTALL_DIR, "uninstall.cmd"), "w", encoding="gbk") as f:
        f.write(UNINSTALL_CMD)

    say("[3/5] 创建快捷方式")
    make_shortcut(os.path.join(START_MENU, APP_NAME + ".lnk"),
                  os.path.join(INSTALL_DIR, APP_EXE), INSTALL_DIR)
    make_shortcut(os.path.join(STARTUP, APP_NAME + ".lnk"),
                  os.path.join(INSTALL_DIR, APP_EXE), INSTALL_DIR)
    say("      开始菜单 + 开机启动 已创建")

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
