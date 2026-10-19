# Change Log
The format is based on [Keep a Changelog](http://keepachangelog.com/).

## [0.1.0] - 2026-10-18
First version.

### Added
- Standalone desktop program (Qt 6 / PySide6) with the skins of the Plasma 6 widget
  plasma-simplemonitor6 0.7.1 (Default, Column, Minimalistic).
- Windows: OS name/build from the registry, CPU temperatures from LibreHardwareMonitor /
  OpenHardwareMonitor (WMI), autostart via the registry, own neutral logo.
- Linux: os-release, hwmon temperatures (psutil), XDG autostart, distribution logo from the icon theme.
- NVIDIA GPU temperatures via NVML on both systems.
- Frameless transparent window: drag to move, lock position, always on top or below,
  size (zoom), black / transparent / translucent background.
- Right-click and tray menu, settings window with live preview, own logo image.
- Translations shared with the Plasma widget; German complete.
- Windows build with PyInstaller and GitHub Actions.
