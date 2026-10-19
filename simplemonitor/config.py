# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Settings, stored as JSON in the user's config directory and exposed to QML
as a QQmlPropertyMap (so QML can read *and* write them, like
Plasmoid.configuration in the Plasma widget)."""

import json
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, QTimer
from PySide6.QtQml import QQmlPropertyMap

log = logging.getLogger(__name__)

# Same keys and meaning as package/contents/config/main.xml of the Plasma widget,
# plus a few desktop-only ones at the end.
DEFAULTS = {
    "skin": 0,              # 0 Default, 1 Column, 2 Minimalistic
    "bgColor": 2,           # 0 black, 1 transparent, 2 translucent
    "logo": 0,              # 0 automatic, 1.. fixed logo (see code.js "logos")
    "logoScale": 1.0,
    "showGpuTemp": True,
    "showSwap": True,
    "showUptime": True,
    "tempUnit": 0,          # 0 °C, 1 °F
    "cpuTempMode": 0,       # 0 per core, 1 average, 2 maximum
    "cpuHighTemp": 70,
    "cpuCritTemp": 85,
    "coloredCpuLoad": True,
    "flatCpuLoad": True,
    "indicatorHeight": 10,
    "updateInterval": 1.0,
    # desktop only
    "posX": -1,
    "posY": -1,
    "locked": False,
    "stayOnTop": False,
    "zoom": 1.0,
    "logoPath": "",         # custom logo image, overrides the automatic logo
    "language": "",         # "" = system language
}


def config_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericConfigLocation)
    path = Path(base) / "SimpleMonitor"
    path.mkdir(parents=True, exist_ok=True)
    return path


class Config(QObject):
    """Holds the settings. `self.map` (a QQmlPropertyMap) is given to QML as
    context property "cfg"; QML can read and write it like
    Plasmoid.configuration. Every change is saved (debounced)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.path = config_dir() / "config.json"
        self.map = QQmlPropertyMap(self)
        self._listeners = []
        data = dict(DEFAULTS)
        try:
            if self.path.exists():
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                for key, value in stored.items():
                    if key in DEFAULTS:
                        data[key] = self._coerce(key, value)
        except Exception:
            log.exception("could not read %s, using defaults", self.path)
        for key, value in data.items():
            self.map.insert(key, value)

        self._saveTimer = QTimer(self)
        self._saveTimer.setSingleShot(True)
        self._saveTimer.setInterval(500)
        self._saveTimer.timeout.connect(self.save)
        # emitted only for changes made from QML
        self.map.valueChanged.connect(self._changed_from_qml)

    def _changed_from_qml(self, key, _value):
        self._notify(key)
        self._saveTimer.start()

    @staticmethod
    def _coerce(key, value):
        default = DEFAULTS[key]
        try:
            if isinstance(default, bool):
                return bool(value)
            if isinstance(default, int):
                return int(value)
            if isinstance(default, float):
                return float(value)
            return str(value)
        except (TypeError, ValueError):
            return default

    def get(self, key):
        return self.map.value(key)

    def set(self, key, value):
        """Set from Python (insert() does not emit valueChanged, so notify ourselves)."""
        value = self._coerce(key, value)
        if self.map.value(key) != value:
            self.map.insert(key, value)
            self._notify(key)
            self._saveTimer.start()

    def on_change(self, callback):
        self._listeners.append(callback)

    def _notify(self, key):
        for cb in self._listeners:
            try:
                cb(key)
            except Exception:
                log.exception("config listener")

    def save(self):
        data = {key: self._coerce(key, self.map.value(key)) for key in DEFAULTS}
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
        except Exception:
            log.exception("could not write %s", self.path)
