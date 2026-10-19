#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copies the shared QML skins, widgets, fonts and images from the Plasma 6
widget (https://github.com/krumbinet/plasma-simplemonitor6) into this project,
so both stay visually identical.

usage: python3 tools/sync_from_plasma.py /path/to/plasma-simplemonitor6
"""
import shutil, sys
from pathlib import Path

SHARED = [
    "contents/code",
    "contents/fonts",
    "contents/images",
    "contents/ui/skins",
    "contents/ui/monitorWidgets",
    "contents/ui/components",
]

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "package"
    dst = Path(__file__).resolve().parent.parent / "simplemonitor" / "qml"
    if not (src / "metadata.json").exists():
        sys.exit(f"{src} is not the Plasma widget package")
    for rel in SHARED:
        s, d = src / rel, dst / rel
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(s, d)
        print("synced", rel)
    # the plasma po files are the base for our translations (same msgids)
    print("Done. Run tools/update_translations.sh afterwards.")

if __name__ == "__main__":
    main()
