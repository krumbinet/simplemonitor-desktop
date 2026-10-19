**Simple Monitor for Windows** – the popular Plasma desktop widget "Simple System Monitor" as a standalone program.

### Install
1. Download `SimpleMonitor-…-windows-x64.zip` below and unzip it, e.g. to `C:\Users\<you>\SimpleMonitor`.
2. Start `SimpleMonitor.exe`. Windows SmartScreen may warn about an unknown publisher (the program is not code-signed): *More info* → *Run anyway*.
3. Right click on the widget for the menu (settings, lock position, start with Windows, …).

### CPU temperatures
Windows does not provide CPU temperatures to normal programs. Install and start
[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) as administrator
and keep it running – Simple Monitor picks up its sensors automatically. NVIDIA GPU temperatures work without it.

See [CHANGELOG.md](CHANGELOG.md) for details. Feedback and bug reports: [Issues](https://github.com/krumbinet/simplemonitor-desktop/issues).
