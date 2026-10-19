#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Screenshots of the widget with fake Windows data (for README / tests).
usage: QT_QPA_PLATFORM=offscreen python3 tools/preview.py <prefix> [skin] [bgColor]"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
prefix = sys.argv[1]
os.environ["SIMPLEMONITOR_SCREENSHOT"] = prefix
os.environ["HOME"] = tempfile.mkdtemp()           # do not touch the real config
os.environ["XDG_CONFIG_HOME"] = os.environ["HOME"]

from simplemonitor import osinfo, systemdata                     # noqa: E402
from simplemonitor.sources import temperatures as T              # noqa: E402

osinfo.os_info = lambda: {"name": "Windows 11", "version": "25H2 (Build 26200.6899)",
                          "prettyName": "Windows 11 25H2", "logo": "", "kernelName": "NT",
                          "kernelVersion": "10.0.26200", "distroKey": ""}
systemdata.osinfo = osinfo


class FakeCollector:
    def __init__(self, interval=2.0):
        self.interval = interval
        self.latest = T.TempReading(cores=[41, 44, 39, 52, 47, 43, 40, 45], package=53,
                                    gpus=[("NVIDIA", 39.0)], source="LibreHardwareMonitor").finish()
    def start(self): pass
    def stop(self): pass


systemdata.TemperatureCollector = FakeCollector

from simplemonitor import config                                 # noqa: E402
args = [a for a in sys.argv if not a.startswith("--")]
if len(args) > 2:
    config.DEFAULTS["skin"] = int(args[2])
if len(args) > 3:
    config.DEFAULTS["bgColor"] = int(args[3])

if os.environ.get("SM_LANG"):
    config.DEFAULTS["language"] = os.environ["SM_LANG"]

from simplemonitor.app import main                               # noqa: E402
sys.exit(main(["simplemonitor"] + [a for a in sys.argv if a == "--settings"]))
