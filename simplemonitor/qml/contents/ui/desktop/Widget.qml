/*
 * SPDX-FileCopyrightText: 2013-2016 Dhaby Xiloj, Konstantin Shtepa
 * SPDX-FileCopyrightText: 2026 krumbinet and Simple Monitor contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

// The desktop window: frameless, transparent, below (or above) other windows.
// Left drag moves it (unless locked), right click opens the menu,
// double click opens the settings.

import QtQuick
import QtQuick.Window

import ".."

Window {
    id: win

    title: "Simple Monitor"
    visible: true
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
           | (cfg.stayOnTop ? Qt.WindowStaysOnTopHint : Qt.WindowStaysOnBottomHint)

    readonly property real zoom: Math.max(0.3, Math.min(4, Number(cfg.zoom) || 1))

    width: Math.max(40, Math.ceil(view.implicitWidth * zoom))
    height: Math.max(40, Math.ceil(view.implicitHeight * zoom))

    function placeInitially() {
        var sx = Screen.virtualX, sy = Screen.virtualY
        if (cfg.posX < 0 || cfg.posY < 0) {
            x = sx + Screen.desktopAvailableWidth - width - 40
            y = sy + 40
        } else {
            x = cfg.posX
            y = cfg.posY
        }
    }
    Component.onCompleted: placeInitially()

    // Development aid: screenshot of the widget (used by tools/screenshot.py).
    function grabTo(path) {
        contentItem.grabToImage(function(r) { r.saveToFile(path) })
    }

    // Remember the position (Config saves debounced).
    onXChanged: if (visible) cfg.posX = x
    onYChanged: if (visible) cfg.posY = y

    MouseArea {
        id: mouse
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        cursorShape: !cfg.locked && containsMouse ? Qt.SizeAllCursor : Qt.ArrowCursor
        onPressed: (ev) => {
            if (ev.button === Qt.RightButton)
                app.showContextMenu()
            else if (!cfg.locked)
                win.startSystemMove()
        }
        onDoubleClicked: (ev) => { if (ev.button === Qt.LeftButton) app.openSettings() }
    }

    Item {
        width: view.implicitWidth
        height: view.implicitHeight
        scale: win.zoom
        transformOrigin: Item.TopLeft

        DesktopView {
            id: view
            anchors.fill: parent
            logoEditMode: app.logoEditMode
        }

        // Frame shown while the widget can be moved, so it is easy to grab
        // even with a transparent background.
        Rectangle {
            anchors.fill: parent
            visible: !cfg.locked && mouse.containsMouse
            color: "#22ffffff"
            border.color: "#88ffffff"
            border.width: 1
            radius: view.radius
        }
    }
}
