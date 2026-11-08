import QtQuick
import QtQuick.Controls

// Bar widget with Omarchy summon contract: open / close / opened.
// Panel.qml is loaded here so shell.summon("example.status-panel") works.
Item {
    id: root
    implicitWidth: button.implicitWidth + 16
    implicitHeight: 28
    property string pluginId: "example.status-panel"
    property var bar
    property var settings: ({})

    Accessible.role: Accessible.Button
    Accessible.name: "Status"
    objectName: "status-bar"
    Accessible.onPressAction: root.toggle()

    readonly property bool opened: panelLoader.item ? panelLoader.item.visible === true : false

    function open() {
        if (panelLoader.item)
            panelLoader.item.open("{}")
    }

    function close() {
        if (panelLoader.item)
            panelLoader.item.close()
    }

    function toggle() {
        if (root.opened)
            root.close()
        else
            root.open()
    }

    Text {
        id: button
        anchors.centerIn: parent
        text: "Status"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.toggle()
    }

    Loader {
        id: panelLoader
        active: true
        source: Qt.resolvedUrl("Panel.qml")
        // Keep the panel in the a11y tree when open; hide when closed.
        visible: item ? item.visible : false
        onLoaded: {
            // Anchor near the bar pill so nested seat screenshots catch it.
            item.x = 8
            item.y = root.height + 8
        }
    }
}
