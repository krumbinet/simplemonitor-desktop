# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Python counterpart of SystemData.qml of the Plasma widget: offers exactly
the same properties and models, so the shared skins work unchanged.
Exposed to QML as context property "sysData"."""

import math
import time
from pathlib import Path

import psutil
from PySide6.QtCore import (QAbstractListModel, QByteArray, QModelIndex, QObject, Qt,
                            QTimer, QUrl, Property, Signal)

from . import osinfo
from .i18n import _
from .sources.temperatures import TemperatureCollector

GIB = 1024 ** 3
QML_DIR = Path(__file__).resolve().parent / "qml"
DEFAULT_LOGO = QML_DIR / "contents" / "images" / "simplemonitor-logo.svg"


class RowModel(QAbstractListModel):
    """List model with fixed role names, filled with a list of dicts."""

    def __init__(self, roles, parent=None):
        super().__init__(parent)
        self._roles = list(roles)
        self._rows = []

    def roleNames(self):
        return {Qt.UserRole + i: QByteArray(r.encode()) for i, r in enumerate(self._roles)}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        i = role - Qt.UserRole
        if 0 <= i < len(self._roles):
            return self._rows[index.row()].get(self._roles[i])
        return None

    def set_rows(self, rows):
        if len(rows) != len(self._rows):
            self.beginResetModel()
            self._rows = rows
            self.endResetModel()
        elif rows != self._rows:
            self._rows = rows
            self.dataChanged.emit(self.index(0), self.index(len(rows) - 1))



class SystemData(QObject):
    changed = Signal()
    osChanged = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.cfg = config
        self._cpu = RowModel(["val"], self)
        self._coreTemps = RowModel(["val", "avail"], self)
        self._gpuTemps = RowModel(["val", "avail", "gpuLabel"], self)
        self._v = dict(cpuCount=0, cpuAvgLoad=0.0, cpuAvgTemp=math.nan, cpuMaxTemp=math.nan,
                       memTotal=0.0, memUsed=0.0, swapTotal=0.0, swapUsed=0.0, uptime=0,
                       tempSource="")
        self._os = osinfo.os_info()

        psutil.cpu_percent(percpu=True)            # prime the counters
        self.temps = TemperatureCollector(interval=max(1.0, self.cfg.get("updateInterval")))
        self.temps.start()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._apply_interval()
        config.on_change(self._config_changed)
        QTimer.singleShot(100, self.update)

    # ---- configuration ---------------------------------------------------
    def _apply_interval(self):
        sec = max(0.1, float(self.cfg.get("updateInterval") or 1.0))
        self._timer.start(int(sec * 1000))
        self.temps.interval = max(1.0, sec)

    def _config_changed(self, key):
        if key == "updateInterval":
            self._apply_interval()
        elif key in ("logoPath", "logo"):
            self.osChanged.emit()

    # ---- polling ----------------------------------------------------------
    def update(self):
        per_cpu = psutil.cpu_percent(percpu=True)
        self._cpu.set_rows([{"val": float(v)} for v in per_cpu])
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        t = self.temps.latest
        self._coreTemps.set_rows([{"val": float(c), "avail": True} for c in t.cores])
        gpus = t.gpus if self.cfg.get("showGpuTemp") else []
        rows = []
        for i, (_name, temp) in enumerate(gpus):
            label = _("GPU:") if len(gpus) == 1 else _("GPU %1:", i)
            rows.append({"val": float(temp), "avail": True, "gpuLabel": label})
        self._gpuTemps.set_rows(rows)
        self._v.update(
            cpuCount=len(per_cpu),
            cpuAvgLoad=sum(per_cpu) / len(per_cpu) if per_cpu else 0.0,
            cpuAvgTemp=float(t.average), cpuMaxTemp=float(t.maximum),
            memTotal=vm.total / GIB, memUsed=(vm.total - vm.available) / GIB,
            swapTotal=sw.total / GIB, swapUsed=sw.used / GIB,
            uptime=int(time.time() - psutil.boot_time()),
            tempSource=t.source,
        )
        self.changed.emit()

    def stop(self):
        self._timer.stop()
        self.temps.stop()

    # ---- models -----------------------------------------------------------
    @Property(QObject, constant=True)
    def cpuModel(self):
        return self._cpu

    @Property(QObject, constant=True)
    def coreTempModel(self):
        return self._coreTemps

    @Property(QObject, constant=True)
    def gpuTempModel(self):
        return self._gpuTemps

    # ---- values (same names as SystemData.qml) ------------------------------
    def _g(name):  # noqa: N805 – helper to build read-only properties
        return lambda self: self._v[name]

    cpuCount = Property(int, _g("cpuCount"), notify=changed)
    cpuAvgLoad = Property(float, _g("cpuAvgLoad"), notify=changed)
    cpuAvgTemp = Property(float, _g("cpuAvgTemp"), notify=changed)
    cpuMaxTemp = Property(float, _g("cpuMaxTemp"), notify=changed)
    memTotal = Property(float, _g("memTotal"), notify=changed)
    memUsed = Property(float, _g("memUsed"), notify=changed)
    swapTotal = Property(float, _g("swapTotal"), notify=changed)
    swapUsed = Property(float, _g("swapUsed"), notify=changed)
    uptime = Property(int, _g("uptime"), notify=changed)
    tempSource = Property(str, _g("tempSource"), notify=changed)

    @Property(int, notify=changed)
    def coreTempCount(self):
        return self._coreTemps.rowCount()

    @Property(float, notify=changed)
    def memFree(self):
        return max(0.0, self._v["memTotal"] - self._v["memUsed"])

    @Property(float, notify=changed)
    def swapFree(self):
        return max(0.0, self._v["swapTotal"] - self._v["swapUsed"])

    # ---- operating system ---------------------------------------------------
    @Property(str, notify=osChanged)
    def osName(self):
        return self._os["name"]

    @Property(str, notify=osChanged)
    def osVersion(self):
        return self._os["version"]

    @Property(str, notify=osChanged)
    def osPrettyName(self):
        return self._os["prettyName"]

    @Property(str, notify=osChanged)
    def kernelName(self):
        return self._os["kernelName"]

    @Property(str, notify=osChanged)
    def kernelVersion(self):
        return self._os["kernelVersion"]

    @Property(str, notify=osChanged)
    def osLogo(self):
        """Custom logo file, else the distribution's logo icon (Linux), else our own logo."""
        custom = self.cfg.get("logoPath")
        if custom and Path(custom).is_file():
            return QUrl.fromLocalFile(custom).toString()
        if self._os.get("logo"):
            return self._os["logo"]
        return QUrl.fromLocalFile(str(DEFAULT_LOGO)).toString()

    @Property(str, notify=osChanged)
    def distroKey(self):
        custom = self.cfg.get("logoPath")
        if custom and Path(custom).is_file():
            return ""
        return self._os["distroKey"]
