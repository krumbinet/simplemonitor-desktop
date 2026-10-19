# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#
# PyInstaller build:  pyinstaller packaging/simplemonitor.spec --noconfirm
# Result: dist/SimpleMonitor/SimpleMonitor(.exe) plus the _internal folder.

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
PKG = ROOT / "simplemonitor"

hidden = ["pynvml", "psutil"]
if sys.platform == "win32":
    hidden += ["win32com", "win32com.client", "pythoncom", "pywintypes"]

a = Analysis(
    [str(ROOT / "packaging" / "run.py")],
    pathex=[str(ROOT)],
    datas=[(str(PKG / "qml"), "simplemonitor/qml"),
           (str(PKG / "locale"), "simplemonitor/locale")],
    hiddenimports=hidden,
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.QtWebEngineQuick", "PySide6.Qt3DCore", "PySide6.QtCharts",
              "PySide6.QtDataVisualization", "PySide6.QtMultimedia", "PySide6.QtPdf",
              "PySide6.QtQuick3D", "PySide6.QtLocation", "PySide6.QtPositioning",
              "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtSql", "PySide6.QtTest",
              "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtSerialPort",
              "PySide6.QtWebSockets", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
              "PySide6.QtTextToSpeech", "PySide6.QtSpatialAudio", "PySide6.QtGraphs",
              "PySide6.QtSensors", "PySide6.QtHttpServer"],
)

# PySide6's hook collects every QML module; keep only what we use.
DROP = ("QtQuick3D", "QtWebEngine", "QtWebView", "QtWebChannel", "QtMultimedia", "QtLocation",
        "QtPositioning", "QtCharts", "QtDataVisualization", "QtGraphs", "Qt3D", "QtSensors",
        "QtTest", "QtRemoteObjects", "QtScxml", "QtTextToSpeech", "QtVirtualKeyboard",
        "QtQuickEffectMaker", "QtSpatialAudio", "QtPdf", "Qt5Compat", "QtNetworkAuth",
        "Controls/Material", "Controls/Universal", "Controls/Imagine", "Controls/FluentWinUI3",
        "Controls/iOS", "Controls/macOS", "Controls/designer", "QtQuick/Timeline",
        "QtQuick/Particles", "QtQuick/Scene2D", "QtQuick/Scene3D", "QtQuick/VirtualKeyboard",
        "QtQuick/Pdf", "QtQuick/LocalStorage", "QtQuick/Shapes/DesignHelpers",
        "Qt6WebEngine", "Qt6Quick3D", "Qt6Multimedia", "Qt6Pdf", "Qt6Charts", "Qt6Graphs",
        "Qt6DataVisualization", "Qt63D", "Qt6Location", "Qt6Positioning", "Qt6VirtualKeyboard",
        "Qt6ShaderTools", "Qt6Sensors", "Qt6Test", "Qt6RemoteObjects", "Qt6Scxml",
        "Qt6TextToSpeech", "Qt6SpatialAudio", "Qt6Bluetooth", "Qt6Nfc", "Qt6Sql",
        "Qt6Designer", "Qt6Help", "Qt6SerialPort", "Qt6WebSockets", "Qt6WebView",
        "Qt6WebChannel", "Qt6QuickTimeline", "Qt6QuickParticles", "Qt6Quick3D",
        "Qt6QuickControls2Material", "Qt6QuickControls2Universal", "Qt6QuickControls2Imagine",
        "Qt6QuickControls2FluentWinUI3", "Qt6QuickControls2IOS", "Qt6QuickControls2MacOS",
        "Qt6Qml/QtQuick3D", "Qt6Pdf", "Qt6HttpServer", "Qt6NetworkAuth", "Qt6Quick3DPhysics",
        "translations/qtwebengine")


def keep(entry):
    path = entry[0].replace("\\", "/")
    return not any(d in path for d in DROP)


a.datas = [e for e in a.datas if keep(e)]
a.binaries = [e for e in a.binaries if keep(e)]

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="SimpleMonitor",
    console=False,
    icon=str(ROOT / "packaging" / "simplemonitor.ico"),
    version=str(ROOT / "packaging" / "version_info.txt") if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="SimpleMonitor", strip=False, upx=False)
