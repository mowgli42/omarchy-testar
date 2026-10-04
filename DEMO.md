# Demo

Fixture app, no Hyprland:

```bash
python3 sim/explore.py
```

Plugin UI (example status panel):

```bash
python3 sim/plugin_ui.py
```

Expect `sim/out/plugin-sequence.jsonl` with summon, Refresh, Close, and `sim/out/plugin-walk.html`.

On a real Omarchy session the same plugin is `omarchy plugin add` of this repo, then `omarchy-shell summon example.status-panel`. That path is tagged `@future`.
