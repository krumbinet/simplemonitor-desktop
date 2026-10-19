# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Start with the system: Windows registry Run key / XDG autostart on Linux."""

import os
import shlex
import sys
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "SimpleMonitor"


def _command():
    if getattr(sys, "frozen", False):                       # PyInstaller build
        return [sys.executable]
    exe = sys.executable
    if sys.platform == "win32":
        pyw = Path(exe).with_name("pythonw.exe")
        if pyw.exists():
            exe = str(pyw)
    return [exe, "-m", "simplemonitor"]


def _desktop_file():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "autostart" / "simplemonitor.desktop"


def is_enabled() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.QueryValueEx(k, VALUE)
            return True
        except OSError:
            return False
    return _desktop_file().exists()


def set_enabled(enabled: bool):
    cmd = _command()
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, VALUE, 0, winreg.REG_SZ, " ".join(f'"{c}"' for c in cmd))
            else:
                try:
                    winreg.DeleteValue(k, VALUE)
                except OSError:
                    pass
        return
    f = _desktop_file()
    if enabled:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            "[Desktop Entry]\nType=Application\nName=Simple Monitor\n"
            f"Exec={shlex.join(cmd)}\nX-GNOME-Autostart-enabled=true\n"
            "Comment=Desktop system monitor\n", encoding="utf-8")
    elif f.exists():
        f.unlink()
