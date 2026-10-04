import QtQuick
import QtQuick.Controls

// Bar widget. Click summons the panel via the shell IPC target.
Item {
    id: root
    implicitWidth: label.implicitWidth + 16
    implicitHeight: 28
    property string pluginId: "example.status-panel"

    Accessible.role: Accessible.Button
    Accessible.name: "Status"
    objectName: "status-bar"

    Text {
        id: label
        anchors.centerIn: parent
        text: "Status"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.PluginHost.summon(root.pluginId)
    }
}
