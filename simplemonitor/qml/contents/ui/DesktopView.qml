/*
 * SPDX-FileCopyrightText: 2013-2016 Dhaby Xiloj, Konstantin Shtepa
 * SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

// Desktop counterpart of MonitorView.qml of the Plasma widget: reads the
// configuration (context property "cfg") and loads the selected skin.
// Sensor values come from the Python object "sysData" (context property).

import QtQuick

import "../code/code.js" as Code

Rectangle {
    id: monitorView

    property bool logoEditMode: false

    implicitWidth: loader.item ? loader.item.implicitWidth : 0
    implicitHeight: loader.item ? loader.item.implicitHeight : 0

    // 0 = black, 1 = transparent, 2 = translucent
    color: confEngine.bgColor === 0 ? "black" : confEngine.bgColor === 2 ? "#a6000000" : "transparent"
    radius: confEngine.bgColor === 2 ? 8 : 0

    QtObject {
        id: confEngine

        readonly property int skin:              Code.num(cfg.skin, 0)
        readonly property int bgColor:           Code.num(cfg.bgColor, 2)
        readonly property int logo:              Code.num(cfg.logo, 0)
        readonly property real logoScale:        Code.num(cfg.logoScale, 1.0)
        readonly property bool showGpuTemp:      !!cfg.showGpuTemp
        readonly property bool showSwap:         !!cfg.showSwap
        readonly property bool showUptime:       !!cfg.showUptime
        readonly property int tempUnit:          Code.num(cfg.tempUnit, 0)
        // Without per-core sensors (e.g. many AMD CPUs) show the average instead.
        readonly property int cpuTempMode: {
            var m = Code.num(cfg.cpuTempMode, 0)
            return (m === 0 && sysData.coreTempCount === 0) ? 1 : m
        }
        readonly property int cpuHighTemp:       Code.num(cfg.cpuHighTemp, 70)
        readonly property int cpuCritTemp:       Code.num(cfg.cpuCritTemp, 85)
        readonly property bool coloredCpuLoad:   !!cfg.coloredCpuLoad
        readonly property bool flatCpuLoad:      !!cfg.flatCpuLoad
        readonly property int indicatorHeight:   Code.num(cfg.indicatorHeight, 10)
        readonly property real updateInterval:   Math.max(0.1, Code.num(cfg.updateInterval, 1.0))

        readonly property bool logoEditMode:     monitorView.logoEditMode

        readonly property int direction: Qt.application.layoutDirection

        function setLogoScale(value) {
            if (cfg.logoScale !== value)
                cfg.logoScale = value
        }
    }

    Loader {
        id: loader
        anchors.fill: parent
        source: {
            switch (confEngine.skin) {
            case 1:  return "skins/ColumnSkin.qml"
            case 2:  return "skins/MinimalisticSkin.qml"
            default: return "skins/DefaultSkin.qml"
            }
        }
    }
}
