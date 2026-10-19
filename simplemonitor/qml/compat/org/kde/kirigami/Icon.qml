// SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Minimal stand-in for Kirigami.Icon, so the skins shared with the Plasma
// widget run without KDE Frameworks. Accepts a file path/URL or a theme icon
// name (resolved by the "theme" image provider of the app).

import QtQuick

Item {
    id: icon

    property var source
    property var fallback

    readonly property string src: String(source || "")
    readonly property bool isFile: /^(file:|qrc:|\/|[A-Za-z]:[\\\/])/.test(src)
    readonly property string resolved: {
        if (src === "")
            return ""
        if (/^[A-Za-z]:[\\\/]/.test(src))
            return "file:///" + src.replace(/\\/g, "/")
        if (isFile)
            return src
        return "image://theme/" + src
    }

    Image {
        id: img
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        sourceSize: Qt.size(Math.max(64, parent.width), Math.max(64, parent.height))
        source: icon.visible ? icon.resolved : ""
        visible: status === Image.Ready
    }
    Image {
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        visible: img.status !== Image.Ready
        source: img.status !== Image.Ready ? String(icon.fallback || "") : ""
    }
}
