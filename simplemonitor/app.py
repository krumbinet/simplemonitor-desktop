# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Application start-up: window, tray icon, menu, settings window."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

from PySide6.QtCore import (QLockFile, QObject, QSize, QStandardPaths, Qt, QUrl, Property,
                            Signal, Slot, qInstallMessageHandler, QtMsgType)
from PySide6.QtGui import QAction, QCursor, QFontDatabase, QIcon, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from . import APP_DISPLAY_NAME, APP_NAME, HOMEPAGE, PLASMA_HOMEPAGE, __version__, autostart, i18n
from .config import Config, config_dir
from .i18n import _
from .systemdata import QML_DIR, SystemData

log = logging.getLogger("simplemonitor")
IS_WINDOWS = sys.platform == "win32"
UI_DIR = QML_DIR / "contents" / "ui"
LOGO = QML_DIR / "contents" / "images" / "simplemonitor-logo.svg"


class ThemeIconProvider(QQuickImageProvider):
    """image://theme/<name> – icons of the desktop theme (Linux distribution logos)."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, name, size, requested):
        icon = QIcon.fromTheme(name)
        if icon.isNull():
            return QPixmap()
        s = requested if requested.isValid() and requested.width() > 0 else QSize(256, 256)
        return icon.pixmap(s)


class Controller(QObject):
    """Context property "app": actions used by the QML side."""

    logoEditModeChanged = Signal()
    autostartChanged = Signal()

    def __init__(self, application, config, sysdata):
        super().__init__()
        self.qapp = application
        self.cfg = config
        self.sysdata = sysdata
        self.engine = None
        self._logoEdit = False
        self._settings = None
        self.menu = QMenu()
        self._build_menu()
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(QIcon(str(LOGO)), self)
            self.tray.setToolTip(APP_DISPLAY_NAME)
            self.tray.setContextMenu(self.menu)
            self.tray.activated.connect(self._tray_activated)
            self.tray.show()

    # ---- menu -------------------------------------------------------------
    def _build_menu(self):
        m = self.menu
        m.clear()
        m.addAction(_("Settings…"), self.openSettings)
        m.addSeparator()
        self.actLock = QAction(_("Lock position"), m, checkable=True)
        self.actLock.toggled.connect(lambda on: self.cfg.set("locked", on))
        m.addAction(self.actLock)
        self.actTop = QAction(_("Always on top"), m, checkable=True)
        self.actTop.toggled.connect(lambda on: self.cfg.set("stayOnTop", on))
        m.addAction(self.actTop)
        self.actLogo = QAction(_("Unlock image scaling"), m)
        self.actLogo.triggered.connect(lambda: setattr(self, "logoEditMode", not self._logoEdit))
        m.addAction(self.actLogo)
        self.actAuto = QAction(_("Start with the system"), m, checkable=True)
        self.actAuto.toggled.connect(lambda on: setattr(self, "autostart", on))
        m.addAction(self.actAuto)
        m.addSeparator()
        m.addAction(_("About Simple Monitor"), self.about)
        m.addAction(_("Quit"), self.qapp.quit)
        m.aboutToShow.connect(self._sync_menu)

    def _sync_menu(self):
        for act, on in ((self.actLock, bool(self.cfg.get("locked"))),
                        (self.actTop, bool(self.cfg.get("stayOnTop"))),
                        (self.actAuto, autostart.is_enabled())):
            act.blockSignals(True)
            act.setChecked(on)
            act.blockSignals(False)
        self.actLogo.setText(_("Lock image scaling") if self._logoEdit else _("Unlock image scaling"))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.openSettings()

    @Slot()
    def showContextMenu(self):
        self._sync_menu()
        self.menu.popup(QCursor.pos())

    # ---- settings window ------------------------------------------------------
    @Slot()
    def openSettings(self):
        if self._settings is not None:
            self._settings.show()
            self._settings.raise_()
            self._settings.requestActivate()
            return
        before = set(self.engine.rootObjects())
        self.engine.load(QUrl.fromLocalFile(str(UI_DIR / "desktop" / "Settings.qml")))
        new = [o for o in self.engine.rootObjects() if o not in before]
        if new:
            self._settings = new[0]
            self._settings.setIcon(QIcon(str(LOGO)))

    @Slot()
    def resetPosition(self):
        self.cfg.set("posX", -1)
        self.cfg.set("posY", -1)
        win = self.engine.rootObjects()[0]
        win.placeInitially()

    @Slot(QUrl, result=str)
    def localPath(self, url):
        return url.toLocalFile()

    @Slot()
    def about(self):
        QMessageBox.about(
            None, _("About Simple Monitor"),
            f"<h3>{APP_DISPLAY_NAME} {__version__}</h3>"
            + "<p>" + _("Clock, CPU load, temperatures and memory on your desktop.") + "</p>"
            + f"<p><a href='{HOMEPAGE}'>{HOMEPAGE}</a></p>"
            + "<p>" + _("Based on the KDE Plasma widget plasma-simpleMonitor by Dhaby Xiloj and Konstantin Shtepa. Plasma 6 version:")
            + f" <a href='{PLASMA_HOMEPAGE}'>{PLASMA_HOMEPAGE}</a></p>"
            + "<p>" + _("License: GNU GPL version 3 or later. Fonts: SIL Open Font License.") + "</p>"
            + "<p>" + _("Settings and log file:") + f" {config_dir()}</p>")

    # ---- properties -------------------------------------------------------------
    def _get_logo_edit(self):
        return self._logoEdit

    def _set_logo_edit(self, on):
        if on != self._logoEdit:
            self._logoEdit = on
            self.logoEditModeChanged.emit()

    logoEditMode = Property(bool, _get_logo_edit, _set_logo_edit, notify=logoEditModeChanged)

    def _get_autostart(self):
        return autostart.is_enabled()

    def _set_autostart(self, on):
        try:
            autostart.set_enabled(bool(on))
        except Exception:
            log.exception("autostart")
        self.autostartChanged.emit()

    autostart = Property(bool, _get_autostart, _set_autostart, notify=autostartChanged)

    @Property(str, constant=True)
    def version(self):
        return __version__

    @Property(str, constant=True)
    def homepage(self):
        return HOMEPAGE

    @Property(bool, constant=True)
    def isWindows(self):
        return IS_WINDOWS


def _setup_logging():
    path = config_dir() / "simplemonitor.log"
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=500_000, backupCount=1, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    if sys.stderr is not None:
        root.addHandler(logging.StreamHandler())
    root.setLevel(logging.INFO)

    qml_log = logging.getLogger("qml")

    def handler_fn(mode, context, message):
        level = {QtMsgType.QtDebugMsg: logging.DEBUG, QtMsgType.QtInfoMsg: logging.INFO,
                 QtMsgType.QtWarningMsg: logging.WARNING}.get(mode, logging.ERROR)
        qml_log.log(level, message)

    qInstallMessageHandler(handler_fn)


def _schedule_screenshots(qapp, engine, ctrl, prefix):
    from PySide6.QtCore import QMetaObject, QTimer, Q_ARG

    def grab():
        objs = engine.rootObjects()
        QMetaObject.invokeMethod(objs[0], "grabTo", Q_ARG("QVariant", prefix + "-widget.png"))
        if ctrl._settings is not None:
            QMetaObject.invokeMethod(ctrl._settings, "grabTo", Q_ARG("QVariant", prefix + "-settings.png"))
        QTimer.singleShot(1500, qapp.quit)

    QTimer.singleShot(3000, grab)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName(APP_NAME)
    QApplication.setApplicationDisplayName(APP_DISPLAY_NAME)
    QApplication.setApplicationVersion(__version__)
    if IS_WINDOWS:
        try:  # own taskbar/tray identity instead of "python"
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("krumbinet.SimpleMonitor")
        except Exception:
            pass
    QQuickStyle.setStyle("Fusion")
    qapp = QApplication(argv)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setWindowIcon(QIcon(str(LOGO)))

    _setup_logging()
    log.info("Simple Monitor %s starting on %s", __version__, sys.platform)

    # only one instance
    lock = QLockFile(os.path.join(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.TempLocation), "simplemonitor.lock"))
    if not lock.tryLock(100):
        log.info("already running")
        return 0

    cfg = Config()
    lang = i18n.setup(cfg.get("language"))
    if cfg.get("language"):
        from PySide6.QtCore import QLocale
        QLocale.setDefault(QLocale(lang))          # dates in the chosen language too
    sysdata = SystemData(cfg)
    ctrl = Controller(qapp, cfg, sysdata)

    for f in (QML_DIR / "contents" / "fonts").rglob("*.ttf"):
        QFontDatabase.addApplicationFont(str(f))

    engine = QQmlApplicationEngine()
    ctrl.engine = engine
    engine.addImportPath(str(QML_DIR / "compat"))
    engine.addImageProvider("theme", ThemeIconProvider())
    engine.rootContext().setContextObject(i18n.QmlI18n(engine))
    engine.rootContext().setContextProperty("cfg", cfg.map)
    engine.rootContext().setContextProperty("sysData", sysdata)
    engine.rootContext().setContextProperty("app", ctrl)
    engine.load(QUrl.fromLocalFile(str(UI_DIR / "desktop" / "Widget.qml")))
    if not engine.rootObjects():
        log.error("could not load the widget")
        return 1

    if "--settings" in argv:
        ctrl.openSettings()

    shot = os.environ.get("SIMPLEMONITOR_SCREENSHOT")   # development aid
    if shot:
        _schedule_screenshots(qapp, engine, ctrl, shot)

    rc = qapp.exec()
    sysdata.stop()
    cfg.save()
    # destroy the QML side first, while the objects it binds to still exist
    ctrl.engine = None
    ctrl._settings = None
    del engine
    lock.unlock()
    return rc
