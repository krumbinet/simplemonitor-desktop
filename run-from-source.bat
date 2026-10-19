@echo off
rem Start Simple Monitor directly from the sources (Windows, Python 3.10+ needed).
cd /d "%~dp0"
python -m pip install -q -r requirements.txt polib
python tools\compile_translations.py >nul 2>&1
start "" pythonw -m simplemonitor
