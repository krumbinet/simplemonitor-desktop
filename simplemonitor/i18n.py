# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Translations. Provides i18n()/i18nc() to QML (same API as KDE's KI18n, so the
skins shared with the Plasma widget work unchanged) and _() for Python code.
Catalogs: simplemonitor/locale/<lang>/LC_MESSAGES/simplemonitor.mo"""

import gettext
import re
from pathlib import Path

from PySide6.QtCore import QLocale, QObject, Slot

DOMAIN = "simplemonitor"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"

_translation = gettext.NullTranslations()


def setup(language: str = "") -> str:
    """Loads the catalog for `language` ("" = system language). Returns the language used."""
    global _translation
    if not language:
        language = QLocale.system().name()          # e.g. "de_DE"
    candidates = [language, language.split("_")[0]]
    _translation = gettext.translation(DOMAIN, LOCALE_DIR, languages=candidates, fallback=True)
    return language


def _subst(text: str, args) -> str:
    def repl(m):
        n = int(m.group(1))
        if 1 <= n <= len(args):
            a = args[n - 1]
            if isinstance(a, float) and a.is_integer():
                a = int(a)
            return str(a)
        return m.group(0)
    return re.sub(r"%(\d)", repl, text)


def _(text: str, *args) -> str:
    return _subst(_translation.gettext(text), args)


def pgettext(context: str, text: str, *args) -> str:
    return _subst(_translation.pgettext(context, text), args)


class QmlI18n(QObject):
    """Set as context object of the QML root context."""

    @Slot(str, result=str)
    @Slot(str, "QVariant", result=str)
    @Slot(str, "QVariant", "QVariant", result=str)
    @Slot(str, "QVariant", "QVariant", "QVariant", result=str)
    def i18n(self, text, *args):
        return _(text, *args)

    @Slot(str, str, result=str)
    @Slot(str, str, "QVariant", result=str)
    @Slot(str, str, "QVariant", "QVariant", result=str)
    def i18nc(self, context, text, *args):
        return pgettext(context, text, *args)
