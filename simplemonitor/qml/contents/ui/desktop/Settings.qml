/*
 * SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

// Settings window. Changes apply immediately (live preview) and are saved
// automatically by the Python side.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

import "../../code/code.js" as Code

ApplicationWindow {
    id: settings

    title: i18n("Simple Monitor – Settings")
    width: 560
    height: 720
    minimumWidth: 460
    minimumHeight: 400
    visible: true

    // Development aid: screenshot (tools/screenshot.py).
    function grabTo(path) {
        scroll.grabToImage(function(r) { r.saveToFile(path) })
    }

    readonly property var previews: ["defaultSkin-preview.png", "columnSkin-preview.png", "minimalisticSkin-preview.png"]

    component Row2: RowLayout {
        property alias label: lbl.text
        spacing: 12
        Layout.fillWidth: true
        Label {
            id: lbl
            Layout.preferredWidth: 190
            horizontalAlignment: Text.AlignRight
            wrapMode: Text.WordWrap
        }
    }

    component Hint: Label {
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
        Layout.leftMargin: 202
        font.pointSize: Math.max(7, Qt.application.font.pointSize - 1)
        opacity: 0.75
    }

    footer: DialogButtonBox {
        Button {
            text: i18n("Close")
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        onAccepted: settings.close()
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        contentWidth: availableWidth
        background: Rectangle { color: settings.palette.window }

        ColumnLayout {
            width: scroll.availableWidth
            spacing: 14

            Item { height: 4 }

            // ---- Appearance --------------------------------------------------
            GroupBox {
                title: i18n("Appearance")
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Row2 {
                        label: i18n("Skin:")
                        ComboBox {
                            id: skinBox
                            model: [i18n("Default"), i18n("Column"), i18n("Minimalistic")]
                            currentIndex: cfg.skin
                            onActivated: (i) => cfg.skin = i
                            Layout.fillWidth: true
                        }
                    }
                    Image {
                        Layout.leftMargin: 202
                        Layout.maximumHeight: 220
                        Layout.preferredHeight: 220
                        Layout.preferredWidth: 220
                        fillMode: Image.PreserveAspectFit
                        horizontalAlignment: Image.AlignLeft
                        source: "../../images/" + settings.previews[Math.max(0, Math.min(2, skinBox.currentIndex))]
                    }

                    Row2 {
                        label: i18n("Background color:")
                        ComboBox {
                            model: [i18n("Black"), i18n("Transparent"), i18n("Translucent")]
                            currentIndex: cfg.bgColor
                            onActivated: (i) => cfg.bgColor = i
                            Layout.fillWidth: true
                        }
                    }

                    Row2 {
                        label: i18n("Size:")
                        Slider {
                            id: zoomSlider
                            from: 0.5; to: 2.5; stepSize: 0.05
                            value: cfg.zoom
                            onMoved: cfg.zoom = Math.round(value * 100) / 100
                            Layout.fillWidth: true
                        }
                        Label { text: Math.round(zoomSlider.value * 100) + " %" ; Layout.preferredWidth: 48 }
                    }

                    Row2 {
                        label: i18n("Logo:")
                        ComboBox {
                            id: logoBox
                            model: [i18n("Automatic"), i18n("Tux"), i18n("Slackware"), i18n("Ubuntu"), i18n("Kubuntu"),
                                    i18n("OpenSUSE"), i18n("Manjaro"), i18n("Arch"), i18n("Fedora"), i18n("Debian")]
                            currentIndex: cfg.logo
                            onActivated: (i) => cfg.logo = i
                            Layout.fillWidth: true
                        }
                    }
                    Row2 {
                        label: i18n("Own logo image:")
                        TextField {
                            readOnly: true
                            text: cfg.logoPath
                            placeholderText: i18n("none")
                            Layout.fillWidth: true
                        }
                        Button {
                            text: i18n("Choose…")
                            onClicked: logoDialog.open()
                        }
                        Button {
                            text: i18n("Remove")
                            enabled: cfg.logoPath !== ""
                            onClicked: cfg.logoPath = ""
                        }
                    }
                    Hint {
                        text: i18n("An own image (PNG, SVG, JPG) is shown when the logo is set to \"Automatic\". The logo size can be changed from the right-click menu.")
                    }
                }
            }

            // ---- Show ----------------------------------------------------------
            GroupBox {
                title: i18n("Show:")
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12

                ColumnLayout {
                    anchors.fill: parent
                    CheckBox { text: i18n("GPU Temperature"); checked: cfg.showGpuTemp; onToggled: cfg.showGpuTemp = checked }
                    CheckBox { text: i18n("Swap"); checked: cfg.showSwap; onToggled: cfg.showSwap = checked }
                    CheckBox { text: i18n("Uptime"); checked: cfg.showUptime; onToggled: cfg.showUptime = checked }
                }
            }

            // ---- Temperatures ----------------------------------------------------
            GroupBox {
                title: i18n("Temperature settings:")
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Row2 {
                        label: i18n("Temperature units:")
                        ComboBox {
                            model: [i18n("Celsius °C"), i18n("Fahrenheit °F")]
                            currentIndex: cfg.tempUnit
                            onActivated: (i) => cfg.tempUnit = i
                            Layout.fillWidth: true
                        }
                    }
                    Row2 {
                        label: i18n("CPU temperature:")
                        ComboBox {
                            model: [i18n("Every core"), i18n("Average only"), i18n("Maximum only")]
                            currentIndex: cfg.cpuTempMode
                            onActivated: (i) => cfg.cpuTempMode = i
                            Layout.fillWidth: true
                        }
                    }
                    Row2 {
                        label: i18n("CPU High Temperature:")
                        SpinBox {
                            from: 20; to: 150
                            value: cfg.cpuHighTemp
                            onValueModified: cfg.cpuHighTemp = value
                            textFromValue: (v) => v + " °C"
                            valueFromText: (t) => parseInt(t)
                        }
                    }
                    Row2 {
                        label: i18n("CPU Critical Temperature:")
                        SpinBox {
                            from: 20; to: 150
                            value: cfg.cpuCritTemp
                            onValueModified: cfg.cpuCritTemp = value
                            textFromValue: (v) => v + " °C"
                            valueFromText: (t) => parseInt(t)
                        }
                    }
                    Row2 {
                        label: i18n("Temperature source:")
                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: sysData.tempSource !== "" ? sysData.tempSource : i18n("none found")
                            font.bold: true
                        }
                    }
                    Hint {
                        visible: app.isWindows
                        text: i18n("Windows does not offer CPU temperatures by itself. Start LibreHardwareMonitor (free, open source) as administrator and keep it running in the background – Simple Monitor then shows its temperatures automatically. NVIDIA graphics cards work without it.")
                    }
                    Button {
                        visible: app.isWindows
                        Layout.leftMargin: 202
                        text: i18n("Get LibreHardwareMonitor")
                        onClicked: Qt.openUrlExternally("https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases")
                    }
                }
            }

            // ---- Style and behaviour -----------------------------------------------
            GroupBox {
                title: i18n("Miscellaneous")
                Layout.fillWidth: true
                Layout.leftMargin: 12
                Layout.rightMargin: 12

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Row2 {
                        label: i18n("CPU load indicator style:")
                        CheckBox { text: i18n("Colored"); checked: cfg.coloredCpuLoad; onToggled: cfg.coloredCpuLoad = checked }
                        CheckBox { text: i18n("Flat"); checked: cfg.flatCpuLoad; onToggled: cfg.flatCpuLoad = checked }
                    }
                    Row2 {
                        label: i18n("CPU load indicator height:")
                        SpinBox {
                            from: 1; to: 99
                            value: cfg.indicatorHeight
                            onValueModified: cfg.indicatorHeight = value
                        }
                    }
                    Row2 {
                        label: i18n("Update interval:")
                        SpinBox {
                            from: 1; to: 100
                            value: Math.round(cfg.updateInterval * 10)
                            onValueModified: cfg.updateInterval = value / 10
                            textFromValue: (v, locale) => Number(v / 10).toLocaleString(locale, "f", 1) + " " + i18nc("Abbreviation for seconds", "s")
                            valueFromText: (t, locale) => Math.round(Number.fromLocaleString(locale, t.replace(/[^0-9.,]/g, "")) * 10)
                        }
                    }
                    Row2 {
                        label: i18n("Window:")
                        ColumnLayout {
                            CheckBox { text: i18n("Lock position"); checked: cfg.locked; onToggled: cfg.locked = checked }
                            CheckBox { text: i18n("Always on top"); checked: cfg.stayOnTop; onToggled: cfg.stayOnTop = checked }
                            CheckBox { text: i18n("Start with the system"); checked: app.autostart; onToggled: app.autostart = checked }
                        }
                    }
                    Row2 {
                        label: ""
                        Button {
                            text: i18n("Reset position")
                            onClicked: app.resetPosition()
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                Layout.margins: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                opacity: 0.7
                textFormat: Text.StyledText
                linkColor: palette.link
                text: "Simple Monitor " + app.version + " · GPL-3.0-or-later · "
                      + "<a href=\"" + app.homepage + "\">" + app.homepage.replace("https://", "") + "</a>"
                onLinkActivated: (link) => Qt.openUrlExternally(link)
            }
        }
    }

    FileDialog {
        id: logoDialog
        title: i18n("Choose a logo image")
        nameFilters: [i18n("Images") + " (*.png *.svg *.jpg *.jpeg *.webp *.bmp)"]
        onAccepted: cfg.logoPath = app.localPath(selectedFile)
    }
}
