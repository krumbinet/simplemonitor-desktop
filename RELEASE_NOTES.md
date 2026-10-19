**Simple Monitor for Windows** – the popular Plasma desktop widget "Simple System Monitor" as a standalone program.

### Install
1. Download `SimpleMonitor-…-windows-x64.zip` below and unzip it, e.g. to `C:\Users\<you>\SimpleMonitor`.
2. Start `SimpleMonitor.exe`. Windows SmartScreen may warn about an unknown publisher (the program is not code-signed): *More info* → *Run anyway*.
3. Right click on the widget for the menu (settings, lock position, start with Windows, …).

### CPU temperatures
Windows does not provide CPU temperatures to normal programs. Keep
[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) (start as administrator)
or [Core Temp](https://www.alcpu.com/CoreTemp/) running – Simple Monitor picks up their sensors automatically.
NVIDIA GPU temperatures work without them.

See [CHANGELOG.md](CHANGELOG.md) for details. Feedback and bug reports: [Issues](https://github.com/krumbinet/simplemonitor-desktop/issues).
