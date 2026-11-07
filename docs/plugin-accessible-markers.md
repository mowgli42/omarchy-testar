# Accessible markers for Omarchy plugins

Reference for plugin authors who want **omarchy-testar** to explore their UI without a hand-written click script.

TESTAR-style discovery does **not** parse your QML as a script. At runtime it reads the accessibility tree (AT-SPI). Offline / CI scrape (`sim/snarksentinel_click.py --scrape`, `sim/plugin_ui.py`) looks for the same markers in QML so the fixture inventory matches what a live seat will see.

If a control has no `Accessible.name` (and no scrapeable `Button.text`), the explorer will not click it.

## Minimum contract

On every control that should be actionable (or asserted), set all three:

| Property | Purpose |
|----------|---------|
| `objectName` | Stable machine id for replay and debugging (kebab-case, unique within the panel when practical) |
| `Accessible.role` | AT-SPI / WAI-ARIA role (`Accessible.Button`, `Accessible.Pane`, `Accessible.StaticText`, …) |
| `Accessible.name` | Human-visible label the explorer uses as the action name |

Shared role vocabulary (see [standards.md](standards.md)): `button`, `text`, `dialog`, `menu item`, `link`.

## Patterns

### Bar widget (summon)

The bar hit-target is often a bare `Item` + `MouseArea`, not a `Button`. Mark the root as a button:

```qml
Item {
    id: root
    objectName: "myplugin-bar"
    Accessible.role: Accessible.Button
    Accessible.name: "MyPlugin"

    MouseArea {
        anchors.fill: parent
        onClicked: root.toggle()  // or PluginHost.summon(...)
    }
}
```

Reference: `examples/status-panel/Widget.qml`, SnarkSentinel `omarchy-plugin/BarWidget.qml`.

### Panel root

```qml
Item {
    id: panel
    objectName: "myplugin-panel"
    Accessible.role: Accessible.Pane
    Accessible.name: "MyPlugin panel"

    function open(payloadJson) { visible = true }
    function close() { visible = false }
}
```

### Static button

Prefer `Accessible.name` equal to the visible label (same string users see):

```qml
Button {
    objectName: "refresh"
    text: "Refresh"
    Accessible.role: Accessible.Button
    Accessible.name: "Refresh"
    onClicked: panel.refresh()
}
```

### Dynamic / Repeater button

Bind `Accessible.name` to the same expression that drives the label. Declare `required property` before you reference `modelData`:

```qml
delegate: Button {
    required property var modelData
    objectName: "row-action"
    Accessible.role: Accessible.Button
    Accessible.name: modelData.label
    text: modelData.label
    onClicked: root.run(modelData.id)
}
```

Ternary labels (both arms must be discoverable offline if you scrape QML):

```qml
Button {
    objectName: "bwrap-net"
    text: modelData.network ? "Set net off" : "Set net on"
    Accessible.role: Accessible.Button
    Accessible.name: text
    onClicked: root.setNetwork(modelData.name, !modelData.network)
}
```

### Icon-only button

When `text` is empty, put the accessible name on the tooltip / label string — never leave `Accessible.name` empty:

```qml
Button {
    objectName: "fix-prompt"
    Accessible.role: Accessible.Button
    Accessible.name: "Fix prompt"
    iconText: "…"
    tooltipText: "Fix prompt"
    onClicked: root.openFix()
}
```

### Status / readout text (optional)

Useful when an oracle asserts panel copy after a click:

```qml
Text {
    objectName: "status-text"
    Accessible.role: Accessible.StaticText
    Accessible.name: panel.status
    text: panel.status
}
```

## Naming rules

1. **`Accessible.name` is the explorer key.** Click-all coverage is by name. Duplicate names across tabs collapse to one click unless you disambiguate (e.g. `"Scan"` tab vs keep dialog primary as `"Run scan"`).
2. **`objectName` is for humans and replay.** Use kebab-case: `refresh-list`, `scan-close`, `accept-these-results`.
3. **Do not invent a second label.** If the button says `"Refresh list"`, the accessible name is `"Refresh list"`, not `"refresh"` or `"btn1"`.
4. **Destructive actions** still get markers. Policy (blocklist / confirm) is the explorer’s job, not a reason to hide a11y.

## What omarchy-testar reads

| Path | Source | Uses |
|------|--------|------|
| Live seat (Future / nested) | AT-SPI via `sim/atspi.py --live` | `Accessible.role` + `Accessible.name` |
| Offline scrape | QML text | `Accessible.name`, else `Button { text: "…" }` / ternary arms |
| Example walk | `examples/status-panel` | Both markers required in `sim/plugin_ui.py` |
| SnarkSentinel fixture | `sim/fixtures/snarksentinel/app.json` | Names must match panel markers |

## Verify before you ship

From this repo (or with a sibling checkout):

```bash
# List scrapeable button labels from your plugin directory
python3 sim/snarksentinel_click.py --scrape /path/to/your-plugin

# Example plugin contract (Accessible.name + objectName required)
python3 sim/plugin_ui.py

# Role map smoke (fixture AT-SPI tree)
python3 sim/atspi.py
```

Checklist:

- [ ] Bar root has `Accessible.role: Accessible.Button` and a product `Accessible.name`
- [ ] Panel root has `Accessible.role: Accessible.Pane` and `objectName`
- [ ] Every clickable `Button` / button-like `MouseArea` has non-empty `Accessible.name`
- [ ] Icon-only controls use label/tooltip as `Accessible.name`
- [ ] Repeater delegates bind `Accessible.name` to the visible label
- [ ] `--scrape` lists every control you expect click-all to hit
- [ ] Destructive controls are marked, not omitted

## Copy-paste skeleton

```qml
import QtQuick
import QtQuick.Controls

Item {
    id: root
    objectName: "example-bar"
    Accessible.role: Accessible.Button
    Accessible.name: "Example"

    // ... bar chrome ...

    Loader {
        active: panelOpen
        source: "Panel.qml"
    }
}
```

```qml
import QtQuick
import QtQuick.Controls

Item {
    id: panel
    objectName: "example-panel"
    Accessible.role: Accessible.Pane
    Accessible.name: "Example panel"

    function open(payloadJson) { visible = true }
    function close() { visible = false }

    Button {
        objectName: "refresh"
        text: "Refresh"
        Accessible.role: Accessible.Button
        Accessible.name: "Refresh"
        onClicked: { /* ... */ }
    }
    Button {
        objectName: "close"
        text: "Close"
        Accessible.role: Accessible.Button
        Accessible.name: "Close"
        onClicked: panel.close()
    }
}
```

## References in-tree

| Example | Path |
|---------|------|
| Minimal bar + panel | `examples/status-panel/` |
| Production-sized panel | SnarkSentinel `omarchy-plugin/BarWidget.qml`, `Panel.qml` |
| Nested seat (do not ydotool the host) | [nested-seat.md](nested-seat.md) |
| Report / role vocabulary | [standards.md](standards.md) |
