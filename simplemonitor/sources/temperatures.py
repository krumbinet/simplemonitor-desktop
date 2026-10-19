# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""CPU and GPU temperatures.

Windows has no usable standard API for CPU temperatures. They are read from
LibreHardwareMonitor (or OpenHardwareMonitor) if it is running – those tools
ship the needed driver and publish their sensors via WMI. NVIDIA GPUs are also
read directly through NVML (part of the NVIDIA driver).

Linux: psutil (hwmon: coretemp, k10temp, zenpower, amdgpu, ...) and NVML.

Everything here runs in a background thread because WMI and NVML calls can
take a few milliseconds and must not block the UI.
"""

import logging
import math
import re
import sys
import threading
import time
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class TempReading:
    cores: list = field(default_factory=list)   # °C per core, in order
    package: float = math.nan                  # CPU package / Tctl
    average: float = math.nan
    maximum: float = math.nan
    gpus: list = field(default_factory=list)    # [(name, °C), ...]
    source: str = ""                           # human readable, for the settings dialog

    def finish(self):
        if math.isnan(self.average):
            self.average = sum(self.cores) / len(self.cores) if self.cores else self.package
        if math.isnan(self.maximum):
            values = self.cores + ([self.package] if not math.isnan(self.package) else [])
            self.maximum = max(values) if values else math.nan
        return self


def _num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) and -50 < f < 200 else math.nan
    except (TypeError, ValueError):
        return math.nan


# ---------------------------------------------------------------------------
# NVIDIA (Windows + Linux)

class NvmlSource:
    def __init__(self):
        self.ok = False
        self.handles = []
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nv = pynvml
            for i in range(pynvml.nvmlDeviceGetCount()):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode(errors="replace")
                self.handles.append((h, name))
            self.ok = bool(self.handles)
        except Exception as e:  # no NVIDIA driver, no pynvml, ...
            log.info("NVML not available: %s", e)

    def read(self):
        out = []
        for h, name in self.handles:
            try:
                t = self.nv.nvmlDeviceGetTemperature(h, self.nv.NVML_TEMPERATURE_GPU)
                out.append((name, float(t)))
            except Exception:
                pass
        return out


# ---------------------------------------------------------------------------
# Windows: LibreHardwareMonitor / OpenHardwareMonitor via WMI

_CORE_RE = re.compile(r"^(?:CPU )?Core #(\d+)$", re.I)


class WmiHardwareMonitorSource:
    NAMESPACES = ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor")

    def __init__(self):
        self.service = None
        self.name = ""
        self._next_try = 0.0

    def _connect(self):
        if self.service is not None or time.monotonic() < self._next_try:
            return self.service is not None
        self._next_try = time.monotonic() + 15      # retry every 15 s (tool may start later)
        try:
            import win32com.client
            for ns in self.NAMESPACES:
                try:
                    svc = win32com.client.GetObject("winmgmts:\\\\.\\" + ns)
                    # the namespace exists only while the tool is running
                    list(svc.ExecQuery("SELECT Name FROM Hardware"))
                    self.service = svc
                    self.name = ns.split("\\")[-1]
                    log.info("using %s for temperatures", self.name)
                    return True
                except Exception:
                    continue
        except Exception as e:
            log.info("pywin32/WMI not available: %s", e)
        return False

    def read(self):
        """Returns TempReading or None if no hardware monitor is running."""
        if not self._connect():
            return None
        try:
            rows = list(self.service.ExecQuery(
                "SELECT Name, Identifier, Value FROM Sensor WHERE SensorType='Temperature'"))
        except Exception:
            self.service = None                     # tool was closed
            return None
        r = TempReading(source=self.name)
        cores = {}
        gpus = {}
        for row in rows:
            name, ident, value = str(row.Name), str(row.Identifier), _num(row.Value)
            if math.isnan(value):
                continue
            hw = ident.split("/")[1] if ident.count("/") >= 2 else ""
            if hw.startswith("gpu") or "gpu" in hw:
                key = "/".join(ident.split("/")[:3])
                prev = gpus.get(key)
                # prefer "GPU Core", otherwise the first temperature of that GPU
                if prev is None or (name.lower() == "gpu core" and prev[1] != "gpu core"):
                    gpus[key] = (value, name.lower(), hw)
            elif "cpu" in hw:
                if "distance" in name.lower() or "tjmax" in name.lower():
                    continue
                m = _CORE_RE.match(name)
                if m:
                    cores[int(m.group(1))] = value
                elif name.lower() in ("cpu package", "core (tctl/tdie)", "core (tctl)", "tctl", "package"):
                    r.package = value
                elif name.lower() == "core average":
                    r.average = value
                elif name.lower() == "core max":
                    r.maximum = value
        r.cores = [cores[k] for k in sorted(cores)]
        for key in sorted(gpus):
            value, _n, hw = gpus[key]
            vendor = "NVIDIA" if "nvidia" in hw else "AMD" if "amd" in hw or "ati" in hw else "Intel" if "intel" in hw else ""
            r.gpus.append((vendor, value))
        return r.finish()


# ---------------------------------------------------------------------------
# Linux: psutil / hwmon

class PsutilSource:
    CPU_CHIPS = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "k8temp", "acpitz")
    GPU_CHIPS = ("amdgpu", "radeon", "nouveau", "i915", "xe")

    def read(self):
        try:
            import psutil
            temps = psutil.sensors_temperatures()
        except Exception:
            return None
        if not temps:
            return None
        r = TempReading(source="hwmon")
        for chip in self.CPU_CHIPS:
            entries = temps.get(chip)
            if not entries:
                continue
            cores = {}
            for e in entries:
                label = (e.label or "").strip()
                m = re.match(r"^Core (\d+)$", label)
                if m:
                    cores[int(m.group(1))] = _num(e.current)
                elif label.lower().startswith(("package id", "tctl", "tdie")) or (chip != "coretemp" and not label):
                    if math.isnan(r.package):
                        r.package = _num(e.current)
            r.cores = [cores[k] for k in sorted(cores) if not math.isnan(cores[k])]
            if r.cores or not math.isnan(r.package):
                break
        for chip in self.GPU_CHIPS:
            for e in temps.get(chip, []):
                label = (e.label or "").lower()
                if label in ("", "edge", "temp1", "gpu"):
                    v = _num(e.current)
                    if not math.isnan(v):
                        r.gpus.append((chip, v))
                        break
        return r.finish()


# ---------------------------------------------------------------------------

class TemperatureCollector:
    """Polls the sources in a daemon thread; `latest` is read by the UI."""

    def __init__(self, interval=2.0):
        self.interval = interval
        self.latest = TempReading().finish()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="temperatures", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
            primary = WmiHardwareMonitorSource()
        else:
            primary = PsutilSource()
        nvml = NvmlSource()
        while not self._stop.is_set():
            try:
                r = primary.read() or TempReading()
                if nvml.ok:
                    has_nvidia = any(n.upper() == "NVIDIA" or n == "nouveau" for n, _t in r.gpus)
                    if not has_nvidia:
                        r.gpus = r.gpus + nvml.read()
                    if not r.source:
                        r.source = "NVML"
                self.latest = r.finish()
            except Exception:
                log.exception("reading temperatures failed")
            self._stop.wait(max(0.5, self.interval))
