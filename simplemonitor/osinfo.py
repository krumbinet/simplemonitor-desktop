# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Name/version of the operating system and kernel, shown below the logo."""

import platform
import re
import sys

# Same mapping as detectDistro() in qml/contents/code/code.js
_ALIASES = {
    "tux": "tux", "linux": "tux", "slackware": "slackware", "ubuntu": "ubuntu",
    "kubuntu": "kubuntu", "neon": "kubuntu", "opensuse": "opensuse",
    "opensuse-tumbleweed": "opensuse", "opensuse-leap": "opensuse", "suse": "opensuse",
    "manjaro": "manjaro", "arch": "arch", "archlinux": "arch", "endeavouros": "arch",
    "fedora": "fedora", "debian": "debian",
}


def detect_distro(*candidates) -> str:
    for c in candidates:
        c = (c or "").lower().strip()
        if not c:
            continue
        if c in _ALIASES:
            return _ALIASES[c]
        for word in re.split(r"[^a-z]+", c):
            if word not in ("logo", "distributor") and word in _ALIASES:
                return _ALIASES[word]
    return ""


def os_info() -> dict:
    """Returns name, version, prettyName, logo (icon name, Linux only),
    kernelName, kernelVersion, distroKey."""
    if sys.platform == "win32":
        return _windows()
    return _linux()


def _windows() -> dict:
    info = {"name": "Windows", "version": "", "prettyName": "Windows", "logo": "",
            "kernelName": "NT", "kernelVersion": platform.version(), "distroKey": ""}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
            def val(name, default=""):
                try:
                    return winreg.QueryValueEx(k, name)[0]
                except OSError:
                    return default
            build = int(val("CurrentBuildNumber", val("CurrentBuild", "0")) or 0)
            ubr = val("UBR", "")
            display = val("DisplayVersion", "") or val("ReleaseId", "")
            # ProductName still says "Windows 10" on Windows 11, the build number does not lie
            info["name"] = "Windows 11" if build >= 22000 else "Windows 10" if build >= 10240 else "Windows"
            build_str = f"{build}.{ubr}" if ubr != "" else str(build)
            info["version"] = f"{display} (Build {build_str})" if display else f"(Build {build_str})"
            info["prettyName"] = f"{info['name']} {display}".strip()
    except Exception:
        pass
    return info


def _linux() -> dict:
    rel = {}
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.rstrip("\n").split("=", 1)
                        rel[k] = v.strip().strip('"').strip("'")
            break
        except OSError:
            continue
    name = rel.get("NAME", platform.system())
    version = rel.get("VERSION", rel.get("VERSION_ID", ""))
    logo = rel.get("LOGO", "")
    kernel = platform.release()
    return {
        "name": name, "version": version,
        "prettyName": rel.get("PRETTY_NAME", f"{name} {version}".strip()),
        "logo": logo,
        "kernelName": platform.system() or "Linux",
        "kernelVersion": kernel.split("-")[0],
        "distroKey": detect_distro(logo, name, rel.get("ID", ""), rel.get("PRETTY_NAME", "")),
    }
