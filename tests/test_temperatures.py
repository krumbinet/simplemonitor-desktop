# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parsing of LibreHardwareMonitor (WMI) and hwmon sensor lists – runs on any OS:
    python3 -m pytest tests   or   python3 tests/test_temperatures.py"""
import math
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from simplemonitor.sources import temperatures as T  # noqa: E402


class Row:
    def __init__(self, name, ident, value):
        self.Name, self.Identifier, self.Value = name, ident, value


class FakeService:
    def __init__(self, rows):
        self.rows = rows

    def ExecQuery(self, q):
        return self.rows


def wmi(rows):
    s = T.WmiHardwareMonitorSource()
    s.service = FakeService(rows)
    s.name = "LibreHardwareMonitor"
    return s.read()


def test_intel_lhm():
    r = wmi([
        Row("CPU Core #1", "/intelcpu/0/temperature/0", 41.0),
        Row("CPU Core #2", "/intelcpu/0/temperature/1", 45.0),
        Row("CPU Core #1 Distance to TjMax", "/intelcpu/0/temperature/8", 59.0),
        Row("CPU Package", "/intelcpu/0/temperature/16", 47.0),
        Row("Core Max", "/intelcpu/0/temperature/17", 45.0),
        Row("Core Average", "/intelcpu/0/temperature/18", 43.0),
        Row("GPU Hot Spot", "/gpu-nvidia/0/temperature/2", 50.0),
        Row("GPU Core", "/gpu-nvidia/0/temperature/0", 39.0),
        Row("Temperature", "/nvme/0/temperature/0", 33.0),
    ])
    assert r.cores == [41.0, 45.0]
    assert r.package == 47.0 and r.average == 43.0 and r.maximum == 45.0
    assert r.gpus == [("NVIDIA", 39.0)]


def test_amd_lhm_without_cores():
    r = wmi([
        Row("Core (Tctl/Tdie)", "/amdcpu/0/temperature/2", 62.5),
        Row("CCD1 (Tdie)", "/amdcpu/0/temperature/3", 60.0),
        Row("GPU Core", "/gpu-amd/0/temperature/0", 51.0),
    ])
    assert r.cores == [] and r.package == 62.5
    assert r.average == 62.5 and r.maximum == 62.5
    assert r.gpus == [("AMD", 51.0)]


def test_hwmon(monkeypatch=None):
    E = lambda label, cur: types.SimpleNamespace(label=label, current=cur)  # noqa: E731
    fake = {"coretemp": [E("Package id 0", 48.0), E("Core 0", 33.0), E("Core 1", 35.0)],
            "amdgpu": [E("edge", 44.0), E("junction", 50.0)],
            "nvme": [E("Composite", 32.9)]}
    import psutil
    # psutil has no sensors_temperatures() on Windows/macOS – add it temporarily
    missing = object()
    old = getattr(psutil, "sensors_temperatures", missing)
    psutil.sensors_temperatures = lambda: fake
    try:
        r = T.PsutilSource().read()
    finally:
        if old is missing:
            del psutil.sensors_temperatures
        else:
            psutil.sensors_temperatures = old
    assert r.cores == [33.0, 35.0] and r.package == 48.0
    assert r.maximum == 48.0 and math.isclose(r.average, 34.0)
    assert r.gpus == [("amdgpu", 44.0)]


def test_coretemp():
    d = T.CoreTempSharedDataEx()
    assert T.ctypes.sizeof(d) == 4740          # size of the documented layout
    assert T.parse_coretemp(d) is None         # Core Temp not running / empty block
    d.uiCoreCnt, d.uiCPUCnt = 4, 1
    for i, v in enumerate([40.0, 42.0, 44.0, 46.0]):
        d.fTemp[i] = v
    r = T.parse_coretemp(d)
    assert r.cores == [40.0, 42.0, 44.0, 46.0] and r.maximum == 46.0 and r.average == 43.0
    assert r.source == "Core Temp"
    d.ucDeltaToTjMax, d.uiTjMax[0] = 1, 100    # "distance to TjMax" mode
    assert T.parse_coretemp(d).cores == [60.0, 58.0, 56.0, 54.0]
    d.ucDeltaToTjMax, d.ucFahrenheit = 0, 1     # Fahrenheit mode
    d.fTemp[0] = 104.0
    assert T.parse_coretemp(d).cores[0] == 40.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
