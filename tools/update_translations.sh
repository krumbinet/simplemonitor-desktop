#!/bin/sh
# SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Updates po/simplemonitor.pot from QML + Python sources and merges it into po/*.po.
#   tools/update_translations.sh        update all
#   tools/update_translations.sh fr     start a French translation
# Requires gettext (xgettext, msgmerge, msgcat).
set -e
cd "$(dirname "$0")/.."
VERSION=$(python3 -c "import simplemonitor;print(simplemonitor.__version__)")
find simplemonitor/qml -name '*.qml' -o -name '*.js' | sort > /tmp/sm_qml.lst
xgettext --from-code=UTF-8 -C --kde -ci18n -ki18n:1 -ki18nc:1c,2 -f /tmp/sm_qml.lst -o /tmp/sm_qml.pot
find simplemonitor -name '*.py' | sort > /tmp/sm_py.lst
xgettext --from-code=UTF-8 -L Python -k_ -kpgettext:1c,2 -f /tmp/sm_py.lst -o /tmp/sm_py.pot
msgcat --use-first /tmp/sm_qml.pot /tmp/sm_py.pot -o po/simplemonitor.pot
sed -i -e 's/charset=CHARSET/charset=UTF-8/' \
       -e "s/Project-Id-Version: PACKAGE VERSION/Project-Id-Version: $VERSION/" po/simplemonitor.pot
rm -f /tmp/sm_qml.lst /tmp/sm_py.lst /tmp/sm_qml.pot /tmp/sm_py.pot
if [ -n "$1" ] && [ ! -f "po/$1.po" ]; then
    msginit --no-translator -l "$1" -i po/simplemonitor.pot -o "po/$1.po"
fi
for po in po/*.po; do
    msgmerge -q -U --backup=none "$po" po/simplemonitor.pot
done
echo "Updated. Compile with: python3 tools/compile_translations.py"
