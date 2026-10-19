#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compiles po/<lang>.po to simplemonitor/locale/<lang>/LC_MESSAGES/simplemonitor.mo
(pure Python via polib, so it also works on Windows without gettext)."""
from pathlib import Path

import polib

root = Path(__file__).resolve().parent.parent
for po_path in sorted((root / "po").glob("*.po")):
    lang = po_path.stem
    out = root / "simplemonitor" / "locale" / lang / "LC_MESSAGES" / "simplemonitor.mo"
    out.parent.mkdir(parents=True, exist_ok=True)
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(out))
    print(f"{lang}: {po.percent_translated()}% -> {out.relative_to(root)}")
