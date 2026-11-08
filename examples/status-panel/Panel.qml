import QtQuick
import QtQuick.Controls

// Panel entry point. Host (Widget.qml / shell.summon) calls open() / close().
Item {
    id: panel
    visible: false
    width: column.implicitWidth + 24
    height: column.implicitHeight + 24
    property string status: "Ready"

    function open(payloadJson) { visible = true }
    function close() { visible = false }

    Accessible.role: Accessible.Pane
    Accessible.name: "Status panel"
    objectName: "status-panel"

    Rectangle {
        anchors.fill: parent
        color: "#1a1b1e"
        border.color: "#3b4252"
        radius: 6
    }

    Column {
        id: column
        anchors.centerIn: parent
        spacing: 8
        Text {
            objectName: "status-text"
            Accessible.role: Accessible.StaticText
            Accessible.name: panel.status
            color: "#eceff4"
            text: panel.status
        }
        Button {
            objectName: "refresh"
            text: "Refresh"
            Accessible.name: "Refresh"
            onClicked: panel.status = "Checked"
        }
        Button {
            objectName: "close"
            text: "Close"
            Accessible.name: "Close"
            onClicked: panel.close()
        }
    }
}
