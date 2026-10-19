@echo off
rem SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Local Windows build. Needs Python 3.10+ from python.org (with "Add to PATH").
cd /d "%~dp0\.."
python -m pip install -r requirements.txt -r requirements-build.txt || goto :error
python tools\compile_translations.py || goto :error
pyinstaller packaging\simplemonitor.spec --noconfirm || goto :error
echo.
echo Fertig / Done: dist\SimpleMonitor\SimpleMonitor.exe
pause
exit /b 0
:error
echo Build failed.
pause
exit /b 1
